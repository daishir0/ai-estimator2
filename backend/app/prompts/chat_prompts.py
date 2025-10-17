"""チャット調整プロンプト"""
from app.core.i18n import t


def get_chat_system_prompt() -> str:
    """チャットシステムプロンプトを取得（言語指示付き）"""
    base_prompt = t('prompts.chat_system')
    language_instruction = t('prompts.chat_language_instruction')
    return f"{base_prompt}\n\n{language_instruction}"


def get_proposal_generation_prompt(user_message: str, estimates: list, totals: dict) -> str:
    """提案生成プロンプトを生成（言語指示付き）"""
    unit = t('prompts.estimate_unit')
    base_prompt = t('prompts.chat_system')
    language_instruction = t('prompts.chat_language_instruction')

    estimates_text = "\n".join([
        f"- {e['deliverable_name']}: {e['person_days']}{unit} ({e['amount']:,}円)"
        for e in estimates
    ])

    return f"""
{base_prompt}
{language_instruction}

ユーザーの要望に基づいて、見積りの調整案を3つ提案してください。

【現在の見積り】
{estimates_text}

合計: {totals.get('subtotal', 0):,}円（税抜）

【ユーザーの要望】
{user_message}

【指示】
1. ユーザーの要望を満たす具体的な調整案を3つ提案してください
2. 各提案には、タイトル、説明、具体的な変更内容を含めてください
3. 現実的で実行可能な提案にしてください

【出力形式】
以下のJSON形式で返してください：
{{
  "proposals": [
    {{
      "title": "提案1のタイトル",
      "description": "提案1の説明",
      "target_amount_change": 目標金額変更（負の値で減額）,
      "changes": [
        {{
          "deliverable_name": "成果物名",
          "person_days_change": 工数変更（負の値で削減）,
          "reason": "変更理由"
        }}
      ]
    }}
  ]
}}
"""
