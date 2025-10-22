"""見積りプロンプト"""
from app.core.i18n import t
from app.prompts.safety_guidelines import get_safety_guidelines


def get_estimate_prompt(deliverable: dict, system_requirements: str, qa_text: str) -> str:
    """見積りプロンプトを生成"""
    unit = t('prompts.estimate_unit')

    return f"""
{t('prompts.estimate_system')}
{t('prompts.estimate_instruction')}

【成果物情報】
{t('ui.label_deliverable_name')}: {deliverable['name']}
{t('ui.label_deliverable_desc')}: {deliverable['description']}

【{t('ui.label_system_requirements')}】
{system_requirements}

【追加情報】
{qa_text}

【厳守事項】
- 単位は必ず「{unit}」を使用し、数字の桁を間違えないこと（例: 4.5{unit}を45と書かない）
- reasoning_breakdown内のすべての数量表記も「{unit}」とし、小数1桁を維持する

【出力形式】
次のJSONのみをコードブロックなしで返す：
{{
  "person_days": 小数1桁の数値（例: 4.5）,
  "reasoning_breakdown": "工数内訳（Markdown可）。工程別の{unit}内訳を箇条書きで記載。",
  "reasoning_notes": "根拠・備考（Markdown可）。見積りの前提条件、リスク、補足説明など。"
}}

【重要】reasoning_breakdownとreasoning_notesは明確に分離すること！

【reasoning_breakdown の記載内容】
工程別の数値内訳のみを箇条書きで記載。説明文や前提条件は含めない。
例：
- 要件定義: 5.0{unit}
- 設計: 3.0{unit}
- 実装: 4.0{unit}
- テスト: 2.0{unit}
- ドキュメント作成: 1.0{unit}

【reasoning_notes の記載内容】
見積りの前提条件、リスク、補足説明を記載。工程別の数値内訳は含めない。
例：
本見積もりはECシステムの要件定義書作成に基づいています。要件定義にはシステム全体の要件を整理するための時間が必要です。設計は比較的シンプルであり、実装も潤沢な人員がいるため、工数を抑えています。テストは基本的な機能確認を行うための時間を見込んでいます。リスクとしては、要件の変更や追加が発生する可能性があるため、柔軟に対応できる体制が必要です。

【見積り範囲】
- 設計・実装・テスト・ドキュメント作成を含める
- 成果物の複雑さを考慮した現実的な工数
- reasoning_breakdownには工程別の数値内訳のみを統一フォーマットで記載（説明文は含めない）
- reasoning_notesには前提条件、リスク、注意点、補足説明を記載（数値内訳は含めない）
"""


def get_system_prompt() -> str:
    """システムプロンプトを取得（安全ガイドライン・言語指示付き）"""
    base_prompt = t('prompts.estimate_system')
    safety_guidelines = get_safety_guidelines()
    language_instruction = t('prompts.language_instruction')
    return f"{base_prompt}\n\n{safety_guidelines}\n\n{language_instruction}"
