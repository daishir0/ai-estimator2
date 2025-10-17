"""質問生成プロンプト"""
from app.core.i18n import t


def get_question_generation_prompt(deliverables_text: str, system_requirements: str) -> str:
    """質問生成プロンプトを生成"""
    return f"""
{t('prompts.question_system')}
{t('prompts.question_instruction')}

【{t('ui.label_deliverable_name')}】
{deliverables_text}

【{t('ui.label_system_requirements')}】
{system_requirements}

【指示】
1. {t('prompts.question_instruction')}
2. 技術的な複雑さ、スケジュール、リソースに関する質問を含めてください
3. 具体的で答えやすい質問にしてください
4. 各質問は一行で簡潔に記載してください
5. 質問番号は付けず、質問文のみを出力してください

出力形式：
{t('prompts.question_format')}
"""


def get_system_prompt() -> str:
    """システムプロンプトを取得"""
    return t('prompts.question_system')
