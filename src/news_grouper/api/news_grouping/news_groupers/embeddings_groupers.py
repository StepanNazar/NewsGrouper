import itertools
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Iterable

import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances

from news_grouper.api.common.models import Post
from news_grouper.api.news_grouping.news_groupers.abstract_grouper import NewsGrouper
from news_grouper.api.news_grouping.news_groupers.gemini import GeminiClient


class EmbeddingsGrouper(NewsGrouper):
    """Abstract base class for groupers that use embeddings."""

    @classmethod
    def _get_groups(
        cls, posts: list[Post], gemini_client: GeminiClient
    ) -> Iterable[list[Post]]:
        """Group posts based on their embeddings.

        :param posts: The list of posts to group.
        :param gemini_client: The Gemini client to use for API calls.
        :return: A list of groups, where each group is a list of posts.
        """
        embeddings, posts_with_failed_embeddings, posts_with_successful_embeddings = (
            cls._computes_embeddings(posts, gemini_client)
        )
        labels = cls._cluster_embeddings(np.stack(embeddings))
        groups = cls._labels_to_groups(labels, posts_with_successful_embeddings)
        return itertools.chain(
            groups.values(), [[post] for post in posts_with_failed_embeddings]
        )

    @classmethod
    def _computes_embeddings(
        cls, posts: list[Post], gemini_client: GeminiClient
    ) -> tuple[list[list[float]], list[Post], list[Post]]:
        """Compute embeddings for a list of posts.
        :param posts: The list of posts to compute embeddings for.
        :param gemini_client: The Gemini client to use for API calls.
        :return: A tuple containing:
            - A list of embeddings (list of floats).
            - A list of posts for which embedding computation failed.
            - A list of posts for which embedding computation succeeded. Here ith post corresponds to ith embedding.
        """
        embeddings = []
        posts_with_failed_embeddings = []
        posts_with_successful_embeddings = []
        for post in posts:
            embedding = gemini_client.compute_embedding(post)
            if embedding is not None:
                embeddings.append(embedding)
                posts_with_successful_embeddings.append(post)
            else:
                posts_with_failed_embeddings.append(post)
        return (
            embeddings,
            posts_with_failed_embeddings,
            posts_with_successful_embeddings,
        )

    @classmethod
    def _labels_to_groups(
        cls, labels: np.ndarray, posts: list[Post]
    ) -> dict[int, list[Post]]:
        """Convert cluster labels to groups of posts.
        :param labels: Array where ith element is the cluster label for the ith embedding.
        :param posts: List of posts corresponding to the embeddings.
        :return: A dictionary where keys are cluster labels and values are lists of posts in that cluster.
        """
        groups = defaultdict(list)
        for i, label in enumerate(labels):
            groups[label].append(posts[i])
        return groups

    @classmethod
    @abstractmethod
    def _cluster_embeddings(cls, embeddings: np.ndarray) -> np.ndarray:
        """Abstract method to cluster embeddings.

        :param embeddings: Array of embeddings to cluster.
        :return: Array where ith element is the cluster label for the ith embedding.
        """


class EmbeddingsAgglomerativeGrouper(EmbeddingsGrouper):
    """Grouper that uses embeddings and Agglomerative Clustering to group posts."""

    name = "Embeddings Agglomerative"
    description = (
        "Better for grouping same news. Converts posts into embeddings using Gemini API, "
        "groups them using DBSCAN and writes summaries using Gemini API."
    )

    @classmethod
    def _cluster_embeddings(cls, embeddings: np.ndarray) -> np.ndarray:
        """Cluster embeddings using Agglomerative Clustering.

        :param embeddings: Array of embeddings to cluster.
        :return: Array where ith element is the cluster label for the ith embedding.
        """
        distance_matrix = cosine_distances(embeddings)
        clustering = AgglomerativeClustering(
            n_clusters=None,  # type: ignore
            distance_threshold=0.17,
            linkage="complete",
            metric="precomputed",
        )
        return clustering.fit_predict(distance_matrix)


class EmbeddingsDBSCANGrouper(EmbeddingsGrouper):
    """Grouper that uses embeddings and DBSCAN to group posts."""

    name = "Embeddings DBSCAN"
    description = (
        "Better for grouping related news. Converts posts into embeddings using Gemini API, groups"
        "them using DBSCAN and writes summaries using Gemini API."
    )

    @classmethod
    def _cluster_embeddings(cls, embeddings: np.ndarray) -> np.ndarray:
        """Cluster embeddings using DBSCAN.

        :param embeddings: Array of embeddings to cluster.
        :return: Array where ith element is the cluster label for the ith embedding.
        """
        distance_matrix = cosine_distances(embeddings)
        clustering = DBSCAN(eps=0.17, min_samples=1, metric="precomputed")
        return clustering.fit_predict(distance_matrix)
