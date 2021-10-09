from django.views import generic
from giveaways.models import Giveaway


class IndexView(generic.ListView):
    template_name = "index.html"
    queryset = (
        Giveaway.objects.select_related("monetary_prize", "creator", "quiz_category")
        .prefetch_related("participants")
        .filter(is_public=True)
        .order_by("-created_at")
    )
    context_object_name = "giveaways"
    paginate_by = 4

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Giveaway"

        return context
