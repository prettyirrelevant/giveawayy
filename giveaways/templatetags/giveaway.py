from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import format_html
from payments.enums import TransactionStatus

from ..enums import GiveawayStatus

register = template.Library()


@register.filter
@stringfilter
def colorize_giveaway_status(value: str):
    if value == GiveawayStatus.CREATED:
        return format_html(f'<span class="badge bg-primary p-2">{value}</span>')
    elif value == GiveawayStatus.ACTIVE:
        return format_html(f'<span class="badge bg-success">{value}</span>')
    elif value == GiveawayStatus.ENDED:
        return format_html(f'<span class="badge bg-secondary">{value}</span>')


@register.filter
def colorize_giveaway_visibility(value: bool):
    if value:
        return format_html(
            '<span class="position-absolute top-0 start-100 translate-middle badge bg-secondary">public<span class="visually-hidden">status</span></span>'
        )
    else:
        return format_html(
            '<span class="position-absolute top-0 start-100 translate-middle badge bg-secondary">private<span class="visually-hidden">status</span></span>'
        )


@register.filter
def colorize_giveaway_contains_quiz(value: bool):
    if value:
        return format_html('<span class="badge bg-info p-2">CONTAINS QUIZ</span>')

    else:
        return format_html("")


@register.filter
def colorize_giveaway_eligibility_status(value: bool):
    if value:
        return format_html(f'<span class="badge bg-success p-2">{value}</span>')

    else:
        return format_html(f'<span class="badge bg-danger p-2">{value}</span>')


@register.filter
def colorize_giveaway_transaction_status(value: bool):
    if value == TransactionStatus.INITIATED:
        return format_html(f'<span class="badge bg-secondary p-2">{value}</span>')
    elif value == TransactionStatus.PENDING:
        return format_html(f'<span class="badge bg-warning p-2">{value}</span>')
    elif value == TransactionStatus.SUCCESS:
        return format_html(f'<span class="badge bg-success p-2">{value}</span>')
    elif value == TransactionStatus.FAILED:
        return format_html(f'<span class="badge bg-danger p-2">{value}</span>')
