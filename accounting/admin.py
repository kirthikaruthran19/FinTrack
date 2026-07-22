from django.contrib import admin
from .models import Category, Transaction, Gst, Ledger

admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Gst)
admin.site.register(Ledger)