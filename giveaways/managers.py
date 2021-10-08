from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db import models


class GiveawayManager(models.Manager):
    def search(self, query):
        search_vectors = (
            SearchVector("title", weight="A")
            + SearchVector("creator__first_name", weight="B")
            + SearchVector("creator__last_name", weight="B")
            + SearchVector("description", weight="C")
        )

        search_query = SearchQuery(query)
        search_rank = SearchRank(search_vectors, search_query)

        similarity = (
            TrigramSimilarity("creator__first_name", query)
            + TrigramSimilarity("creator__last_name", query)
            + TrigramSimilarity("title", query)
            + TrigramSimilarity("description", query)
        )

        queryset = (
            self.get_queryset()
            .filter(search_vector_column=search_query)
            .annotate(rank=search_rank + similarity)
            .order_by("-rank")
        )
        return queryset

    def with_vectors(self):
        vectors = (
            SearchVector("title", weight="A")
            + SearchVector("creator__first_name", weight="B")
            + SearchVector("creator__last_name", weight="B")
            + SearchVector("description", weight="C")
        )

        return self.get_queryset().annotate(vectors=vectors)
