"""質問生成サービス"""
import openai
from typing import List, Dict
from app.core.config import settings


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

        prompt = f"""
あなたは経験豊富なシステム開発プロジェクトマネージャーです。
以下の成果物とシステム要件を基に、見積り精度を向上させるための重要な質問を3つ生成してください。

【成果物一覧】
{deliverable_list}

【システム要件】
{system_requirements}

【指示】
1. 見積り精度向上に最も重要な3つの質問を作成してください
2. 技術的な複雑さ、スケジュール、リソースに関する質問を含めてください
3. 具体的で答えやすい質問にしてください
4. 各質問は一行で簡潔に記載してください
5. 質問番号は付けず、質問文のみを出力してください

出力形式：
質問1の内容
質問2の内容
質問3の内容
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは経験豊富なシステム開発プロジェクトマネージャーです。",
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
            "想定しているユーザー数とアクセス頻度はどの程度ですか？",
            "システムの稼働環境（オンプレミス、クラウド等）はどちらを想定していますか？",
            "外部システムとの連携や既存システムとの統合は必要ですか？",
        ]
