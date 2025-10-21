"""Estimate adjustment chat service

- Quick actions: Immediate calculation with local logic
- AI estimate adjustment: Generate proposals with OpenAI for free input (message) (synchronous)
"""
from typing import List, Dict, Any, Tuple
import uuid
import logging
from app.models import Estimate, Task, Message
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.i18n import t
from app.services.retry_service import retry_with_exponential_backoff
from app.services.circuit_breaker import openai_circuit_breaker
import json
import re

logger = logging.getLogger(__name__)

try:
    import openai
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False


class ChatService:
    # 提案キャッシュ（クラス変数として全インスタンス共有）
    _proposals_cache: Dict[str, List[Dict[str, Any]]] = {}

    def __init__(self, db: Session):
        self.db = db

    def _load_estimates(self, task_id: str) -> List[Estimate]:
        return self.db.query(Estimate).filter(Estimate.task_id == task_id).all()

    def _calc_totals(self, estimates: List[Dict[str, Any]]) -> Dict[str, float]:
        subtotal = float(sum(e.get("amount", 0.0) for e in estimates))
        tax = round(subtotal * settings.get_tax_rate(), 2)
        total = round(subtotal + tax, 2)
        return {"subtotal": subtotal, "tax": tax, "total": total}

    def _as_dicts(self, rows: List[Estimate]) -> List[Dict[str, Any]]:
        return [
            {
                "deliverable_name": r.deliverable_name,
                "deliverable_description": r.deliverable_description,
                "person_days": float(r.person_days),
                "amount": float(r.amount),
                "reasoning": r.reasoning or "",
            }
            for r in rows
        ]

    def save_user_message(self, task_id: str, content: str) -> None:
        m = Message(id=str(uuid.uuid4()), task_id=task_id, role="user", content=content)
        self.db.add(m)
        self.db.commit()

    def save_assistant_message(self, task_id: str, content: str) -> None:
        m = Message(id=str(uuid.uuid4()), task_id=task_id, role="assistant", content=content)
        self.db.add(m)
        self.db.commit()

    # --- Intent processors (ローカルロジック) ---
    def _fit_budget(self, estimates: List[Dict[str, Any]], cap: float) -> Tuple[List[Dict[str, Any]], str]:
        totals = self._calc_totals(estimates)
        current = totals["total"]
        if current <= cap:
            return estimates, f"現在の総額は {int(current):,} 円で、上限 {int(cap):,} 円以下のため調整は不要です。"
        # 比率で縮小（税前ベースの縮小）
        ratio = max(0.1, cap / current)
        out = []
        for e in estimates:
            pd = round(float(e["person_days"]) * ratio, 1)
            amount = pd * (float(e["amount"]) / max(float(e["person_days"]) or 1.0, 0.1))
            out.append({**e, "person_days": pd, "amount": amount, "reasoning": (e.get("reasoning") or "")})
        note = f"総額 {int(current):,} 円 → {int(self._calc_totals(out)['total']):,} 円（上限 {int(cap):,} 円に合わせ係数 {ratio:.2f} を適用）"
        return out, note

    def _unit_cost_change(self, estimates: List[Dict[str, Any]], new_unit_cost: float) -> Tuple[List[Dict[str, Any]], str]:
        out = []
        for e in estimates:
            pd = float(e["person_days"])
            amount = pd * new_unit_cost
            out.append({**e, "amount": amount})
        note = f"単価を {int(new_unit_cost):,} 円/人日に変更しました。"
        return out, note

    def _risk_buffer(self, estimates: List[Dict[str, Any]], percent: float) -> Tuple[List[Dict[str, Any]], str]:
        factor = 1.0 + (percent / 100.0)
        out = []
        for e in estimates:
            amount = float(e["amount"]) * factor
            out.append({**e, "amount": amount})
        note = f"リスクバッファ {percent:.1f}% を上乗せしました。"
        return out, note

    def _scope_reduce(self, estimates: List[Dict[str, Any]], keywords: List[str]) -> Tuple[List[Dict[str, Any]], str]:
        kws = [k.strip() for k in keywords if k.strip()]
        if not kws:
            return estimates, "対象キーワードが指定されていません。"
        out = []
        removed = []
        for e in estimates:
            name = (e.get("deliverable_name") or "").lower()
            if any(k.lower() in name for k in kws):
                removed.append(e["deliverable_name"])
                continue
            out.append(e)
        note = "除外対象: " + (", ".join(removed) if removed else "なし")
        return out, note

    # --- 自由入力の意図解析と適用（ルールベース） ---
    def _analyze_and_apply(self, estimates: List[Dict[str, Any]], message: str) -> Tuple[List[Dict[str, Any]], str, bool]:
        m = (message or "").lower()
        targets: list[str] = []
        # 全体適用フラグ（「全体」「合計」「すべて」などの語彙を検出）
        apply_to_all = any(x in m for x in ['全体', '合計', '全部', 'すべて', '全て', 'トータル', '総額', '総計', '全項目', '全成果物'])

        # ターゲット辞書（大幅に拡張）
        mapping = {
            '管理画面': ['管理', '管理画面', 'admin', 'フロント', 'ui', '画面', 'ダッシュボード'],
            'レポート': ['レポート', '帳票', '出力', '印刷', 'エクスポート'],
            'api': ['api', 'エンドポイント', 'rest', 'graphql', 'バックエンド', 'サーバ', 'サーバー'],
            'テスト': ['テスト', '試験', 'test', '検証', 'qa', '品質保証'],
            '認証': ['認証', 'ログイン', 'login', 'auth', 'セキュリティ', 'セッション', 'パスワード'],
            'デザイン': ['デザイン', 'design', 'ui', 'ux', 'css', 'スタイル', '見た目'],
            'インフラ': ['インフラ', 'デプロイ', 'deploy', '環境', '構築', 'サーバ', 'aws', 'クラウド'],
            'ドキュメント': ['ドキュメント', '資料', '説明', 'マニュアル', '手順書', 'readme'],
            'データベース': ['データベース', 'db', 'database', 'sql', 'rdb', 'テーブル', 'スキーマ'],
            '検索': ['検索', 'search', 'サーチ', '全文検索', 'elasticsearch'],
            '通知': ['通知', 'notification', 'メール', 'mail', 'プッシュ', 'アラート'],
            '決済': ['決済', 'payment', '課金', '支払', 'クレジット', 'カード'],
            'バッチ': ['バッチ', 'batch', '定期処理', 'cron', 'ジョブ'],
        }
        for key, kws in mapping.items():
            if any(k in m for k in kws):
                targets.extend(kws)
        # デバッグ出力
        try:
            print(f"[RB] message='{message}' norm='{m}' targets={targets} apply_to_all={apply_to_all}")
        except Exception:
            pass
        # 変更率の推定
        reduce_ratio = None
        # 明示的なパーセンテージ指定（例: 20%下げる/安く）に対応
        pct_match = re.search(r"([1-9]\d?)\s*[%％]", m)
        if pct_match and any(k in m for k in ['下げ', '安く', '削減', '減ら', '縮小', '少なく', '減額', 'カット', 'ダウン']):
            try:
                p = float(pct_match.group(1))
                if 0 < p < 100:
                    reduce_ratio = max(0.1, 1.0 - (p/100.0))
            except Exception:
                pass
        # 言い回しに応じた既定比率（語彙を大幅に拡張）
        if reduce_ratio is None and any(x in m for x in ['簡便', '簡易', '簡単', 'シンプル', 'ライト', '軽量', 'ミニマム', '最小限', '必要最小']):
            reduce_ratio = 0.7  # 30%削減
        if reduce_ratio is None and any(x in m for x in ['安く', '安価', 'コストダウン', '費用抑', 'コスト削減', 'コストカット', '予算削減', '節約', 'もう少し安', '少し安', '価格を下げ', '値下げ']):
            reduce_ratio = 0.8  # 20%削減
        if reduce_ratio is None and any(x in m for x in ['大幅', 'かなり', 'もっと下げ', '大きく下げ', '大きく削減', '大胆', '思い切']):
            reduce_ratio = 0.6  # 40%削減
        # 軽度の削減を示す語彙
        if reduce_ratio is None and any(x in m for x in ['少し下げ', '若干下げ', 'ちょっと下げ', '少しだけ', 'わずかに', '微調整']):
            reduce_ratio = 0.9  # 10%削減
        # 中度の削減を示す語彙
        if reduce_ratio is None and any(x in m for x in ['ある程度', '適度', '程々', 'そこそこ', 'まあまあ']):
            reduce_ratio = 0.85  # 15%削減

        # 完全除外
        full_remove = any(x in m for x in ['除外', '外す', '不要'])
        try:
            print(f"[RB] reduce_ratio={reduce_ratio} full_remove={full_remove}")
        except Exception:
            pass

        changed = []
        new_ests = []
        for e in estimates:
            name = (e.get('deliverable_name') or e.get('name') or '').lower()
            # 全体適用フラグがtrueの場合、または個別ターゲットにマッチする場合
            match = apply_to_all or (any(t in name for t in targets) if targets else False)
            before_pd = float(e.get('person_days', 0.0))
            before_amt = float(e.get('amount', 0.0))
            pd = before_pd
            amt = before_amt
            did_change = False
            if match:
                if full_remove:
                    pd = 0.0
                    amt = 0.0
                    did_change = True
                elif reduce_ratio is not None:
                    new_pd = round(before_pd * reduce_ratio, 1)
                    if abs(new_pd - before_pd) >= 0.05:
                        pd = new_pd
                        amt = pd * settings.get_daily_unit_cost()
                        did_change = True
                # 記録（実際に変化があった場合のみ）
                if did_change:
                    changed.append((e.get('deliverable_name') or e.get('name'), before_pd, pd, int(before_amt), int(amt)))
                try:
                    print(f"[RB] item match name='{e.get('deliverable_name') or e.get('name')}' before={before_pd}/{int(before_amt)} after={pd}/{int(amt)} changed={did_change}")
                except Exception:
                    pass
            # push
            new_ests.append({
                'deliverable_name': e.get('deliverable_name') or e.get('name'),
                'deliverable_description': e.get('deliverable_description') or e.get('description'),
                'person_days': pd,
                'amount': amt,
                'reasoning': e.get('reasoning') or ''
            })

        if not changed and not targets:
            # 対象不明: 自動変更は行わず、具体例を提示
            note = (
                '対象が特定できなかったため見積りは変更していません。\n'
                '以下のように、対象と調整内容を具体的にご指示ください。\n'
                '例) 管理画面を20%下げてください\n'
                '例) 管理画面を簡易版にして30%削減してください\n'
                '例) 管理画面は初期リリース対象外にしてください（除外）\n'
                '例) フロント（UI）を15%下げてください\n'
                '例) API設計とバックエンド開発をそれぞれ10%下げてください\n'
                '例) 認証機能は今回は除外してください\n'
                '例) レポート（帳票）機能を25%下げてください\n'
                '例) テスト（単体・結合）を20%削減してください\n'
                '例) 全体を5%下げてください\n'
                '例) 合計120万円に収まるように調整してください\n'
                '例) 単価を40,000円/人日に変更してください'
            )
        elif not changed and targets and reduce_ratio is None and not full_remove:
            # 対象は見つかったが強度が曖昧 → デフォルトで軽減
            factor = 0.85
            tmp = []
            for e in new_ests:
                nm = (e.get('deliverable_name') or '').lower()
                if any(t in nm for t in targets):
                    pd = round(float(e['person_days']) * factor, 1)
                    amt = pd * settings.get_daily_unit_cost()
                    changed.append((e.get('deliverable_name') or e.get('name'), float(e['person_days']), pd, int(float(e['amount'])), int(amt)))
                    tmp.append({**e, 'person_days': pd, 'amount': amt})
                else:
                    tmp.append(e)
            new_ests = tmp
            lines = ['調整対象（強度自動推定: 15%削減）:']
            for n, bpd, apd, bam, aam in changed:
                lines.append(f'- {n}: {bpd:.1f}人日/{bam:,}円 → {apd:.1f}人日/{aam:,}円')
            note = '\n'.join(lines)
        else:
            lines = ['調整対象:']
            for n, bpd, apd, bam, aam in changed:
                lines.append(f'- {n}: {bpd:.1f}人日/{bam:,}円 → {apd:.1f}人日/{aam:,}円')
            note = '\n'.join(lines)

        try:
            print(f"[RB] changed_count={len(changed)} targets_count={len(targets)}")
        except Exception:
            pass

        has_changes = len(changed) > 0
        return new_ests, note, has_changes

    # --- 金額調整検出（2ステップフロー用） ---
    def _detect_adjustment_request(self, message: str) -> Dict[str, Any] | None:
        """
        「30万円安く」「100万円アップ」などの金額調整リクエストを検出

        Returns:
            {
                'amount': 300000,  # 絶対値
                'direction': 'reduce',  # 'reduce' or 'increase'
            }
            or None
        """
        if not message:
            return None

        m = message.lower()

        # デバッグログ
        print(f"[ChatService] _detect_adjustment_request: message='{message}' normalized='{m}'")

        # パターン1: 「30万円安く」「50万削減」（削減系）
        # 「あと」「さらに」「もっと」などの前置詞に対応
        # 「ほど」「ぐらい」「くらい」などの助詞に対応
        # 「する」「して」「したい」などの動詞に対応
        reduce_patterns = [
            r'(?:あと|さらに|もっと|もう少し)?[\s　]*(\d+)[\s　]*万円?(?:ほど|ぐらい|くらい)?(?:安く|削減|減らし|下げ|カット|ダウン|マイナス)',
            r'(?:あと|さらに|もっと|もう少し)?[\s　]*(\d+)[\s　]*万(?:ほど|ぐらい|くらい)?(?:安く|削減|減らし|下げ|カット|ダウン|マイナス)',
            r'(?:あと|さらに|もっと|もう少し)?[\s　]*(\d+)0{4}[\s　]*円(?:ほど|ぐらい|くらい)?(?:安く|削減|減らし|下げ|カット|ダウン|マイナス)',
        ]

        # パターン2: 「100万円アップ」「50万追加」（増額系）
        increase_patterns = [
            r'(?:あと|さらに|もっと|もう少し)?[\s　]*(\d+)[\s　]*万円?(?:ほど|ぐらい|くらい)?(?:アップ|増やし|追加|上げ|プラス)',
            r'(?:あと|さらに|もっと|もう少し)?[\s　]*(\d+)[\s　]*万(?:ほど|ぐらい|くらい)?(?:アップ|増やし|追加|上げ|プラス)',
            r'(?:あと|さらに|もっと|もう少し)?[\s　]*(\d+)0{4}[\s　]*円(?:ほど|ぐらい|くらい)?(?:アップ|増やし|追加|上げ|プラス)',
        ]

        for pattern in reduce_patterns:
            match = re.search(pattern, m)
            if match:
                amount = int(match.group(1)) * 10000
                print(f"[ChatService] 削減パターン検出: amount={amount:,}円 pattern={pattern}")
                return {'amount': amount, 'direction': 'reduce'}

        for pattern in increase_patterns:
            match = re.search(pattern, m)
            if match:
                amount = int(match.group(1)) * 10000
                print(f"[ChatService] 増額パターン検出: amount={amount:,}円 pattern={pattern}")
                return {'amount': amount, 'direction': 'increase'}

        print(f"[ChatService] 金額調整パターンなし")
        return None

    # --- 提案生成（GPT-4活用） ---
    def _generate_proposals(
        self,
        task_id: str,
        target_change: int,
        direction: str,
        current_estimates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        複数の調整案を生成

        Returns:
            [
                {
                    'id': 'proposal_1',
                    'title': '運用マニュアルを簡素化',
                    'description': '...',
                    'target_amount_change': -120000,
                    'changes': [...],
                    'new_estimates': [...],
                }
            ]
        """
        print(f"[ChatService] _generate_proposals called: task_id={task_id}, amount={target_change}, direction={direction}, estimates={len(current_estimates)}")
        print(f"[ChatService] _OPENAI_AVAILABLE={_OPENAI_AVAILABLE}, has_api_key={bool(getattr(settings, 'OPENAI_API_KEY', None))}")

        if not _OPENAI_AVAILABLE or not getattr(settings, 'OPENAI_API_KEY', None):
            # OpenAI未設定の場合は空配列を返す
            print(f"[ChatService] OpenAI未設定のため提案生成をスキップ")
            return []

        # 現在の見積を整形
        current_summary = json.dumps(
            [
                {
                    "deliverable_name": e.get("deliverable_name"),
                    "person_days": e.get("person_days"),
                    "amount": e.get("amount"),
                }
                for e in current_estimates
            ],
            ensure_ascii=False,
            indent=2
        )

        direction_text = '削減' if direction == 'reduce' else '増額'

        # 言語指示を取得
        language_instruction = t('prompts.chat_language_instruction')

        # GPT-4にプロンプト送信
        prompt = f"""{language_instruction}

あなたは見積調整の専門家です。以下の見積に対して、{direction_text}方向に約{target_change:,}円調整する提案を3つ作成してください。

【現在の見積】
{current_summary}

【要求】
- 方向: {direction_text}
- 目標額: {target_change:,}円

【出力形式】
以下のJSON形式で3つの提案を返してください（コードブロック不要、JSONのみ）：
{{
  "proposals": [
    {{
      "title": "提案タイトル（短く）",
      "description": "提案の概要説明",
      "target_amount_change": -120000,
      "changes": [
        {{
          "deliverable_name": "成果物名",
          "person_days_before": 3.0,
          "person_days_after": 1.0,
          "amount_before": 120000,
          "amount_after": 40000,
          "reasoning": "変更理由を簡潔に"
        }}
      ]
    }}
  ]
}}

【重要な制約】
1. 削減の場合：優先度が低く、リスクが少ない項目から削減（運用マニュアル、テスト、ドキュメント類が候補）
2. 増額の場合：価値が高く、関連性がある項目を追加/強化（セキュリティ、性能、品質が候補）
3. 各提案の合計変化額は目標額±20%以内
4. 論理的整合性を保つ（削減理由、追加理由を明確に）
5. 成果物名は現在の見積に存在するもののみ使用（削減の場合）
6. 増額の場合は新規成果物追加も可（例：セキュリティ強化、性能監視、バックアップ機能など）
7. 単価は{settings.get_daily_unit_cost()}{t('ui.unit_yen')}/人日として計算
"""

        try:
            print(f"[ChatService] GPT-4呼び出し開始: model={getattr(settings, 'OPENAI_MODEL', 'gpt-4o')}")

            # Call LLM with retry and circuit breaker
            content = self._call_proposal_llm_with_retry(prompt)
            print(f"[ChatService] レスポンス内容（最初の200文字）: {content[:200]}")

            # JSONを抽出
            m = re.search(r'\{.*\}', content, re.DOTALL)
            if m:
                print(f"[ChatService] JSON抽出成功")
                data = json.loads(m.group(0))
                proposals_raw = data.get("proposals", [])
                print(f"[ChatService] 生proposals数: {len(proposals_raw)}")

                # 提案ごとに完全な見積を生成
                proposals = []
                for i, prop in enumerate(proposals_raw[:3]):  # 最大3つ
                    proposal_id = f"proposal_{task_id}_{i+1}"
                    new_estimates = self._apply_changes_to_estimates(
                        current_estimates, prop.get('changes', [])
                    )

                    # 実際の削減額を計算（現在の見積 - 新しい見積）
                    current_subtotal = self._calc_totals(current_estimates)['subtotal']
                    new_subtotal = self._calc_totals(new_estimates)['subtotal']
                    actual_change = new_subtotal - current_subtotal

                    print(f"[ChatService] 提案{i+1}作成: title={prop.get('title', '')}, changes={len(prop.get('changes', []))}, actual_change={actual_change:,.0f}円")

                    proposals.append({
                        'id': proposal_id,
                        'title': prop.get('title', f'提案{i+1}'),
                        'description': prop.get('description', ''),
                        'target_amount_change': int(actual_change),  # 実際の変化額を使用
                        'changes': prop.get('changes', []),
                        'new_estimates': new_estimates,
                    })

                # キャッシュに保存
                self._cache_proposals(task_id, proposals)
                print(f"[ChatService] 最終proposals数: {len(proposals)}")

                return proposals
            else:
                print(f"[ChatService] JSON抽出失敗: {content[:500]}")
                return []

        except Exception as e:
            print(f"[ChatService] 提案生成エラー: {e}")
            import traceback
            traceback.print_exc()
            return []

    @retry_with_exponential_backoff()
    def _call_proposal_llm_with_retry(self, prompt: str) -> str:
        """Call LLM for proposal generation with retry logic"""
        client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT
        )

        # System prompt with language instruction
        system_prompt = f"{t('prompts.chat_system')}\n\n{t('prompts.chat_language_instruction')}\n\nあなたは厳密なフォーマットで応答する上級PMです。JSON形式のみで返答してください。"

        resp = client.chat.completions.create(
            model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
            timeout=settings.OPENAI_TIMEOUT
        )

        return resp.choices[0].message.content.strip()

    @retry_with_exponential_backoff()
    def _call_adjustment_llm_with_retry(self, prompt: dict) -> str:
        """Call LLM for general adjustment with retry logic"""
        client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT
        )

        # System prompt with language instruction
        system_prompt = f"{t('prompts.chat_system')}\n\n{t('prompts.chat_language_instruction')}\n\nあなたは厳密なフォーマットで応答する上級PMです。"

        resp = client.chat.completions.create(
            model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": system_prompt},
                prompt,
            ],
            max_tokens=1000,
            temperature=0.2,
            timeout=settings.OPENAI_TIMEOUT
        )

        return resp.choices[0].message.content.strip()

    # --- 変更を見積に適用 ---
    def _apply_changes_to_estimates(
        self,
        current_estimates: List[Dict[str, Any]],
        changes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """変更を見積に適用"""
        import copy
        new_estimates = copy.deepcopy(current_estimates)

        for change in changes:
            deliverable_name = change.get('deliverable_name', '')

            # 既存成果物の変更
            found = False
            for est in new_estimates:
                if est.get('deliverable_name') == deliverable_name:
                    est['person_days'] = float(change.get('person_days_after', 0.0))
                    est['amount'] = float(change.get('amount_after', 0.0))

                    # 変更理由を追記
                    reasoning_notes = est.get('reasoning_notes', est.get('reasoning', ''))
                    reasoning = change.get('reasoning', '')
                    if reasoning:
                        est['reasoning_notes'] = (reasoning_notes + f"\n\n【調整】{reasoning}").strip()

                    found = True
                    break

            # 新規成果物の追加（増額の場合）
            if not found and change.get('person_days_after', 0.0) > 0:
                new_estimates.append({
                    'deliverable_name': deliverable_name,
                    'deliverable_description': change.get('description', ''),
                    'person_days': float(change.get('person_days_after', 0.0)),
                    'amount': float(change.get('amount_after', 0.0)),
                    'reasoning': change.get('reasoning', ''),
                    'reasoning_breakdown': change.get('reasoning', ''),
                    'reasoning_notes': f'【追加機能】{change.get("reasoning", "")}',
                })

        # 0円の項目を除外
        new_estimates = [e for e in new_estimates if float(e.get('amount', 0.0)) > 0]

        return new_estimates

    # --- 提案適用 ---
    def _apply_proposal(self, task_id: str, proposal_id: str) -> List[Dict[str, Any]]:
        """選択された提案を適用"""
        proposals = self._get_cached_proposals(task_id)
        proposal = next((p for p in proposals if p['id'] == proposal_id), None)

        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found in cache")

        return proposal['new_estimates']

    # --- キャッシュ管理 ---
    def _cache_proposals(self, task_id: str, proposals: List[Dict[str, Any]]) -> None:
        """提案をキャッシュに保存"""
        self._proposals_cache[task_id] = proposals

    def _get_cached_proposals(self, task_id: str) -> List[Dict[str, Any]]:
        """キャッシュから提案を取得"""
        return self._proposals_cache.get(task_id, [])

    def process(self, task_id: str, message: str | None, intent: str | None, params: Dict[str, Any] | None, provided_estimates: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        # 読み込み
        if provided_estimates:
            # フロントから現時点表示中の見積りが来た場合はそれを基準にする
            ests = [
                {
                    "deliverable_name": e.get("deliverable_name") or e.get("name"),
                    "deliverable_description": e.get("deliverable_description") or e.get("description"),
                    "person_days": float(e.get("person_days", 0.0)),
                    "amount": float(e.get("amount", 0.0)),
                    "reasoning": e.get("reasoning") or "",
                    "reasoning_breakdown": e.get("reasoning_breakdown") or "",
                    "reasoning_notes": e.get("reasoning_notes") or "",
                }
                for e in provided_estimates
            ]
        else:
            rows = self._load_estimates(task_id)
            if not rows:
                return {"reply_md": "まだ見積りが作成されていません。まずはExcelをアップロードして実行してください。"}
            ests = self._as_dicts(rows)

        # --- 提案適用リクエストの処理 ---
        if intent == 'apply_proposal':
            proposal_id = (params or {}).get('proposal_id')
            if not proposal_id:
                return {"reply_md": "提案IDが指定されていません。", "estimates": ests, "totals": self._calc_totals(ests)}

            try:
                new_estimates = self._apply_proposal(task_id, proposal_id)
                totals = self._calc_totals(new_estimates)

                return {
                    "reply_md": "提案を適用しました！",
                    "estimates": new_estimates,
                    "totals": totals,
                    "version": 2,
                }
            except Exception as e:
                print(f"[ChatService] 提案適用エラー: {e}")
                return {
                    "reply_md": f"提案の適用に失敗しました: {str(e)}",
                    "estimates": ests,
                    "totals": self._calc_totals(ests)
                }

        # --- 金額調整リクエストの検出と提案生成 ---
        adjustment_request = self._detect_adjustment_request(message or "") if message else None

        if adjustment_request:
            # 金額調整リクエストの場合は複数の提案を生成
            if message:
                self.save_user_message(task_id, message)

            proposals = self._generate_proposals(
                task_id=task_id,
                target_change=adjustment_request['amount'],
                direction=adjustment_request['direction'],
                current_estimates=ests,
            )

            if proposals:
                direction_text = '削減' if adjustment_request['direction'] == 'reduce' else '増額'
                reply_md = f"約{adjustment_request['amount']:,}円の{direction_text}案を3つご提案いたします。\n\n以下から最適な案をお選びください。"

                # 提案を返却（見積は変更しない）
                return {
                    "reply_md": reply_md,
                    "proposals": proposals,
                    "estimates": ests,  # 現在の見積を保持
                    "totals": self._calc_totals(ests),
                    "version": 2,
                }
            else:
                # 提案生成失敗時は従来の処理にフォールバック
                reply_md = "提案の生成に失敗しました。従来の調整方法をお試しください。"
                return {
                    "reply_md": reply_md,
                    "estimates": ests,
                    "totals": self._calc_totals(ests),
                    "version": 2,
                }

        # --- 従来の処理（クイックアクション、ルールベース、AI調整） ---
        reply_parts = []
        if message:
            self.save_user_message(task_id, message)
            reply_parts.append(t('messages.ai_request_received'))

        updated = ests
        note = None

        def _num(val, default=0.0):
            try:
                # JSONでnullが来る場合もある
                if val is None:
                    return float(default)
                # 文字列が来た場合の簡易パース（カンマや全角記号除去）
                if isinstance(val, str):
                    v = val.replace(',', '').replace('円', '').replace('％', '').replace('%', '')
                    return float(v)
                return float(val)
            except Exception:
                return float(default)

        if intent == "fit_budget":
            cap = _num((params or {}).get("cap", 0))
            updated, note = self._fit_budget(updated, cap)
        elif intent == "unit_cost_change":
            new_cost = _num((params or {}).get("unit_cost", 40000), 40000)
            updated, note = self._unit_cost_change(updated, new_cost)
        elif intent == "risk_buffer":
            percent = _num((params or {}).get("percent", 10), 10)
            updated, note = self._risk_buffer(updated, percent)
        elif intent == "scope_reduce":
            keywords = (params or {}).get("keywords", [])
            updated, note = self._scope_reduce(updated, keywords)
        else:
            # 自由入力: まずはルールで適用 → さらにAI案が取れれば上書き
            updated, rule_note, has_rule_changes = self._analyze_and_apply(updated, message or "")
            note = rule_note
            if _OPENAI_AVAILABLE and getattr(settings, 'OPENAI_API_KEY', None):
                try:
                    # 言語指示を取得
                    language_instruction = t('prompts.chat_language_instruction')
                    # daily unit cost は設定値を伝え、金額整合を要求
                    prompt = {
                        "role": "user",
                        "content": (
                            f"{language_instruction}\n\n"
                            "以下は現在の見積です。各項目の人日(person_days)と金額(amount)を単価"
                            f"{settings.get_daily_unit_cost()}{t('ui.unit_yen')}/人日で整合がとれるように調整し、依頼文に沿って改善案を出してください。\n"
                            "JSONのみ、コードブロックなしで返してください。フィールドは reply_md, estimates(配列), totals のみ。\n"
                            "estimates の各要素は {deliverable_name, deliverable_description, person_days(小数1桁), amount(数値), reasoning(短いMarkdown可)} とします。\n"
                            f"totals は {{subtotal, tax, total}}（税率{settings.get_tax_rate()*100:.0f}%）です。\n"
                            "依頼文:\n" + (message or "") + "\n\n"
                            "現在の見積(JSON):\n" + json.dumps(updated, ensure_ascii=False)
                        ),
                    }

                    # Call LLM with retry
                    content = self._call_adjustment_llm_with_retry(prompt)
                    m = re.search(r"\{.*\}\s*$", content, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        ai_estimates = data.get("estimates") or []
                        if ai_estimates:
                            # 正規化
                            norm = []
                            for e in ai_estimates:
                                pd = _num(e.get("person_days", 0.0), 0.0)
                                amt = _num(e.get("amount", pd * settings.get_daily_unit_cost()), 0.0)
                                norm.append({
                                    "deliverable_name": e.get("deliverable_name"),
                                    "deliverable_description": e.get("deliverable_description"),
                                    "person_days": pd,
                                    "amount": amt,
                                    "reasoning": e.get("reasoning") or "",
                                })
                            # AI案がルール適用結果と実質同じなら、ルール結果を保持
                            def _differs(a, b):
                                if len(a) != len(b):
                                    return True
                                amap = { (x.get('deliverable_name') or '').lower(): x for x in a }
                                for y in b:
                                    k = (y.get('deliverable_name') or '').lower()
                                    x = amap.get(k)
                                    if not x:
                                        return True
                                    if abs(float(x.get('person_days',0.0)) - float(y.get('person_days',0.0))) >= 0.05:
                                        return True
                                    if abs(float(x.get('amount',0.0)) - float(y.get('amount',0.0))) >= 0.5:
                                        return True
                                return False
                            if _differs(norm, updated):
                                # ルールベースで変更がない場合はAI案を無条件で採用
                                # ルールベースで変更がある場合は、AI案の総額が下がる場合のみ採用
                                if not has_rule_changes:
                                    updated = norm
                                    try:
                                        print(f"[RB] AI案を採用（ルールベースで変更なし）")
                                    except Exception:
                                        pass
                                else:
                                    ai_tot = self._calc_totals(norm).get('total', 0.0)
                                    rb_tot = self._calc_totals(updated).get('total', 0.0)
                                    if ai_tot < rb_tot - 1e-3:
                                        updated = norm
                                        try:
                                            print(f"[RB] AI案を採用（総額改善: {int(rb_tot):,}円 → {int(ai_tot):,}円）")
                                        except Exception:
                                            pass
                                    else:
                                        try:
                                            print(f"[RB] ルール案を保持（AI案は総額改善なし: {int(rb_tot):,}円 vs {int(ai_tot):,}円）")
                                        except Exception:
                                            pass
                        ai_note = (data.get("reply_md") or "AIからの提案を反映しました。")
                        note = (rule_note + "\n\n" + ai_note).strip()
                except Exception as e:
                    # 失敗時は従来のメッセージのみ
                    if not note:
                        note = "（AI提案の取得に失敗したため、見積値は変更していません）"
            else:
                if not note:
                    note = "（AI提案は無効化されているため、見積値は変更していません）"

        totals = self._calc_totals(updated)
        unit = t('ui.unit_yen')
        reply_md = "\n\n".join([p for p in ["\n".join(reply_parts), f"- {note}", f"- {t('messages.summary_subtotal')}: {int(totals['subtotal']):,}{unit} / {t('messages.summary_tax')}: {int(totals['tax']):,}{unit} / {t('messages.summary_total')}: {int(totals['total']):,}{unit}"] if p])

        # 保存（会話のみ）。見積りのDB反映は「適用」APIで予定（フェーズ2）
        self.save_assistant_message(task_id, reply_md)

        # 提案チップを動的生成（上位3件+汎用）
        def build_suggestions(base_ests: List[Dict[str, Any]]):
            top = sorted(base_ests, key=lambda e: float(e.get('amount',0.0)), reverse=True)
            names, seen = [], set()
            for e in top:
                nm = e.get('deliverable_name') or ''
                if nm and nm not in seen:
                    names.append(nm); seen.add(nm)
                if len(names) >= 3: break
            sugs = []
            for nm in names:
                sugs.append({ 'label': t('messages.suggestion_reduce_20').format(name=nm), 'payload': { 'message': t('messages.suggestion_message_reduce_20').format(name=nm) } })
                sugs.append({ 'label': t('messages.suggestion_exclude').format(name=nm), 'payload': { 'message': t('messages.suggestion_message_exclude').format(name=nm) } })
            sugs.append({ 'label': t('messages.suggestion_reduce_all_5'), 'payload': { 'message': t('messages.suggestion_message_reduce_all_5') } })
            sugs.append({ 'label': t('messages.suggestion_unit_cost_40k'), 'payload': { 'intent': 'unit_cost_change', 'params': { 'unit_cost': 40000 } } })
            sugs.append({ 'label': t('messages.suggestion_fit_budget_1.2m'), 'payload': { 'intent': 'fit_budget', 'params': { 'cap': 1200000 } } })
            return sugs

        suggestions = build_suggestions(updated if updated else ests)

        return {
            "reply_md": reply_md,
            "estimates": updated,
            "totals": totals,
            "version": 2,
            "suggestions": suggestions,
        }
