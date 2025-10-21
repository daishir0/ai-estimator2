"""Question generation service"""
import openai
import time
from typing import List, Dict, Optional
from app.core.config import settings
from app.prompts.question_prompts import get_question_generation_prompt, get_system_prompt
from app.core.i18n import t
from app.services.retry_service import retry_with_exponential_backoff
from app.services.circuit_breaker import openai_circuit_breaker
from app.core.logging_config import get_logger
from app.core.metrics import metrics_collector

logger = get_logger(__name__)


class QuestionService:
    """Question generation service"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT
        )
        self.model = settings.OPENAI_MODEL

    def generate_questions(
        self, deliverables: List[Dict[str, str]], system_requirements: str,
        request_id: Optional[str] = None
    ) -> List[str]:
        """Generate 3 questions to improve estimation accuracy from deliverables and system requirements"""

        logger.info(
            "Starting question generation",
            request_id=request_id,
            deliverable_count=len(deliverables)
        )

        try:
            # Call through circuit breaker
            questions = openai_circuit_breaker.call(
                self._call_llm_with_retry,
                deliverables,
                system_requirements,
                request_id
            )
            logger.info(
                "Question generation completed",
                request_id=request_id,
                question_count=len(questions)
            )
            return questions
        except Exception as e:
            logger.error(
                f"Question generation failed: {e}",
                request_id=request_id
            )
            # Use default questions as fallback
            logger.warning(
                "Using default questions as fallback",
                request_id=request_id
            )
            return self._get_default_questions()

    @retry_with_exponential_backoff()
    def _call_llm_with_retry(
        self, deliverables: List[Dict[str, str]], system_requirements: str,
        request_id: Optional[str] = None
    ) -> List[str]:
        """Call LLM with retry logic (exponential backoff)"""
        # Format deliverable list
        deliverable_list = "\n".join(
            [f"- {item['name']}: {item['description']}" for item in deliverables]
        )

        prompt = get_question_generation_prompt(deliverable_list, system_requirements)

        # Measure OpenAI API call duration
        start_time = time.perf_counter()
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
                timeout=settings.OPENAI_TIMEOUT
            )
            duration = time.perf_counter() - start_time

            # Record successful OpenAI API call metrics (TODO-9: added input/output tokens for cost tracking)
            metrics_collector.record_openai_call(
                model=self.model,
                tokens=response.usage.total_tokens,
                duration=duration,
                success=True,
                request_id=request_id or "unknown",
                operation="question",
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens
            )

            logger.debug(
                "OpenAI API call successful",
                request_id=request_id,
                model=self.model,
                tokens=response.usage.total_tokens,
                duration=round(duration, 3)
            )

            questions_text = response.choices[0].message.content.strip()
            questions = [q.strip() for q in questions_text.split("\n") if q.strip()]

            # Ensure 3 questions
            if len(questions) < 3:
                questions.extend(self._get_default_questions()[len(questions):])

            return questions[:3]

        except Exception as e:
            duration = time.perf_counter() - start_time

            # Record failed OpenAI API call metrics (TODO-9: added input/output tokens for cost tracking)
            metrics_collector.record_openai_call(
                model=self.model,
                tokens=0,
                duration=duration,
                success=False,
                request_id=request_id or "unknown",
                operation="question",
                input_tokens=0,
                output_tokens=0
            )

            logger.error(
                "OpenAI API call failed",
                request_id=request_id,
                model=self.model,
                error=str(e),
                duration=round(duration, 3)
            )
            raise

    def _get_default_questions(self) -> List[str]:
        """Return default questions"""
        return [
            t('defaults.question1'),
            t('defaults.question2'),
            t('defaults.question3'),
        ]
