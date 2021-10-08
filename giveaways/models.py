from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.constraints import CheckConstraint
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .enums import Banks, GiveawayStatus, QuizChoices
from .managers import GiveawayManager


class Giveaway(models.Model):
    title = models.CharField(_("title"), max_length=100, blank=False, null=False)
    description = models.TextField(_("description"), blank=True, null=True)
    slug = models.SlugField(
        _("slug"),
        max_length=120,
        unique=True,
        db_index=True,
        editable=False,
        blank=False,
        null=False,
    )
    number_of_participants = models.PositiveIntegerField(
        _("number of participants"),
        blank=False,
        null=False,
        validators=[MinValueValidator(5), MaxValueValidator(1000)],
    )
    number_of_winners = models.PositiveIntegerField(
        _("number of winners"),
        blank=False,
        null=False,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
    )
    creator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="giveaways"
    )
    is_creator_anonymous = models.BooleanField(_("is creator anonymous"), default=False)
    is_public = models.BooleanField(_("is public"), default=True)

    is_prize_monetary = models.BooleanField(_("is prize monetary"), default=False)
    is_category_quiz = models.BooleanField(_("is category quiz"), default=False)

    password = models.CharField(_("password"), max_length=128, blank=True, null=True)

    has_winners = models.BooleanField(_("has winners"), default=False)
    paid_winners = models.BooleanField(_("paid winners"), default=False)

    status = models.CharField(
        _("status"), max_length=10, choices=GiveawayStatus.choices, default=GiveawayStatus.CREATED
    )

    search_vector_column = SearchVectorField(null=True)

    objects = GiveawayManager()

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    end_at = models.DateTimeField(_("end at"), blank=False, null=False)

    def save(self, *args, **kwargs):
        from .utils import generate_hex

        if not self.pk:
            self.slug = slugify(self.title) + "-" + generate_hex()

        super().save(*args, **kwargs)

    class Meta:
        indexes = [GinIndex(fields=["search_vector_column"])]

        constraints = [
            CheckConstraint(
                check=Q(number_of_winners__lt=F("number_of_participants")),
                name="compare_winners_to_participants",
            )
        ]


class MonetaryPrize(models.Model):
    giveaway = models.OneToOneField(
        Giveaway, on_delete=models.CASCADE, related_name="monetary_prize"
    )

    amount = models.DecimalField(
        _("amount"),
        max_digits=11,
        decimal_places=3,
        blank=False,
        null=False,
        validators=[
            MinValueValidator(Decimal("1000.000")),
            MaxValueValidator(Decimal("10000000.000")),
        ],
    )

    net_amount = models.DecimalField(
        _("net amount"),
        max_digits=11,
        decimal_places=3,
        blank=False,
        null=False,
    )

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(net_amount__lt=F("amount")),
                name="net_amount_lt_amount",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            net_amount = self.amount * Decimal("0.96")
            self.net_amount = net_amount.quantize(Decimal(".01"))

        super().save(*args, **kwargs)


class QuizCategory(models.Model):
    giveaway = models.OneToOneField(
        Giveaway, on_delete=models.CASCADE, related_name="quiz_category"
    )

    choice = models.IntegerField(
        _("quiz choice"), choices=QuizChoices.choices, default=QuizChoices.RANDOM
    )

    class Meta:
        verbose_name_plural = "quiz categories"


class Participant(models.Model):
    giveaway = models.ForeignKey(Giveaway, on_delete=models.CASCADE, related_name="participants")

    name = models.CharField(_("name"), max_length=150, blank=False, null=False)
    email = models.EmailField(_("email address"), blank=False, null=False)

    bank_code = models.CharField(
        _("bank code"), choices=Banks.choices, max_length=6, null=False, blank=False
    )
    account_number = models.CharField(_("account number"), max_length=10, blank=False, null=False)

    is_eligible = models.BooleanField(_("is eligible"), default=False)

    is_winner = models.BooleanField(_("is_winner"), default=False)
    is_paid = models.BooleanField(_("is paid"), default=False)

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
