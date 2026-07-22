from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
class Transaction(models.Model):

    TRANSACTION_TYPES = [
        ("Income", "Income"),
        ("Expense", "Expense"),
    ]

    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.type} - {self.amount}"

class Gst(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="gst_records"
    )

    gst_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.gst_percentage}% GST"


class Ledger(models.Model):
    date = models.DateField()

    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE
    )

    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.date} - {self.current_balance}"        