from typing import Any, Dict

from django.views import generic


class IndexView(generic.TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = "Giveaway"

        return context
