from django import forms
from django.forms import inlineformset_factory, modelformset_factory

from .models import (
    JournalEntry, JournalLine, Account, AccountingPeriod,
    Customer, Supplier, SalesInvoice, PurchaseInvoice,
    SalesItem, PurchaseItem, Payment, OpeningBalance
)

# =======================
# رأس القيد
# =======================
class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ["period", "date", "reference", "description"]
        widgets = {
            "period": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "reference": forms.TextInput(attrs={"class": "form-control", "placeholder": "مرجع / رقم سند / …"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "بيان القيد"}),
        }


class JournalLineForm(forms.ModelForm):
    # ✅ حقل عرض فقط (لا يُكتب يدويًا)
    account_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "readonly": "readonly",
            "placeholder": "اسم الحساب",
            "tabindex": "-1",
        })
    )

    class Meta:
        model = JournalLine
        fields = ["account", "account_name", "note", "debit", "credit"]
        widgets = {
            "account": forms.Select(attrs={"class": "form-select account-select"}),
            "note": forms.TextInput(attrs={"class": "form-control", "placeholder": "ملاحظة السطر"}),
            "debit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "credit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
        }


# ✅ هذا لازم يكون على مستوى الملف (مش داخل كلاس)
JournalLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalLine,
    form=JournalLineForm,
    extra=2,
    can_delete=True
)


# =======================
# شجرة الحسابات
# =======================
class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["code", "name", "parent"]
        labels = {"code": "رمز الحساب", "name": "اسم الحساب", "parent": "الحساب الرئيسي"}
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "أدخل رمز الحساب"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "أدخل اسم الحساب"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
        }


# =======================
# العملاء / الموردين
# =======================
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "contact"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "contact": forms.TextInput(attrs={"class": "form-control"}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "contact": forms.TextInput(attrs={"class": "form-control"}),
        }


# =======================
# فواتير (كما هي عندك)
# =======================
class SalesInvoiceForm(forms.ModelForm):
    class Meta:
        model = SalesInvoice
        fields = ["customer", "date"]
        widgets = {
            "customer": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class PurchaseInvoiceForm(forms.ModelForm):
    class Meta:
        model = PurchaseInvoice
        fields = ["supplier", "date"]
        widgets = {
            "supplier": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class OpeningBalanceForm(forms.ModelForm):
    class Meta:
        model = OpeningBalance
        fields = ["account", "debit", "credit", "note"]
        widgets = {
            "account": forms.Select(attrs={"class": "form-select"}),
            "debit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "credit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "note": forms.TextInput(attrs={"class": "form-control"}),
        }


OpeningBalanceFormSet = modelformset_factory(
    OpeningBalance,
    form=OpeningBalanceForm,
    extra=0,
    can_delete=True
)


class SalesItemForm(forms.ModelForm):
    class Meta:
        model = SalesItem
        fields = ["product", "qty", "price"]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
            "qty": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
        }


class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ["product", "qty", "price"]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
            "qty": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
        }


SalesItemFormSet = inlineformset_factory(SalesInvoice, SalesItem, form=SalesItemForm, extra=5, can_delete=True)
PurchaseItemFormSet = inlineformset_factory(PurchaseInvoice, PurchaseItem, form=PurchaseItemForm, extra=5, can_delete=True)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["payment_type", "date", "customer", "supplier", "cash_account", "amount", "note"]
        widgets = {
            "payment_type": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "supplier": forms.Select(attrs={"class": "form-select"}),
            "cash_account": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "note": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default cash/bank account from AccountingConfig (if available)
        if not self.instance or not getattr(self.instance, 'pk', None):
            try:
                from .models import AccountingConfig
                cfg = AccountingConfig.objects.first()
                if cfg and cfg.cash_account_id and not self.initial.get('cash_account'):
                    self.initial['cash_account'] = cfg.cash_account_id
            except Exception:
                # Don't break the form if config table isn't ready yet
                pass

        # Keep both fields optional in UI; validation is enforced in Payment.clean()
        self.fields['customer'].required = False
        self.fields['supplier'].required = False

from django import forms
from django.core.exceptions import ValidationError
from .models import AccountingPeriod

class AccountingPeriodForm(forms.ModelForm):
    class Meta:
        model = AccountingPeriod
        fields = ["name", "start_date", "end_date", "is_closed"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "is_closed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")

        if start and end and end < start:
            raise ValidationError("تاريخ النهاية يجب أن يكون بعد تاريخ البداية.")

        if start and end:
            qs = AccountingPeriod.objects.filter(start_date__lte=end, end_date__gte=start)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("هذه الفترة تتداخل مع فترة محاسبية موجودة بالفعل.")

        return cleaned
