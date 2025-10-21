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

【reasoning_breakdown のフォーマット】
以下の統一フォーマットで記載してください：
{t('prompts.estimate_breakdown_format')}

【見積り範囲】
- 設計・実装・テスト・ドキュメント作成を含める
- 成果物の複雑さを考慮した現実的な工数
- reasoning_breakdownには工程別の数値内訳を統一フォーマットで記載
- reasoning_notesには前提条件やリスク、注意点を記載
"""


def get_system_prompt() -> str:
    """システムプロンプトを取得（安全ガイドライン・言語指示付き）"""
    base_prompt = t('prompts.estimate_system')
    safety_guidelines = get_safety_guidelines()
    language_instruction = t('prompts.language_instruction')
    return f"{base_prompt}\n\n{safety_guidelines}\n\n{language_instruction}"
