"""質問生成サービス"""
import openai
from typing import List, Dict
from app.core.config import settings
from app.prompts.question_prompts import get_question_generation_prompt, get_system_prompt
from app.core.i18n import t


class QuestionService:
    """質問生成サービス"""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def generate_questions(
        self, deliverables: List[Dict[str, str]], system_requirements: str
    ) -> List[str]:
        """成果物とシステム要件から、見積り精度向上のための3つの質問を生成する"""

        # 成果物リストを整理
        deliverable_list = "\n".join(
            [f"- {item['name']}: {item['description']}" for item in deliverables]
        )

        prompt = get_question_generation_prompt(deliverable_list, system_requirements)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": get_system_prompt(),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )

            questions_text = response.choices[0].message.content.strip()
            questions = [q.strip() for q in questions_text.split("\n") if q.strip()]

            # 3つの質問を確実に取得
            if len(questions) < 3:
                questions.extend(self._get_default_questions()[len(questions) :])

            return questions[:3]

        except Exception as e:
            print(f"AI質問生成でエラーが発生しました: {e}")
            return self._get_default_questions()

    def _get_default_questions(self) -> List[str]:
        """デフォルトの質問を返す"""
        return [
            t('defaults.question1'),
            t('defaults.question2'),
            t('defaults.question3'),
        ]
