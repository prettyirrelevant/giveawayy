# Generated by Django 3.2.7 on 2021-10-05 10:03

from decimal import Decimal

import django.contrib.postgres.indexes
import django.contrib.postgres.search
import django.core.validators
import django.db.models.deletion
import django.db.models.expressions
from django.conf import settings
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        TrigramExtension(),
        migrations.CreateModel(
            name="Giveaway",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("title", models.CharField(max_length=100, verbose_name="title")),
                (
                    "description",
                    models.TextField(blank=True, null=True, verbose_name="description"),
                ),
                (
                    "slug",
                    models.SlugField(
                        editable=False, max_length=120, unique=True, verbose_name="slug"
                    ),
                ),
                (
                    "number_of_participants",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(5),
                            django.core.validators.MaxValueValidator(1000),
                        ],
                        verbose_name="number of participants",
                    ),
                ),
                (
                    "number_of_winners",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(200),
                        ],
                        verbose_name="number of winners",
                    ),
                ),
                (
                    "is_creator_anonymous",
                    models.BooleanField(default=False, verbose_name="is creator anonymous"),
                ),
                ("is_public", models.BooleanField(default=True, verbose_name="is public")),
                (
                    "is_prize_monetary",
                    models.BooleanField(default=False, verbose_name="is prize monetary"),
                ),
                (
                    "is_category_quiz",
                    models.BooleanField(default=False, verbose_name="is category quiz"),
                ),
                (
                    "password",
                    models.CharField(
                        blank=True, max_length=128, null=True, verbose_name="password"
                    ),
                ),
                ("has_winners", models.BooleanField(default=False, verbose_name="has winners")),
                ("paid_winners", models.BooleanField(default=False, verbose_name="paid winners")),
                (
                    "status",
                    models.CharField(
                        choices=[("CREATED", "Created"), ("ACTIVE", "Active"), ("ENDED", "Ended")],
                        default="CREATED",
                        max_length=10,
                        verbose_name="status",
                    ),
                ),
                (
                    "search_vector_column",
                    django.contrib.postgres.search.SearchVectorField(null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("end_at", models.DateTimeField(verbose_name="end at")),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="giveaways",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="QuizCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "choice",
                    models.IntegerField(
                        choices=[
                            (0, "Random"),
                            (21, "Sports"),
                            (12, "Music"),
                            (28, "Vehicles"),
                            (31, "Anime"),
                            (19, "Mathematics"),
                            (15, "Video Games"),
                        ],
                        default=0,
                        verbose_name="quiz choice",
                    ),
                ),
                (
                    "giveaway",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="quiz_category",
                        to="giveaways.giveaway",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "quiz categories",
            },
        ),
        migrations.CreateModel(
            name="Participant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=150, verbose_name="name")),
                ("email", models.EmailField(max_length=254, verbose_name="email address")),
                (
                    "bank_code",
                    models.CharField(
                        choices=[
                            ("044", "Access Bank"),
                            ("063", "Access Bank Diamond"),
                            ("035A", "Alat By Wema"),
                            ("565", "Carbon"),
                            ("023", "Citibank Nigeria"),
                            ("050", "Ecobank Nigeria"),
                            ("50126", "Eyowo"),
                            ("070", "Fidelity Bank"),
                            ("011", "First Bank Of Nigeria"),
                            ("214", "First City Monument Bank"),
                            ("00103", "Globus Bank"),
                            ("100022", "Gomoney"),
                            ("058", "Guaranty Trust Bank"),
                            ("030", "Heritage Bank"),
                            ("301", "Jaiz Bank"),
                            ("082", "Keystone Bank"),
                            ("50211", "Kuda Bank"),
                            ("100002", "Paga"),
                            ("999991", "Palmpay"),
                            ("526", "Parallex Bank"),
                            ("999992", "Paycom"),
                            ("076", "Polaris Bank"),
                            ("101", "Providus Bank"),
                            ("502", "Rand Merchant Bank"),
                            ("125", "Rubies Mfb"),
                            ("221", "Stanbic Ibtc Bank"),
                            ("068", "Standard Chartered Bank"),
                            ("232", "Sterling Bank"),
                            ("100", "Suntrust Bank"),
                            ("102", "Titan Bank"),
                            ("032", "Union Bank Of Nigeria"),
                            ("033", "United Bank For Africa"),
                            ("215", "Unity Bank"),
                            ("566", "Vfd Microfinance Bank Limited"),
                            ("035", "Wema Bank"),
                            ("057", "Zenith Bank"),
                        ],
                        max_length=6,
                        verbose_name="bank code",
                    ),
                ),
                ("account_number", models.CharField(max_length=10, verbose_name="account number")),
                ("is_winner", models.BooleanField(default=False, verbose_name="is_winner")),
                ("is_paid", models.BooleanField(default=False, verbose_name="is paid")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                (
                    "giveaway",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participants",
                        to="giveaways.giveaway",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MonetaryPrize",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=3,
                        max_digits=11,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("1000.000")),
                            django.core.validators.MaxValueValidator(Decimal("10000000.000")),
                        ],
                        verbose_name="amount",
                    ),
                ),
                (
                    "net_amount",
                    models.DecimalField(
                        decimal_places=3, max_digits=11, verbose_name="net amount"
                    ),
                ),
                (
                    "giveaway",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="monetary_prize",
                        to="giveaways.giveaway",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="monetaryprize",
            constraint=models.CheckConstraint(
                check=models.Q(("net_amount__lt", django.db.models.expressions.F("amount"))),
                name="net_amount_lt_amount",
            ),
        ),
        migrations.AddIndex(
            model_name="giveaway",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_vector_column"], name="giveaways_g_search__29c63a_gin"
            ),
        ),
        migrations.AddConstraint(
            model_name="giveaway",
            constraint=models.CheckConstraint(
                check=models.Q(
                    (
                        "number_of_winners__lt",
                        django.db.models.expressions.F("number_of_participants"),
                    )
                ),
                name="compare_winners_to_participants",
            ),
        ),
    ]
