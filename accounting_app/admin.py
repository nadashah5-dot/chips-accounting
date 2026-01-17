from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Account, AccountingPeriod, JournalEntry, JournalLine,
    Customer, Supplier, SalesInvoice, PurchaseInvoice,
    AccountingConfig, DocumentSequence, OpeningBalance, Payment
)

# ==========================
# Helpers
# ==========================
def _period_for_date_or_period(date_obj, period_obj=None):
    if period_obj:
        return period_obj
    if date_obj:
        return AccountingPeriod.get_for_date(date_obj)
    return None

def _is_closed_for_obj(date_obj, period_obj=None) -> bool:
    p = _period_for_date_or_period(date_obj, period_obj)
    return bool(p and p.is_closed)


# =========================
# Accounts
# =========================
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "parent", "account_type", "normal_balance")
    list_filter = ("account_type", "normal_balance")
    search_fields = ("code", "name")
    ordering = ("code",)


# =========================
# Periods
# =========================
@admin.register(AccountingPeriod)
class AccountingPeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_closed")
    list_filter = ("is_closed",)
    search_fields = ("name",)
    ordering = ("-start_date",)


# =========================
# Journal (inline lines)
# =========================
class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 0
    fields = ("account", "debit", "credit", "note")
    autocomplete_fields = ("account",)

    def has_change_permission(self, request, obj=None):
        if obj and _is_closed_for_obj(obj.date, obj.period):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and _is_closed_for_obj(obj.date, obj.period):
            return False
        return super().has_delete_permission(request, obj)


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    inlines = [JournalLineInline]

    list_display = (
        "serial_number", "date", "period", "reference",
        "description_short", "is_reversed", "reversed_entry_link",
        "pdf_link",
    )
    list_filter = ("period", "is_reversed", "date")
    search_fields = ("serial_number", "reference", "description")
    ordering = ("-date", "-id")
    autocomplete_fields = ("period",)

    fieldsets = (
        ("بيانات القيد", {"fields": ("serial_number", "date", "period", "reference", "description")}),
        ("العكس", {"fields": ("is_reversed", "reversed_entry")}),
        ("نظام", {"fields": ("created_at", "created_by")}),
    )

    readonly_fields = ("serial_number", "created_at", "created_by", "is_reversed", "reversed_entry")

    def description_short(self, obj):
        txt = obj.description or ""
        return txt[:60] + ("..." if len(txt) > 60 else "")
    description_short.short_description = "البيان"

    def reversed_entry_link(self, obj):
        if obj.reversed_entry_id:
            url = f"/admin/accounting_app/journalentry/{obj.reversed_entry_id}/change/"
            label = obj.reversed_entry.serial_number or obj.reversed_entry_id
            return format_html('<a href="{}">{} ↗</a>', url, label)
        return "-"
    reversed_entry_link.short_description = "القيد العكسي"

    def pdf_link(self, obj):
        url = f"/account/journal/{obj.id}/export/pdf/"
        return format_html('<a class="button" href="{}" target="_blank">PDF</a>', url)
    pdf_link.short_description = "PDF"

    def has_change_permission(self, request, obj=None):
        if obj and _is_closed_for_obj(obj.date, obj.period):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and _is_closed_for_obj(obj.date, obj.period):
            return False
        return super().has_delete_permission(request, obj)


@admin.register(JournalLine)
class JournalLineAdmin(admin.ModelAdmin):
    list_display = ("entry", "account", "debit", "credit", "note")
    list_filter = ("account",)
    search_fields = ("note", "entry__serial_number", "entry__reference")
    autocomplete_fields = ("entry", "account")

    def has_change_permission(self, request, obj=None):
        if obj and obj.entry_id and _is_closed_for_obj(obj.entry.date, obj.entry.period):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.entry_id and _is_closed_for_obj(obj.entry.date, obj.entry.period):
            return False
        return super().has_delete_permission(request, obj)


