from django.urls import path

from .views import (
    add_transaction,
    categorize_transactions,
    generate_gst_bill,
    generate_gst_report,
    predictive_analytics,
    dashboard,
    transaction_history,
)

urlpatterns = [
    path("", add_transaction, name="add_transaction"),

    path(
        "categorize/",
        categorize_transactions,
        name="categorize_transactions",
    ),

    path(
        "gst-report/",
        generate_gst_report,
        name="gst_report",
    ),

    path(
        "gst-bill/<int:transaction_id>/",
        generate_gst_bill,
        name="gst_bill",
    ),

    path(
        "analytics/",
        predictive_analytics,
        name="analytics",
    ),
    path("dashboard/", dashboard, name="dashboard"),
    path(
    "transactions/",
    transaction_history,
    name="transaction_history",
),
]