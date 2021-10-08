from decimal import Decimal

from django import forms
from django.contrib.auth.hashers import check_password

from giveaways.utils import verify_nuban_and_bank

from .enums import Banks, DurationType, GiveawayCategory, QuizChoices


class CreateGiveawayBasicInformationForm(forms.Form):
    title = forms.CharField(
        max_length=100,
        min_length=4,
        label="Title",
        help_text="A meaningful name to call the giveaway.",
    )

    description = forms.CharField(
        widget=forms.Textarea(),
        help_text="Help people understand why you're doing this giveaway",
        label="Description",
        required=False,
    )

    category = forms.ChoiceField(choices=GiveawayCategory.choices, label="Category")

    number_of_participants = forms.IntegerField(
        max_value=1000, min_value=5, label="Number of Participants"
    )
    number_of_winners = forms.IntegerField(max_value=200, min_value=1, label="Number of Winners")

    duration_length = forms.IntegerField(min_value=1, label="Duration Length")
    duration_type = forms.ChoiceField(choices=DurationType.choices, label="Duration Type")

    is_creator_anonymous = forms.BooleanField(label="Make Creator Anonymous", required=False)
    is_public = forms.BooleanField(label="Make Public", required=False)

    def clean(self):
        cleaned_data = super().clean()

        duration_length = cleaned_data.get("duration_length")
        duration_type = cleaned_data.get("duration_type")

        if duration_type == DurationType.MINUTES:
            if duration_length < 15:
                self.add_error("duration_length", "Giveaways must at least span 15 minutes.")
            elif duration_length > 10080:
                self.add_error("duration_length", "Giveaways cannot span more than a week.")

        elif duration_type == DurationType.HOURS:
            if duration_length > 168:
                self.add_error("duration_length", "Giveaways cannot span more than a week.")

        elif duration_type == DurationType.DAYS:
            if duration_length > 7:
                self.add_error("duration_length", "Giveaways cannot span more than a week.")


class CreateGiveawayAddPasswordForm(forms.Form):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(),
        min_length=2,
        max_length=6,
        help_text="A password to key your giveaway safe from intruders. Min length of 2 & Max length of 6",
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(),
        min_length=2,
        max_length=6,
    )

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get("password")
        confirm_pw = cleaned_data.get("confirm_password")

        if pw != confirm_pw:
            self.add_error("password", "")
            self.add_error("confirm_password", "Passwords do not match!")


class CreateGiveawayMonetaryPrizeForm(forms.Form):
    amount = forms.DecimalField(
        label="Amount",
        max_digits=11,
        decimal_places=3,
        min_value=Decimal("1000.000"),
        max_value=Decimal("10000000.000"),
        widget=forms.NumberInput(attrs={"step": 500, "min": 1000}),
    )


class CreateGiveawayQuizCategoryForm(forms.Form):
    choice = forms.ChoiceField(label="Quiz Choice", choices=QuizChoices.choices)


class PrivateGiveawayEntryForm(forms.Form):
    password = forms.CharField(
        max_length=6, min_length=2, label="Password", widget=forms.PasswordInput()
    )

    def __init__(self, *args, **kwargs):
        self.giveaway = kwargs.pop("giveaway")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")

        if not check_password(password, self.giveaway.password):
            self.add_error("password", "Invalid passcode. Please check and try again.")


class JoinGiveawayForm(forms.Form):
    name = forms.CharField(
        label="Name",
        max_length=150,
        required=False,
        disabled=True,
        help_text="Don't fret. The name of the account provided will be used.",
    )
    email = forms.EmailField(
        label="Email Address",
        required=True,
        help_text="This is used to notify you when you win a giveaway.",
    )
    account_number = forms.CharField(max_length=10, min_length=10, label="Account Number")
    bank = forms.ChoiceField(choices=Banks.choices, label="Bank")

    def clean(self):
        cleaned_data = super().clean()
        nuban, bank_code = cleaned_data.get("account_number"), cleaned_data.get("bank")

        status, account_name = verify_nuban_and_bank(nuban, bank_code)

        if not status:
            self.add_error(None, "Account number does not exist for the specified bank.")
        else:
            cleaned_data["name"] = account_name
            cleaned_data["bank_code"] = cleaned_data.pop("bank")

            return cleaned_data


class JoinGiveawayQuizForm(forms.Form):
    timer = forms.CharField(label="timer", widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        questions = kwargs.pop("questions")
        super().__init__(*args, **kwargs)

        self.fields["quiz_id"] = forms.CharField(
            label="quiz_id", widget=forms.HiddenInput, initial=questions["id"]
        )
        self.fields["timer"] = forms.CharField(
            label="quiz_id", widget=forms.HiddenInput, initial=20
        )

        for index, question in enumerate(questions["questions"], start=1):
            self.fields[f'question={question["id"]}'] = forms.ChoiceField(
                label=f'{index}. {question["question"]}',
                required=False,
                choices=[(option, option) for option in question["options"]],
                widget=forms.RadioSelect,
            )
