import json
import logging
from collections import defaultdict

import numpy as np
from google import genai
from google.genai import types
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances

from news_grouper.api.common.models import Post, PostGroup
from news_grouper.api.config import GOOGLE_API_KEY
from news_grouper.api.news_grouping.news_groupers.abstract_grouper import NewsGrouper

GEMINI_SUMMARY_PROMPT_TEMPLATE = """You are given group of posts with similar semantic meaning. Your goal is to write condensed summary of posts which takes into account all information given but is not to broad. After each sentence you can add list of post ids from where you took that information. Format of list: [id, id, id].  When processing posts, please ignore any information that appears to be author metadata or technical details (e.g., author names, subscription requests), especially if they are at the beginning or end of the text and separated by a newline (\n). If this metadata looks like text to which post replied, then use it.
Input format: {{id: {{'author':text, 'body': text}},  {{'author':text, 'body': text}}}}
Input:
{}
"""

gemini_client = genai.Client(api_key=GOOGLE_API_KEY)


class EmbeddingsDBSCANGrouper(NewsGrouper):
    """Grouper that uses embeddings and DBSCAN to group posts."""

    name = "Embeddings DBSCAN"
    description = "Converts posts into embeddings using Gemini API, groups them using DBSCAN and writes summaries using Gemini API."

    @staticmethod
    def group_posts(posts: list[Post]) -> list[Post | PostGroup]:
        """Group posts using embeddings and DBSCAN.

        :param posts: The list of posts to group.
        :return: A list of grouped posts.
        """
        embeddings = EmbeddingsDBSCANGrouper.compute_gemini_embeddings(posts)
        distance_matrix = cosine_distances(embeddings)
        clustering = DBSCAN(eps=0.18, min_samples=1, metric="precomputed")
        labels = clustering.fit_predict(distance_matrix)

        groups = defaultdict(list)
        for i, label in enumerate(labels):
            groups[label].append(i)

        result = []
        for group in groups.values():
            if len(group) == 1:
                result.append(posts[group[0]])
            else:
                grouped_posts = [posts[i] for i in group]
                summary = EmbeddingsDBSCANGrouper.summarize_posts(grouped_posts)
                result.append(PostGroup(posts=grouped_posts, summary=summary))
        return result

    @staticmethod
    def compute_gemini_embeddings(posts: list[Post]) -> np.ndarray:
        """Compute the embedding for posts using Gemini API.

        :param posts: The list of posts to compute embeddings for.
        :return: The embedding of the post.
        """
        embeddings = []
        for post in posts:
            result = gemini_client.models.embed_content(
                model="text-embedding-004",
                contents=post.body,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
            )
            if not result.embeddings or not result.embeddings[0].values:
                logging.error(
                    f"Failed to compute embedding for post: {post.title}. Generating random embedding."
                )
                length = len(embeddings[0]) if embeddings else 100
                embeddings.append(np.random.rand(length).tolist())
                continue
            embeddings.append(result.embeddings[0].values)
        return np.stack(embeddings)

    @staticmethod
    def summarize_posts(posts: list[Post]) -> str:
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
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite-preview-06-17",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                temperature=0.5,
                top_p=0.5,
            ),
        )
        return response.text or "Failed to summarize posts."
