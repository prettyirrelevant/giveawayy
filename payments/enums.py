from django.db.models import TextChoices


class TransactionStatus(TextChoices):
    INITIATED = "INITIATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    REVERSED = "REVERSED"
    FAILED = "FAILED"
