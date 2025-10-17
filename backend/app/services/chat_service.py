"""見積り調整チャットサービス

- クイックアクション: ローカルロジックで即時計算
- AI見積調整: 自由入力（message）の場合はOpenAIで提案を生成（同期）
"""
from typing import List, Dict, Any, Tuple
import uuid
from app.models import Estimate, Task, Message
from sqlalchemy.orm import Session
from app.core.config import settings
import json
import re

try:
    import openai
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False


class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def _load_estimates(self, task_id: str) -> List[Estimate]:
        return self.db.query(Estimate).filter(Estimate.task_id == task_id).all()

    def _calc_totals(self, estimates: List[Dict[str, Any]]) -> Dict[str, float]:
        subtotal = float(sum(e.get("amount", 0.0) for e in estimates))
        tax = round(subtotal * 0.1, 2)
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
                        amt = pd * settings.DAILY_UNIT_COST
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
                    amt = pd * settings.DAILY_UNIT_COST
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
                }
                for e in provided_estimates
            ]
        else:
            rows = self._load_estimates(task_id)
            if not rows:
                return {"reply_md": "まだ見積りが作成されていません。まずはExcelをアップロードして実行してください。"}
            ests = self._as_dicts(rows)

        reply_parts = []
        if message:
            self.save_user_message(task_id, message)
            reply_parts.append("ご要望を承知しました。以下の調整案を適用します。")

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
                    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                    # daily unit cost は設定値を伝え、金額整合を要求
                    prompt = {
                        "role": "user",
                        "content": (
                            "以下は現在の見積です。各項目の人日(person_days)と金額(amount)を単価"
                            f"{settings.DAILY_UNIT_COST}円/人日で整合がとれるように調整し、依頼文に沿って改善案を出してください。\n"
                            "JSONのみ、コードブロックなしで返してください。フィールドは reply_md, estimates(配列), totals のみ。\n"
                            "estimates の各要素は {deliverable_name, deliverable_description, person_days(小数1桁), amount(数値), reasoning(短いMarkdown可)} とします。\n"
                            "totals は {subtotal, tax, total}（税込10%）です。\n"
                            "依頼文:\n" + (message or "") + "\n\n"
                            "現在の見積(JSON):\n" + json.dumps(updated, ensure_ascii=False)
                        ),
                    }
                    resp = client.chat.completions.create(
                        model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
                        messages=[
                            {"role": "system", "content": "あなたは厳密なフォーマットで応答する上級PMです。"},
                            prompt,
                        ],
                        max_tokens=1000,
                        temperature=0.2,
                    )
                    content = resp.choices[0].message.content.strip()
                    m = re.search(r"\{.*\}\s*$", content, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        ai_estimates = data.get("estimates") or []
                        if ai_estimates:
                            # 正規化
                            norm = []
                            for e in ai_estimates:
                                pd = _num(e.get("person_days", 0.0), 0.0)
                                amt = _num(e.get("amount", pd * settings.DAILY_UNIT_COST), 0.0)
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
        reply_md = "\n\n".join([p for p in ["\n".join(reply_parts), f"- {note}", f"- 小計: {int(totals['subtotal']):,} 円 / 税額: {int(totals['tax']):,} 円 / 合計: {int(totals['total']):,} 円"] if p])

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
                sugs.append({ 'label': f"{nm}を20%下げる", 'payload': { 'message': f"{nm}を20%下げてください" } })
                sugs.append({ 'label': f"{nm}を除外", 'payload': { 'message': f"{nm}は今回は除外してください" } })
            sugs.append({ 'label': '全体を5%下げる', 'payload': { 'message': '全体を5%下げてください' } })
            sugs.append({ 'label': '単価を4万円/人日に', 'payload': { 'intent': 'unit_cost_change', 'params': { 'unit_cost': 40000 } } })
            sugs.append({ 'label': '上限120万円に合わせる', 'payload': { 'intent': 'fit_budget', 'params': { 'cap': 1200000 } } })
            return sugs

        suggestions = build_suggestions(updated if updated else ests)

        return {
            "reply_md": reply_md,
            "estimates": updated,
            "totals": totals,
            "version": 2,
            "suggestions": suggestions,
        }
