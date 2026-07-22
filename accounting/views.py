import json
from decimal import Decimal
from io import BytesIO
from django.db.models import Sum

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from groq import Groq
from reportlab.pdfgen import canvas

from .forms import TransactionForm
from .models import Category, Gst, Ledger, Transaction
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone


from django.db.models import Q
GST_RATE = Decimal("18.00")

client = Groq(api_key=settings.GROQ_API_KEY)


# ----------------------------
# Add Transaction
# ----------------------------
def add_transaction(request):

    if request.method == "POST":

        form = TransactionForm(request.POST)

        if form.is_valid():

            transaction = form.save()

            # Save GST
            Gst.objects.create(
                transaction=transaction,
                gst_percentage=GST_RATE,
            )

            # Previous Balance
            last_ledger = Ledger.objects.order_by("-id").first()

            previous_balance = (
                last_ledger.current_balance
                if last_ledger
                else Decimal("0.00")
            )

            # Update Balance
            if transaction.type == "Income":
                new_balance = previous_balance + transaction.amount
            else:
                new_balance = previous_balance - transaction.amount

            Ledger.objects.create(
                date=transaction.date,
                transaction=transaction,
                current_balance=new_balance,
            )

            return redirect("add_transaction")

    else:
        form = TransactionForm()

    return render(
        request,
        "accounting/add_transaction.html",
        {
            "form": form,
        },
    )


# ----------------------------
# Categorize Transactions
# ----------------------------
def categorize_transactions(request):

    if request.method == "POST":

        transaction_id = request.POST.get("transaction_id")
        category_id = request.POST.get("category")

        transaction = get_object_or_404(
            Transaction,
            id=transaction_id,
        )

        transaction.category_id = category_id
        transaction.save()

        return redirect("categorize_transactions")

    transactions = Transaction.objects.all()
    categories = Category.objects.all()

    return render(
        request,
        "accounting/categorize_transactions.html",
        {
            "transactions": transactions,
            "categories": categories,
        },
    )


# ----------------------------
# GST Report
# ----------------------------
def generate_gst_report(request):

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("GST Report")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, "GST REPORT")

    y = 760

    total_taxable = Decimal("0.00")
    total_gst = Decimal("0.00")

    transactions = Transaction.objects.all()

    for transaction in transactions:

        gst_amount = transaction.amount * Decimal("0.18")

        total_taxable += transaction.amount
        total_gst += gst_amount

        pdf.setFont("Helvetica", 10)

        pdf.drawString(40, y, str(transaction.date))
        pdf.drawString(110, y, transaction.description[:20])
        pdf.drawString(260, y, str(transaction.amount))
        pdf.drawString(360, y, f"GST: {gst_amount:.2f}")

        y -= 20

        if y < 50:
            pdf.showPage()
            y = 800

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(
        40,
        y - 20,
        f"Total Taxable : {total_taxable:.2f}",
    )

    pdf.drawString(
        40,
        y - 40,
        f"Total GST : {total_gst:.2f}",
    )

    pdf.save()

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename="gst_report.pdf",
    )


# ----------------------------
# GST Bill
# ----------------------------
def generate_gst_bill(request, transaction_id):

    transaction = get_object_or_404(
        Transaction,
        id=transaction_id,
    )

    gst = transaction.amount * Decimal("0.18")
    total = transaction.amount + gst

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("GST Bill")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(200, 800, "GST BILL")

    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, 740, f"Date : {transaction.date}")
    pdf.drawString(50, 710, f"Description : {transaction.description}")
    pdf.drawString(50, 680, f"Amount : {transaction.amount}")
    pdf.drawString(50, 650, f"GST (18%) : {gst:.2f}")
    pdf.drawString(50, 620, f"Total Amount : {total:.2f}")

    pdf.save()

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename="gst_bill.pdf",
    )


# ----------------------------
# AI Predictive Analytics
# ----------------------------
def predictive_analytics(request):

    transactions = Transaction.objects.all()

    history = []

    for transaction in transactions:

        history.append(
            {
                "date": str(transaction.date),
                "type": transaction.type,
                "amount": float(transaction.amount),
                "description": transaction.description,
                "category": (
                    transaction.category.name
                    if transaction.category
                    else "Uncategorized"
                ),
            }
        )

    prompt = f"""
You are a Professional Financial Analyst.

Analyze these accounting transactions.

Transaction History:

{json.dumps(history, indent=4)}

Return ONLY JSON.

{{
    "predictions":[
        "...",
        "..."
    ],

    "insights":[
        "...",
        "..."
    ],

    "recommendations":[
        "...",
        "..."
    ]
}}
"""

    result = {
        "predictions": [],
        "insights": [],
        "recommendations": [],
    }

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],

            temperature=0.4,

            response_format={
                "type": "json_object"
            }

        )

        result = json.loads(
            response.choices[0].message.content
        )

    except Exception as e:

        result["insights"] = [
            f"Error: {str(e)}"
        ]

    return render(

        request,

        "accounting/analytics_report.html",

        {
            "result": result,
            "transactions": transactions,
        },

    )

