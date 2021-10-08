from django.db import models
from django.utils.translation import gettext_lazy as _
from giveaways.models import Giveaway

from payments.enums import TransactionStatus


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, db_index=True)
    giveaway = models.ForeignKey(
        Giveaway,
        related_name="transactions",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )

    narration = models.CharField(_("narration"), max_length=100, blank=False, null=False)
    amount = models.DecimalField(
        _("amount"), max_digits=11, decimal_places=3, blank=False, null=False
    )
    status = models.CharField(
        _("transaction status"),
        choices=TransactionStatus.choices,
        default=TransactionStatus.INITIATED,
        max_length=15,
    )
    gateway_response = models.CharField(
        _("gateway response"), max_length=256, blank=True, null=True
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
