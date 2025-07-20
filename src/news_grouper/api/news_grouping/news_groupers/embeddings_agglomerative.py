from collections import defaultdict

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances

from news_grouper.api.common.models import Post
from news_grouper.api.news_grouping.news_groupers.abstract_grouper import NewsGrouper


class EmbeddingsAgglomerativeGrouper(NewsGrouper):
    """Grouper that uses embeddings and Agglomerative Clustering to group posts."""

    name = "Embeddings Agglomerative"
    description = (
        "Better for grouping same news. Converts posts into embeddings using Gemini API, "
        "groups them using DBSCAN and writes summaries using Gemini API."
    )

    @classmethod
    def _get_groups(cls, posts: list[Post]) -> dict[int, list[int]]:
        """ "Abstract method to get groups of posts.

        :param posts: The list of posts to group.
        :return: A dictionary where keys are group labels and values are lists of posts indices.
        """
        embeddings = np.stack(
            [NewsGrouper.gemini_client.compute_embedding(post) for post in posts]
        )
        distance_matrix = cosine_distances(embeddings)
        clustering = AgglomerativeClustering(
            n_clusters=None,  # type: ignore
            distance_threshold=0.17,
            linkage="complete",
            metric="precomputed",
        )
        labels = clustering.fit_predict(distance_matrix)

        groups = defaultdict(list)
        for i, label in enumerate(labels):
            groups[label].append(i)
        return groups
