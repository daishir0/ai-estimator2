"""Question generation service"""
import openai
import logging
from typing import List, Dict
from app.core.config import settings
from app.prompts.question_prompts import get_question_generation_prompt, get_system_prompt
from app.core.i18n import t
from app.services.retry_service import retry_with_exponential_backoff
from app.services.circuit_breaker import openai_circuit_breaker

logger = logging.getLogger(__name__)


class QuestionService:
    """Question generation service"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT
        )
        self.model = settings.OPENAI_MODEL

    def generate_questions(
        self, deliverables: List[Dict[str, str]], system_requirements: str
    ) -> List[str]:
        """Generate 3 questions to improve estimation accuracy from deliverables and system requirements"""

        try:
            # Call through circuit breaker
            return openai_circuit_breaker.call(
                self._call_llm_with_retry,
                deliverables,
                system_requirements
            )
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            # Use default questions as fallback
            return self._get_default_questions()

    @retry_with_exponential_backoff()
    def _call_llm_with_retry(
        self, deliverables: List[Dict[str, str]], system_requirements: str
    ) -> List[str]:
        """Call LLM with retry logic (exponential backoff)"""
        # Format deliverable list
        deliverable_list = "\n".join(
            [f"- {item['name']}: {item['description']}" for item in deliverables]
        )

        prompt = get_question_generation_prompt(deliverable_list, system_requirements)

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
            timeout=settings.OPENAI_TIMEOUT
        )

        questions_text = response.choices[0].message.content.strip()
        questions = [q.strip() for q in questions_text.split("\n") if q.strip()]

        # Ensure 3 questions
        if len(questions) < 3:
            questions.extend(self._get_default_questions()[len(questions):])

        return questions[:3]

    def _get_default_questions(self) -> List[str]:
        """Return default questions"""
        return [
            t('defaults.question1'),
            t('defaults.question2'),
            t('defaults.question3'),
        ]
