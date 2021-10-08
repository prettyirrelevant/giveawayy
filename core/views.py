from typing import Any, Dict

from django.views import generic
from giveaways.models import Giveaway


class IndexView(generic.TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Giveaway"
        context["giveaways"] = (
            Giveaway.objects.select_related("monetary_prize", "creator", "quiz_category")
            .filter(is_public=True)
            .order_by("-created_at")
        )

        return context
