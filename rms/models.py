from django.db import models

# Create your models here.


class DailySummary(models.Model):
    """Agent End-of-Day (EOD) closure for financial reconciliation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    closing_date = models.DateTimeField(db_index=True)
    sales_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_closures",
    )

    total_sales_count = models.IntegerField(default=0)
    total_revenue = MoneyField(max_digits=15, decimal_places=2, default_currency="TZS")
    total_cash_sales = MoneyField(
        max_digits=15, decimal_places=2, default_currency="TZS"
    )
    net_cash_settlement = MoneyField(
        max_digits=15, decimal_places=2, default_currency="TZS"
    )
    # Breakdown JSON includes: {
    #     'expenses': [{'category': 'Fuel', 'amount': 5000}],
    #     'cash_denominations': {'10k_notes': 5, '5k_notes': 10},
    #     'notes': "Slightly late closure due to high traffic"
    # }
    breakdown = models.JSONField(_("Financial Breakdown"), default=dict, blank=True)

    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="closures_managed",
    )
    closed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "daily_summary"
        unique_together = ("closing_date", "sales_agent")

    def get_log_message(self, old_data=None):
        if old_data:
            return (
                f"Updated Daily Summary for Agent '{self.sales_agent}' "
                f"from: {old_data} to: total sales {self.total_sales_count}, revenue {self.total_revenue}, cash {self.total_cash_sales}"
            )
        return (
            f"Recorded Daily Summary for Agent '{self.sales_agent}' "
            f"date {self.closing_date}, total sales {self.total_sales_count}, revenue {self.total_revenue}, cash {self.total_cash_sales}"
        )