# =========================
# Customers / Suppliers
# =========================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "contact")
    search_fields = ("name", "contact")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact")
    search_fields = ("name", "contact")


# =========================
# Invoices
# =========================
@admin.register(SalesInvoice)
class SalesInvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer", "date", "total", "journal_entry_link")
    list_filter = ("date", "customer")
    search_fields = ("invoice_number", "customer__name")
    ordering = ("-date", "-id")
    autocomplete_fields = ("customer",)

    def journal_entry_link(self, obj):
        if obj.journal_entry_id:
            url = f"/admin/accounting_app/journalentry/{obj.journal_entry_id}/change/"
            label = obj.journal_entry.serial_number or obj.journal_entry_id
            return format_html('<a href="{}">{} ↗</a>', url, label)
        return "-"
    journal_entry_link.short_description = "القيد"

    def has_change_permission(self, request, obj=None):
        if obj:
            if obj.journal_entry_id:
                return False
            if _is_closed_for_obj(obj.date, None):
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj:
            if obj.journal_entry_id:
                return False
            if _is_closed_for_obj(obj.date, None):
                return False
        return super().has_delete_permission(request, obj)


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "supplier", "date", "total", "journal_entry_link")
    list_filter = ("date", "supplier")
    search_fields = ("invoice_number", "supplier__name")
    ordering = ("-date", "-id")
    autocomplete_fields = ("supplier",)

    def journal_entry_link(self, obj):
        if obj.journal_entry_id:
            url = f"/admin/accounting_app/journalentry/{obj.journal_entry_id}/change/"
            label = obj.journal_entry.serial_number or obj.journal_entry_id
            return format_html('<a href="{}">{} ↗</a>', url, label)
        return "-"
    journal_entry_link.short_description = "القيد"

    def has_change_permission(self, request, obj=None):
        if obj:
            if obj.journal_entry_id:
                return False
            if _is_closed_for_obj(obj.date, None):
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj:
            if obj.journal_entry_id:
                return False
            if _is_closed_for_obj(obj.date, None):
                return False
        return super().has_delete_permission(request, obj)


# =========================
# Config + Sequences
# =========================
@admin.register(AccountingConfig)
class AccountingConfigAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ar_account",
        "ap_account",
        "sales_account",
        "purchases_account",
        "retained_earnings_account",
    )
    autocomplete_fields = (
        "ar_account",
        "ap_account",
        "sales_account",
        "purchases_account",
        "retained_earnings_account",
    )


@admin.register(DocumentSequence)
class DocumentSequenceAdmin(admin.ModelAdmin):
    list_display = ("doc_type", "period", "last_number")
    list_filter = ("doc_type", "period")
    ordering = ("doc_type", "period")


# =========================
# OpeningBalance + Payment (FIXED)
# =========================
@admin.register(OpeningBalance)
class OpeningBalanceAdmin(admin.ModelAdmin):
    # OpeningBalance عندك: debit/credit مش amount
    list_display = ("account", "period", "debit", "credit", "note")
    autocomplete_fields = ("account", "period")
    list_filter = ("period",)
    search_fields = ("account__code", "account__name", "note")

    def has_change_permission(self, request, obj=None):
        if obj and obj.period_id and obj.period.is_closed:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.period_id and obj.period.is_closed:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # Payment ما عنده posted، مؤشر الترحيل هو journal_entry_id
    list_display = ("id", "payment_type", "amount", "date", "who", "is_posted")
    list_filter = ("payment_type",)
    search_fields = ("note", "customer__name", "supplier__name")
    autocomplete_fields = ("customer", "supplier", "journal_entry")

    def who(self, obj):
        if obj.customer_id:
            return obj.customer.name
        if obj.supplier_id:
            return obj.supplier.name
        return "-"
    who.short_description = "الطرف"

    def is_posted(self, obj):
        return bool(obj.journal_entry_id)
    is_posted.boolean = True
    is_posted.short_description = "Posted"
