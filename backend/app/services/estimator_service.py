import openai
from typing import List, Dict, Any, Tuple
import json
import re
import logging
from app.core.config import settings
from app.core.i18n import t
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import traceback
import time
from app.prompts.estimate_prompts import get_estimate_prompt, get_system_prompt
from app.services.retry_service import retry_with_exponential_backoff
from app.services.circuit_breaker import openai_circuit_breaker

logger = logging.getLogger(__name__)


class EstimatorService:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT  # Add timeout setting
        )
        self.model = settings.OPENAI_MODEL
        self.daily_unit_cost = settings.get_daily_unit_cost()
        
    def generate_estimates(self, deliverables: List[Dict[str, str]], 
                          system_requirements: str,
                          qa_pairs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """成果物ごとの見積りを生成する（並列実行で高速化）"""
        max_workers =  int(getattr(settings, 'MAX_PARALLEL_ESTIMATES', 5)) if hasattr(settings, 'MAX_PARALLEL_ESTIMATES') else 5
        results: List[Tuple[int, Dict[str, Any]]] = []

        total_start = time.perf_counter()
        print(f"[EST] batch start: n={len(deliverables)} max_workers={max_workers} model={self.model} unit_cost={self.daily_unit_cost}")

        def worker(idx: int, d: Dict[str, str]) -> Tuple[int, Dict[str, Any]]:
            name = d.get('name')
            tid = threading.get_ident()
            start = time.perf_counter()

            try:
                print(f"[EST] start deliverable[{idx}] tid={tid}: {name}")
                est = self._estimate_single_deliverable(d, system_requirements, qa_pairs)
                dur = time.perf_counter() - start
                print(f"[EST] done  deliverable[{idx}] tid={tid}: {name} in {dur:.2f}s -> {est.get('person_days')}人日 {int(est.get('amount',0))}円")
                return (idx, est)
            except Exception as e:
                dur = time.perf_counter() - start
                print(f"[EST] error deliverable[{idx}] tid={tid}: {name} after {dur:.2f}s: {e}")
                traceback.print_exc()
                # Use fallback estimation
                print(f"[EST] fallback deliverable[{idx}] tid={tid}: {name} use fallback estimation")
                est = self._fallback_estimation(d, e)
                return (idx, est)

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(worker, i, d) for i, d in enumerate(deliverables)]
            for fut in as_completed(futures):
                results.append(fut.result())

        # 元の順序に並べ替え
        results.sort(key=lambda x: x[0])
        total_dur = time.perf_counter() - total_start
        print(f"[EST] batch complete in {total_dur:.2f}s")
        return [e for _, e in results]
    
    def _estimate_single_deliverable(self, deliverable: Dict[str, str],
                                   system_requirements: str,
                                   qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate estimate for single deliverable with circuit breaker protection"""
        try:
            # Call through circuit breaker
            return openai_circuit_breaker.call(
                self._call_llm_with_retry,
                deliverable,
                system_requirements,
                qa_pairs
            )
        except Exception as e:
            logger.error(f"Estimation failed for {deliverable.get('name')}: {e}")
            # Use fallback estimation
            return self._fallback_estimation(deliverable, e)

    @retry_with_exponential_backoff()
    def _call_llm_with_retry(self, deliverable: Dict[str, str],
                            system_requirements: str,
                            qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call LLM with retry logic (exponential backoff)"""
        # Format Q&A pairs
        qa_text = "\n".join([
            f"質問: {qa['question']}\n回答: {qa['answer']}"
            for qa in qa_pairs
        ])

        prompt = get_estimate_prompt(deliverable, system_requirements, qa_text)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3,
            timeout=settings.OPENAI_TIMEOUT
        )

        return self._parse_llm_response(response, deliverable)

    def _parse_llm_response(self, response, deliverable: Dict[str, str]) -> Dict[str, Any]:
        """Parse LLM response and extract estimate data"""
        content = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            # Extract JSON part
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)

                person_days = float(result.get('person_days', 5.0))
                reasoning_breakdown = result.get('reasoning_breakdown', '')
                reasoning_notes = result.get('reasoning_notes', '')
                # Backward compatibility: keep reasoning field
                reasoning = result.get('reasoning', f"{reasoning_breakdown}\n\n{reasoning_notes}")
            else:
                # Fallback if JSON not found
                person_days = 5.0
                reasoning_breakdown = content
                reasoning_notes = ''
                reasoning = content

        except (json.JSONDecodeError, ValueError):
            person_days = 5.0
            reasoning_breakdown = content
            reasoning_notes = ''
            reasoning = content

        # Calculate amount
        amount = person_days * self.daily_unit_cost

        return {
            'name': deliverable['name'],
            'description': deliverable['description'],
            'person_days': person_days,
            'amount': amount,
            'reasoning': reasoning,  # Backward compatibility
            'reasoning_breakdown': reasoning_breakdown,
            'reasoning_notes': reasoning_notes
        }

    def _fallback_estimation(self, deliverable: Dict[str, str], error: Exception = None) -> Dict[str, Any]:
        """Fallback estimation using keyword-based heuristics"""
        name = deliverable.get('name', '').lower()
        description = deliverable.get('description', '').lower()

        # Keyword-based effort estimation
        base_days = 5.0  # Default

        # Japanese keywords
        if any(kw in name or kw in description for kw in ['要件定義', 'requirements']):
            base_days = 10.0
        elif any(kw in name or kw in description for kw in ['基本設計', '詳細設計', 'design']):
            base_days = 15.0
        elif any(kw in name or kw in description for kw in ['実装', 'implementation', '開発', 'development', 'programming']):
            base_days = 30.0
        elif any(kw in name or kw in description for kw in ['テスト', 'test', 'testing']):
            base_days = 10.0
        elif any(kw in name or kw in description for kw in ['データベース', 'database', 'db']):
            base_days = 12.0
        elif any(kw in name or kw in description for kw in ['api', 'バックエンド', 'backend']):
            base_days = 20.0
        elif any(kw in name or kw in description for kw in ['フロント', 'frontend', 'ui', 'ux']):
            base_days = 18.0
        elif any(kw in name or kw in description for kw in ['認証', 'auth', 'authentication']):
            base_days = 8.0
        elif any(kw in name or kw in description for kw in ['マニュアル', 'manual', 'ドキュメント', 'document']):
            base_days = 5.0

        error_note = f"\nエラー: {error}" if error else ""

        return {
            'name': deliverable['name'],
            'description': deliverable.get('description', ''),
            'person_days': base_days,
            'amount': base_days * self.daily_unit_cost,
            'reasoning': t('messages.fallback_estimation_note'),
            'reasoning_breakdown': f'{base_days}人日（{t("messages.fallback_estimation_note")}）',
            'reasoning_notes': t('messages.fallback_estimation_reason') + error_note
        }
    
    def calculate_totals(self, estimates: List[Dict[str, Any]]) -> Dict[str, float]:
        """合計金額、税額、総額を計算する"""
        subtotal = sum(estimate['amount'] for estimate in estimates)
        tax = subtotal * settings.get_tax_rate()
        total = subtotal + tax
        
        return {
            'subtotal': subtotal,
            'tax': tax,
            'total': total
        }
