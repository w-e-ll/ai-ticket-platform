from __future__ import annotations

from openai import AsyncOpenAI

from ai_ticket_platform.app.ai.prompts import render_prompt
from ai_ticket_platform.app.config import get_settings
from ai_ticket_platform.app.utils.errors import LLMServiceError
from ai_ticket_platform.app.utils.logging import get_logger


logger = get_logger(__name__)


class LLMService:
    """Service for LLM-based generation tasks."""

    def __init__(self) -> None:
        """Initialize LLM client."""
        self.settings = get_settings()
        self.model = self.settings.openai_model
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

        logger.info(
            "LLM service initialized",
            extra={
                "event": "llm_service_initialized",
                "operation": "llm_service_init",
                "status": "success",
                "provider": "openai",
                "model": self.model,
            },
        )

    async def generate_rag_answer(
        self,
        *,
        question: str,
        context: str,
    ) -> str:
        """Generate grounded answer from retrieved context."""
        question = self._validate_text(question, field_name="question")
        context = self._validate_text(context, field_name="context")

        logger.info(
            "RAG LLM answer generation started",
            extra={
                "event": "rag_llm_answer_generation_started",
                "operation": "generate_rag_answer",
                "status": "started",
                "provider": "openai",
                "model": self.model,
                "question_length": len(question),
                "context_length": len(context),
            },
        )

        try:
            system_prompt, user_prompt = render_prompt(
                template_name="rag_qa_prompt",
                question=question,
                context=context,
            )

            answer = await self._chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                operation="generate_rag_answer",
            )

            logger.info(
                "RAG LLM answer generation completed",
                extra={
                    "event": "rag_llm_answer_generation_completed",
                    "operation": "generate_rag_answer",
                    "status": "success",
                    "provider": "openai",
                    "model": self.model,
                    "answer_length": len(answer),
                },
            )

            return answer

        except LLMServiceError:
            raise

        except Exception as exc:
            logger.error(
                "RAG LLM answer generation failed",
                extra={
                    "event": "rag_llm_answer_generation_failed",
                    "operation": "generate_rag_answer",
                    "status": "failed",
                    "provider": "openai",
                    "model": self.model,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise LLMServiceError("Failed to generate RAG answer") from exc

    async def classify_ticket_with_llm(self, *, ticket_content: str) -> str:
        """Classify ticket with LLM routing prompt."""
        ticket_content = self._validate_text(
            ticket_content,
            field_name="ticket_content",
        )

        logger.info(
            "LLM ticket classification started",
            extra={
                "event": "llm_ticket_classification_started",
                "operation": "classify_ticket_with_llm",
                "status": "started",
                "provider": "openai",
                "model": self.model,
                "text_length": len(ticket_content),
            },
        )

        try:
            system_prompt, user_prompt = render_prompt(
                template_name="ticket_classification_prompt",
                ticket_content=ticket_content,
            )

            department = await self._chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                operation="classify_ticket_with_llm",
            )

            normalized_department = department.strip().lower()

            logger.info(
                "LLM ticket classification completed",
                extra={
                    "event": "llm_ticket_classification_completed",
                    "operation": "classify_ticket_with_llm",
                    "status": "success",
                    "provider": "openai",
                    "model": self.model,
                    "department": normalized_department,
                },
            )

            return normalized_department

        except LLMServiceError:
            raise

        except Exception as exc:
            logger.error(
                "LLM ticket classification failed",
                extra={
                    "event": "llm_ticket_classification_failed",
                    "operation": "classify_ticket_with_llm",
                    "status": "failed",
                    "provider": "openai",
                    "model": self.model,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise LLMServiceError("Failed to classify ticket with LLM") from exc

    async def summarize_ticket(self, *, ticket_content: str) -> str:
        """Generate short professional ticket summary."""
        ticket_content = self._validate_text(
            ticket_content,
            field_name="ticket_content",
        )

        logger.info(
            "Ticket summarization started",
            extra={
                "event": "ticket_summarization_started",
                "operation": "summarize_ticket",
                "status": "started",
                "provider": "openai",
                "model": self.model,
                "text_length": len(ticket_content),
            },
        )

        try:
            system_prompt, user_prompt = render_prompt(
                template_name="ticket_summarization_prompt",
                ticket_content=ticket_content,
            )

            summary = await self._chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                operation="summarize_ticket",
            )

            logger.info(
                "Ticket summarization completed",
                extra={
                    "event": "ticket_summarization_completed",
                    "operation": "summarize_ticket",
                    "status": "success",
                    "provider": "openai",
                    "model": self.model,
                    "summary_length": len(summary),
                },
            )

            return summary

        except LLMServiceError:
            raise

        except Exception as exc:
            logger.error(
                "Ticket summarization failed",
                extra={
                    "event": "ticket_summarization_failed",
                    "operation": "summarize_ticket",
                    "status": "failed",
                    "provider": "openai",
                    "model": self.model,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise LLMServiceError("Failed to summarize ticket") from exc

    async def analyze_escalation(self, *, ticket_content: str) -> str:
        """Analyze ticket escalation risk."""
        ticket_content = self._validate_text(
            ticket_content,
            field_name="ticket_content",
        )

        logger.info(
            "Ticket escalation analysis started",
            extra={
                "event": "ticket_escalation_analysis_started",
                "operation": "analyze_escalation",
                "status": "started",
                "provider": "openai",
                "model": self.model,
                "text_length": len(ticket_content),
            },
        )

        try:
            system_prompt, user_prompt = render_prompt(
                template_name="escalation_analysis_prompt",
                ticket_content=ticket_content,
            )

            analysis = await self._chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                operation="analyze_escalation",
            )

            logger.info(
                "Ticket escalation analysis completed",
                extra={
                    "event": "ticket_escalation_analysis_completed",
                    "operation": "analyze_escalation",
                    "status": "success",
                    "provider": "openai",
                    "model": self.model,
                    "analysis_length": len(analysis),
                },
            )

            return analysis

        except LLMServiceError:
            raise

        except Exception as exc:
            logger.error(
                "Ticket escalation analysis failed",
                extra={
                    "event": "ticket_escalation_analysis_failed",
                    "operation": "analyze_escalation",
                    "status": "failed",
                    "provider": "openai",
                    "model": self.model,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise LLMServiceError("Failed to analyze ticket escalation") from exc

    async def _chat_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        operation: str,
    ) -> str:
        """Call OpenAI chat completion API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )

            content = response.choices[0].message.content

            if not content or not content.strip():
                raise LLMServiceError("LLM returned empty response")

            logger.info(
                "LLM chat completion completed",
                extra={
                    "event": "llm_chat_completion_completed",
                    "operation": operation,
                    "status": "success",
                    "provider": "openai",
                    "model": self.model,
                },
            )

            return content.strip()

        except LLMServiceError:
            raise

        except Exception as exc:
            logger.error(
                "LLM chat completion failed",
                extra={
                    "event": "llm_chat_completion_failed",
                    "operation": operation,
                    "status": "failed",
                    "provider": "openai",
                    "model": self.model,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True,
            )

            raise LLMServiceError("LLM chat completion failed") from exc

    def _validate_text(self, value: str, *, field_name: str) -> str:
        """Validate and normalize text input."""
        if not isinstance(value, str):
            raise LLMServiceError(f"{field_name} must be a string")

        normalized = " ".join(value.strip().split())

        if not normalized:
            raise LLMServiceError(f"{field_name} must not be empty")

        if len(normalized) > 50000:
            raise LLMServiceError(f"{field_name} is too long")

        return normalized
