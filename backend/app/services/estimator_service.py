import openai
from typing import List, Dict, Any, Tuple
import json
import re
from app.core.config import settings
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import traceback
import time
from app.prompts.estimate_prompts import get_estimate_prompt, get_system_prompt

class EstimatorService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
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
            # リトライ付きで堅牢化
            backoffs = [0, 1.0, 2.0]
            last = None
            for wait in backoffs:
                if wait:
                    print(f"[EST] retry in {wait:.1f}s deliverable[{idx}] tid={tid}: {name}")
                    time.sleep(wait)
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
                    last = e
                    continue
            # 最終フォールバック
            print(f"[EST] fallback deliverable[{idx}] tid={tid}: {name} use default estimate (error: {last})")
            est = {
                'name': d.get('name'),
                'description': d.get('description'),
                'person_days': 5.0,
                'amount': 5.0 * self.daily_unit_cost,
                'reasoning': f'デフォルト見積り（リトライ失敗: {last}）',
                'reasoning_breakdown': 'デフォルト見積り: 5.0人日',
                'reasoning_notes': f'エラーが発生したため、デフォルト値を使用しました。\nエラー: {last}'
            }
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
        """単一成果物の見積りを生成する"""

        # 質問と回答を整理
        qa_text = "\n".join([
            f"質問: {qa['question']}\n回答: {qa['answer']}"
            for qa in qa_pairs
        ])

        prompt = get_estimate_prompt(deliverable, system_requirements, qa_text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSONレスポンスの解析
            try:
                # JSON部分を抽出
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)

                    person_days = float(result.get('person_days', 5.0))
                    reasoning_breakdown = result.get('reasoning_breakdown', '')
                    reasoning_notes = result.get('reasoning_notes', '')
                    # 後方互換性: reasoning フィールドも保持
                    reasoning = result.get('reasoning', f"{reasoning_breakdown}\n\n{reasoning_notes}")
                else:
                    # JSONが見つからない場合のフォールバック
                    person_days = 5.0
                    reasoning_breakdown = content
                    reasoning_notes = ''
                    reasoning = content

            except (json.JSONDecodeError, ValueError):
                person_days = 5.0
                reasoning_breakdown = content
                reasoning_notes = ''
                reasoning = content

        except Exception as e:
            print(f"AI見積りでエラーが発生しました: {e}")
            person_days = 5.0
            reasoning_breakdown = "デフォルト見積り（AIエラーのため）"
            reasoning_notes = ""
            reasoning = "デフォルト見積り（AIエラーのため）"

        # 金額計算
        amount = person_days * self.daily_unit_cost

        return {
            'name': deliverable['name'],
            'description': deliverable['description'],
            'person_days': person_days,
            'amount': amount,
            'reasoning': reasoning,  # 後方互換性のため保持
            'reasoning_breakdown': reasoning_breakdown,
            'reasoning_notes': reasoning_notes
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
