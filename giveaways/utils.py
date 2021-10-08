import datetime
import html
import random
from operator import itemgetter
from typing import Tuple
from uuid import uuid4

import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone

from .enums import DurationType, GiveawayCategory, QuizChoices
from .models import Giveaway, MonetaryPrize, QuizCategory


def generate_hex() -> str:
    """Utility function that generates random hex string"""
    return "%0x" % random.getrandbits(25)


def show_quiz_step_if_category(wizard) -> bool:
    """Utility function that adds `CreateGiveawayQuizCategoryForm` if `category` is QUIZ"""

    cleaned_data = wizard.get_cleaned_data_for_step("basic") or dict()

    return cleaned_data.get("category") == GiveawayCategory.QUIZ


def show_add_password_if_not_public(wizard) -> bool:
    """Utility function that adds `CreateGiveawayAddPasswordForm` if `is_public` is False"""
    cleaned_data = wizard.get_cleaned_data_for_step("basic") or dict()

    return not cleaned_data.get("is_public")


def get_datetime_from_duration_params(type: str, length: int) -> datetime.datetime:
    """Utility that generates `datetime.datetime` object from duration length and type."""

    dt = None
    if type == DurationType.MINUTES:
        dt = timezone.now() + datetime.timedelta(minutes=length)

    elif type == DurationType.HOURS:
        dt = timezone.now() + datetime.timedelta(hours=length)

    elif type == DurationType.DAYS:
        dt = timezone.now() + datetime.timedelta(days=length)

    return dt


@transaction.atomic
def create_new_giveaway(user, forms) -> Giveaway:
    """A function that creates a new `Giveaway` model instance and other related model instances."""

    new_giveaway = None

    basic_form = forms["basic"].cleaned_data

    giveaway_category = basic_form.pop("category")
    is_public = basic_form.get("is_public")

    end_at = get_datetime_from_duration_params(
        basic_form.pop("duration_type"), basic_form.pop("duration_length")
    )

    monetary_form = forms["monetary"].cleaned_data

    password = None
    if not is_public:
        security_form = forms["security"].cleaned_data
        password = make_password(security_form.get("password"))

    if giveaway_category == GiveawayCategory.NONE:
        new_giveaway = Giveaway.objects.create(
            **basic_form,
            is_category_quiz=False,
            is_prize_monetary=True,
            creator=user,
            password=password,
            end_at=end_at,
        )
        new_monetary_prize = MonetaryPrize.objects.create(giveaway=new_giveaway, **monetary_form)
    elif giveaway_category == GiveawayCategory.QUIZ:
        quiz_form = forms["quiz"].cleaned_data

        new_giveaway = Giveaway.objects.create(
            **basic_form,
            is_category_quiz=True,
            is_prize_monetary=True,
            creator=user,
            password=password,
            end_at=end_at,
        )
        new_monetary_prize = MonetaryPrize.objects.create(giveaway=new_giveaway, **monetary_form)
        new_quiz_category = QuizCategory.objects.create(giveaway=new_giveaway, **quiz_form)

    return new_giveaway


def get_quiz_url(quiz_choice: str) -> str:
    """Utility function that returns the API endpoint to get quiz based on choice of quiz."""
    if quiz_choice == QuizChoices.RANDOM:
        quiz_url = "https://opentdb.com/api.php?amount=4&difficulty=easy&type=multiple"
    else:
        quiz_url = f"https://opentdb.com/api.php?amount=4&category={quiz_choice}&difficulty=easy&type=multiple"

    return quiz_url


def format_questions_and_answers(data) -> Tuple[dict, dict]:
    """Utility function that formats quiz questions and its answers."""
    quiz_id = str(uuid4())
    final_questions = {"id": quiz_id, "questions": []}
    final_answers = {"quiz_id": quiz_id, "answers": []}

    for question in data:
        question_id = str(uuid4())
        q = html.unescape(question["question"])

        options = html.unescape(question["incorrect_answers"])
        correct_answer = html.unescape(question["correct_answer"])
        options.append(correct_answer)

        final_answers["answers"].append({"question_id": question_id, "answer": correct_answer})
        final_questions["questions"].append({"id": question_id, "question": q, "options": options})

    return final_questions, final_answers


def calculate_quiz_score(attempts, answers) -> float:
    """Utility function that calculates the score of a taken quiz."""
    score = 0

    cleaned_attempts = [
        {"question_id": key.split("=")[-1], "answer": value} for key, value in attempts.items()
    ]
    sorted_attempts = sorted(cleaned_attempts, key=itemgetter("question_id"))
    sorted_answers = sorted(answers, key=itemgetter("question_id"))

    for item in zip(sorted_answers, sorted_attempts):
        if item[0]["answer"] == item[1]["answer"]:
            score += 10
    return (score / 40) * 100


def verify_nuban_and_bank(nuban: str, bank_code: str) -> Tuple[bool, str]:
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    params = {"account_number": nuban, "bank_code": bank_code}

    response = requests.get(
        f"{settings.PAYSTACK_URL}/bank/resolve", headers=headers, params=params
    )
    response_data = response.json()

    if response_data["status"]:
        return True, response_data["data"]["account_name"]

    return False, ""
