from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Giveaway


@receiver(post_save, sender=Giveaway)
def update_search_vector_column_on_giveaway(sender, instance, **kwargs):
    if not kwargs.get("update_fields"):
        instance = sender.objects.with_vectors().get(pk=instance.pk)
        instance.search_vector_column = instance.vectors
        instance.save(update_fields=["search_vector_column"])