def dashboard(request):

    total_income = (
        Transaction.objects.filter(type="Income")
        .aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    total_expense = (
        Transaction.objects.filter(type="Expense")
        .aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    balance = total_income - total_expense

    recent_transactions = Transaction.objects.order_by("-date")[:5]

    return render(
        request,
        "accounting/dashboard.html",
        {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "recent_transactions": recent_transactions,
        },
    )

def transaction_history(request):

    transactions = Transaction.objects.all().order_by("-date")

    search = request.GET.get("search")

    category = request.GET.get("category")

    transaction_type = request.GET.get("type")

    if search:
        transactions = transactions.filter(
            Q(description__icontains=search)
        )

    if category:
        transactions = transactions.filter(
            category__id=category
        )

    if transaction_type:
        transactions = transactions.filter(
            type=transaction_type
        )

    categories = Category.objects.all()

    return render(
        request,
        "accounting/transaction_history.html",
        {
            "transactions": transactions,
            "categories": categories,
        },
    )

def dashboard(request):
    # -----------------------------
    # Dashboard Cards
    # -----------------------------
    total_income = (
        Transaction.objects.filter(type="Income")
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    total_expense = (
        Transaction.objects.filter(type="Expense")
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    balance = total_income - total_expense

    total_transactions = Transaction.objects.count()

    # -----------------------------
    # Monthly Income vs Expense
    # -----------------------------
    monthly_data = (
        Transaction.objects
        .annotate(month=TruncMonth("date"))
        .values("month", "type")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    monthly_labels = []
    monthly_income = []
    monthly_expense = []

    months = {}

    for item in monthly_data:
        month = item["month"].strftime("%b")

        if month not in months:
            months[month] = {
                "Income": 0,
                "Expense": 0,
            }

        months[month][item["type"]] = float(item["total"])

    for month, values in months.items():
        monthly_labels.append(month)
        monthly_income.append(values["Income"])
        monthly_expense.append(values["Expense"])

    # -----------------------------
    # Expense by Category
    # -----------------------------
    expense_categories = (
        Transaction.objects.filter(type="Expense")
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    category_labels = [
        item["category__name"] or "Uncategorized"
        for item in expense_categories
    ]

    category_amounts = [
        float(item["total"])
        for item in expense_categories
    ]

    # -----------------------------
    # Balance Trend
    # -----------------------------
    trend_transactions = (
        Transaction.objects.order_by("date")
    )

    trend_labels = []
    trend_balance = []

    running_balance = 0

    for t in trend_transactions:

        if t.type == "Income":
            running_balance += float(t.amount)
        else:
            running_balance -= float(t.amount)

        trend_labels.append(
            t.date.strftime("%d %b")
        )

        trend_balance.append(running_balance)

    # -----------------------------
    # Recent Activity
    # -----------------------------
    recent_transactions = (
        Transaction.objects.order_by("-date")[:8]
    )

    # -----------------------------
    # Monthly Summary
    # -----------------------------
    today = timezone.now()

    month_income = (
        Transaction.objects.filter(
            type="Income",
            date__month=today.month,
            date__year=today.year,
        ).aggregate(total=Sum("amount"))["total"] or 0
    )

    month_expense = (
        Transaction.objects.filter(
            type="Expense",
            date__month=today.month,
            date__year=today.year,
        ).aggregate(total=Sum("amount"))["total"] or 0
    )

    month_savings = month_income - month_expense

    ai_score = 95

    context = {

        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "total_transactions": total_transactions,

        "monthly_labels": monthly_labels,
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,

        "category_labels": category_labels,
        "category_amounts": category_amounts,

        "trend_labels": trend_labels,
        "trend_balance": trend_balance,

        "recent_transactions": recent_transactions,

        "month_income": month_income,
        "month_expense": month_expense,
        "month_savings": month_savings,

        "ai_score": ai_score,
    }

    return render(
        request,
        "dashboard.html",
        context,
    )