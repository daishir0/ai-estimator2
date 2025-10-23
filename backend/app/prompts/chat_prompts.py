"""チャット調整プロンプト"""
from app.core.i18n import t
from app.prompts.safety_guidelines import get_safety_guidelines


def get_chat_system_prompt() -> str:
    """チャットシステムプロンプトを取得（安全ガイドライン・言語指示付き）"""
    base_prompt = t('prompts.chat_system')
    safety_guidelines = get_safety_guidelines()
    language_instruction = t('prompts.chat_language_instruction')
    return f"{base_prompt}\n\n{safety_guidelines}\n\n{language_instruction}"


def get_proposal_generation_prompt(user_message: str, estimates: list, totals: dict) -> str:
    """提案生成プロンプトを生成（安全ガイドライン・言語指示付き）"""
    unit = t('prompts.estimate_unit')
    currency = t('prompts.currency_symbol')
    base_prompt = t('prompts.chat_system')
    safety_guidelines = get_safety_guidelines()
    language_instruction = t('prompts.chat_language_instruction')

    # 見積りリスト（多言語対応）
    estimates_text = "\n".join([
        f"- {e['deliverable_name']}: {e['person_days']}{unit} ({e['amount']:,}{currency})"
        for e in estimates
    ])

    # プロンプトテキスト（多言語対応）
    proposal_instruction = t('prompts.chat_proposal_instruction')
    current_estimate_label = t('prompts.chat_current_estimate')
    subtotal_label = t('prompts.chat_subtotal')
    before_tax_label = t('prompts.chat_before_tax')
    user_request_label = t('prompts.chat_user_request')
    instructions_title = t('prompts.chat_instructions_title')
    instruction_1 = t('prompts.chat_instruction_1')
    instruction_2 = t('prompts.chat_instruction_2')
    instruction_3 = t('prompts.chat_instruction_3')
    output_format_title = t('prompts.chat_output_format_title')
    output_format_description = t('prompts.chat_output_format_description')

    # JSON例の翻訳
    json_proposal_title = t('prompts.chat_json_proposal_title')
    json_proposal_description = t('prompts.chat_json_proposal_description')
    json_target_amount_change = t('prompts.chat_json_target_amount_change')
    json_deliverable_name = t('prompts.chat_json_deliverable_name')
    json_person_days_change = t('prompts.chat_json_person_days_change')
    json_reason = t('prompts.chat_json_reason')

    return f"""
{base_prompt}
{safety_guidelines}
{language_instruction}

{proposal_instruction}

【{current_estimate_label}】
{estimates_text}

{subtotal_label}: {totals.get('subtotal', 0):,}{currency}（{before_tax_label}）

【{user_request_label}】
{user_message}

【{instructions_title}】
{instruction_1}
{instruction_2}
{instruction_3}

【{output_format_title}】
{output_format_description}
{{
  "proposals": [
    {{
      "title": "{json_proposal_title}",
      "description": "{json_proposal_description}",
      "target_amount_change": {json_target_amount_change},
      "changes": [
        {{
          "deliverable_name": "{json_deliverable_name}",
          "person_days_change": {json_person_days_change},
          "reason": "{json_reason}"
        }}
      ]
    }}
  ]
}}
"""
