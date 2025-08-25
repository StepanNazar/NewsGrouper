import json
import logging
from typing import Callable

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from news_grouper.api.common.models import Post

GEMINI_SUMMARY_PROMPT_TEMPLATE = (
    "You are given group of posts with similar semantic meaning. Your goal is to write condensed summary of "
    "posts which takes into account all information given but is not to broad. After each sentence you can "
    "add list of post ids from where you took that information. Also add title at the beginning of text which "
    "tells everything in 1-2 sentences. Don't use Markdown. Format of list: [id, id, id]. When processing posts, "
    "please ignore any information that appears to be author metadata or technical details (e.g., author names, "
    "subscription requests), especially if they are at the beginning or end of the text and separated by a newline "
    "(\\n). If this metadata looks like text to which post replied, then use it."
    "\nInput format: {{id: {{'author': text, 'body': text}},  {{'author': text, 'body': text}}}}"
    "\nInput:"
    "\n{}"
)
SUMMARY_MODEL = "gemini-2.5-flash-lite-preview-06-17"
TOP_P = 0.5
TEMPERATURE = 0.5
THINKING_BUDGET = 0

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_TASK_TYPE = "SEMANTIC_SIMILARITY"
EMBEDDING_LENGTH = 3072

RETRY_WAIT_SECONDS = 2
RETRY_ATTEMPTS = 5

logger = logging.getLogger(__name__)


def _retry_decorator(
    wait_seconds: int = RETRY_WAIT_SECONDS, attempts: int = RETRY_ATTEMPTS
) -> Callable:
    return retry(
        retry=retry_if_exception_type((genai_errors.ClientError, GeminiResponseError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        wait=wait_fixed(wait_seconds),
        stop=stop_after_attempt(attempts),
    )


def _create_summarization_prompt(posts: list[Post]) -> str:
    """Create a prompt for summarizing posts."""
    prompt_input = {
        i + 1: {"author": post.author, "body": post.body}
        for i, post in enumerate(posts)
    }
    prompt = GEMINI_SUMMARY_PROMPT_TEMPLATE.format(
        json.dumps(prompt_input, ensure_ascii=False)
    )
    return prompt


class GeminiResponseError(Exception):
    """Custom exception for Gemini API response errors."""


class GeminiEmptyTextError(GeminiResponseError):
    """Exception raised when generated text is empty."""


class GeminiEmptyEmbeddingError(GeminiResponseError):
    """Exception raised when returned embedding is empty."""


class GeminiClient:
    def __init__(self, api_key: str):
        self.gemini_client = genai.Client(api_key=api_key)

    def summarize_posts(self, posts: list[Post]) -> str:
        """Summarize a list of posts using Gemini API.

        :param posts: The list of posts to summarize.
        :return: The summary of the posts.
        """
        prompt = _create_summarization_prompt(posts)
        try:
            return self._generate_content_with_retry(prompt)
        except RetryError as e:
            logger.error("Failed to generate summary after retries: %s", e)
            return "Failed to generate summary."

    @_retry_decorator()
    def _generate_content_with_retry(self, prompt: str) -> str:
        """Generate content using Gemini API with retry logic."""
        response = self.gemini_client.models.generate_content(
            model=SUMMARY_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
                temperature=TEMPERATURE,
                top_p=TOP_P,
            ),
        )
        if response.text is None:
            raise GeminiEmptyTextError("Empty response text")
        return response.text

    def compute_embedding(self, post: Post) -> list[float] | None:
        """Compute the embedding for post using Gemini API.

        :param post: The post to compute embedding for.
        :return: The embedding of the post or None if failed.
        """
        try:
            return self._embed_content_with_retry(post.body)
        except RetryError as e:
            logger.error("Failed to compute embedding after retries: %s", e)
            return None

    @_retry_decorator()
    def _embed_content_with_retry(self, content: str) -> list[float]:
        """Compute the embedding for content using Gemini API with retry logic."""
        response = self.gemini_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=content,
            config=types.EmbedContentConfig(task_type=EMBEDDING_TASK_TYPE),
        )
        if not response.embeddings or not response.embeddings[0].values:
            raise GeminiEmptyEmbeddingError("Empty embeddings in response")
        return response.embeddings[0].values
