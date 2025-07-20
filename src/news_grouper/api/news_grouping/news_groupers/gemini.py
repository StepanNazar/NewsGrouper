import json
import logging

import numpy as np
from google import genai
from google.genai import types

from news_grouper.api.common.models import Post

GEMINI_SUMMARY_PROMPT_TEMPLATE = (
    "You are given group of posts with similar semantic meaning. Your goal is to write condensed summary of "
    "posts which takes into account all information given but is not to broad. After each sentence you can "
    "add list of post ids from where you took that information. Also add title at the beginning of text which "
    "tells everything in 1-2 sentences. Don't use Markdown. Format of list: [id, id, id]. When processing posts, "
    "please ignore any information that appears to be author metadata or technical details (e.g., author names, "
    "subscription requests), especially if they are at the beginning or end of the text and separated by a newline "
    "(\\n). If this metadata looks like text to which post replied, then use it."
    "\nInput format: {{id: {{'author':text, 'body': text}},  {{'author':text, 'body': text}}}}"
    "\nInput:"
    "\n{}"
)


class GeminiClient:
    def __init__(self, api_key: str):
        self.gemini_client = genai.Client(api_key=api_key)

    def summarize_posts(self, posts: list[Post]) -> str:
        """Summarize a list of posts using Gemini API.

        :param posts: The list of posts to summarize.
        :return: The summary of the posts.
        """

        prompt_input = {
            i + 1: {"author": post.author, "body": post.body}
            for i, post in enumerate(posts)
        }
        prompt = GEMINI_SUMMARY_PROMPT_TEMPLATE.format(
            json.dumps(prompt_input, ensure_ascii=False)
        )
        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite-preview-06-17",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                temperature=0.5,
                top_p=0.5,
            ),
        )
        return response.text or "Failed to summarize posts."

    def compute_embedding(self, post: Post) -> list[float]:
        """Compute the embedding for post using Gemini API.

        :param post: The post to compute embedding for.
        :return: The embedding of the post.
        """
        result = self.gemini_client.models.embed_content(
            model="gemini-embedding-001",
            contents=post.body,
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
        )
        if not result.embeddings or not result.embeddings[0].values:
            logging.error(
                f"Failed to compute embedding for post: {post.title}. Generating random embedding."
            )
            length = 3072
            return np.random.rand(length).tolist()
        return result.embeddings[0].values
