from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import decimal

from inventory.models import Product, StockLayer, StockMovement


# =======================
# Helpers: FIFO stock costing (Inventory integration)
# =======================
def _stock_in(product: Product, qty, unit_cost, related_invoice: str = ""):
    qty = decimal.Decimal(qty)
    unit_cost = decimal.Decimal(unit_cost)
    if qty <= 0:
        return

    # ⚠️ تأكدي أن StockLayer عندك فيه الحقول: qty_remaining + cost
    StockLayer.objects.create(
        product=product,
        qty_remaining=qty,
        cost=unit_cost,
    )

    # ⚠️ تأكدي أن StockMovement عندك فيه الحقول: movement_type + related_invoice
    StockMovement.objects.create(
        product=product,
        movement_type="in",
        qty=qty,
        unit_cost=unit_cost,
        related_invoice=related_invoice,
    )


def _fifo_consume(product: Product, qty, related_invoice: str = ""):
    """Consume qty from StockLayer FIFO. Returns total_cost (Decimal) and avg unit cost."""
    qty = decimal.Decimal(qty)
    if qty <= 0:
        return decimal.Decimal("0"), decimal.Decimal("0")

    remaining = qty
    total_cost = decimal.Decimal("0")

    layers = (
        StockLayer.objects.select_for_update()
        .filter(product=product, qty_remaining__gt=0)
        .order_by("created_at", "id")
    )

    for layer in layers:
        if remaining <= 0:
            break

        take = min(layer.qty_remaining, remaining)
        total_cost += take * layer.cost

        layer.qty_remaining = layer.qty_remaining - take
        layer.save(update_fields=["qty_remaining"])
        remaining -= take

    if remaining > 0:
        raise ValidationError(f"المخزون غير كافي للمنتج {product.sku}. المطلوب {qty}.")

    avg = (total_cost / qty) if qty else decimal.Decimal("0")

    StockMovement.objects.create(
        product=product,
        movement_type="out",
        qty=qty,
        unit_cost=avg,
        related_invoice=related_invoice,
    )

    return total_cost, avg


# =======================
# شجرة الحسابات
# =======================
class Account(models.Model):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"

    ACCOUNT_TYPES = (
        (ASSET, "أصول"),
        (LIABILITY, "خصوم"),
        (EQUITY, "حقوق ملكية"),
        (REVENUE, "إيرادات"),
        (EXPENSE, "مصاريف"),
    )

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    NORMAL_BALANCES = (
        (DEBIT, "مدين"),
        (CREDIT, "دائن"),
    )

    code = models.CharField(max_length=20, unique=True, verbose_name="رقم الحساب")
    name = models.CharField(max_length=255, verbose_name="اسم الحساب")

    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="الحساب الرئيسي",
    )

    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        default=ASSET,
        verbose_name="نوع الحساب",
    )

    normal_balance = models.CharField(
        max_length=10,
        choices=NORMAL_BALANCES,
        default=DEBIT,
        verbose_name="الطبيعي",
    )

    def __str__(self):
        return f"{self.code} - {self.name}"


# =======================
# العملاء / الموردين
# =======================
class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=255)
    contact = models.TextField(blank=True)

    def __str__(self):
        return self.name


# =======================
# الفترات المحاسبية
# =======================
class AccountingPeriod(models.Model):
    name = models.CharField(max_length=50)  # مثال: 2025-01
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        status = "مقفلة" if self.is_closed else "مفتوحة"
        return f"{self.name} ({status})"

    @classmethod
    def get_for_date(cls, dt):
        """
        ترجع الفترة اللي يغطيها تاريخ معيّن (أو None إذا ما في فترة).
        dt ممكن يكون date أو datetime
        """
        if dt is None:
            d = timezone.now().date()
        else:
            d = dt.date() if hasattr(dt, "date") else dt
        return cls.objects.filter(start_date__lte=d, end_date__gte=d).order_by("-start_date").first()

    # Alias لأن Payment عندك يستخدم get_period_for_date
    @classmethod
    def get_period_for_date(cls, dt):
        return cls.get_for_date(dt)


# =======================
# ✅ تسلسل أرقام المستندات (آمن مع PostgreSQL)
# =======================
class DocumentSequence(models.Model):
    DOC_TYPES = (
       ("JE", "Journal Entry"),
       ("SI", "Sales Invoice"),
       ("PI", "Purchase Invoice"),
       ("RC", "Receipt Voucher"),
       ("PV", "Payment Voucher"),
    )

    doc_type = models.CharField(max_length=10, choices=DOC_TYPES)
    period = models.ForeignKey(
        "AccountingPeriod",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sequences",
    )
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("doc_type", "period")

    def __str__(self):
        p = self.period.name if self.period_id else "NO-PERIOD"
        return f"{self.doc_type} / {p} = {self.last_number}"

    @classmethod
    def next(cls, doc_type: str, period=None) -> int:
        with transaction.atomic():
            obj, _ = cls.objects.select_for_update().get_or_create(
                doc_type=doc_type,
                period=period,
                defaults={"last_number": 0},
            )
            obj.last_number = F("last_number") + 1
            obj.save(update_fields=["last_number"])
            obj.refresh_from_db(fields=["last_number"])
            return obj.last_number


# =======================
# إعدادات الربط Control Accounts
# =======================
class AccountingConfig(models.Model):
    ar_account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="cfg_ar",
        verbose_name="حساب ذمم العملاء (AR)",
    )
    ap_account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="cfg_ap",
        verbose_name="حساب ذمم الموردين (AP)",
    )
    sales_account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="cfg_sales",
        verbose_name="حساب المبيعات",
    )
    purchases_account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="cfg_purchases",
        verbose_name="حساب المشتريات/المخزون",
    )

    inventory_account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="cfg_inventory",
        verbose_name="حساب المخزون (Inventory)",
        null=True,
        blank=True,
    )
    cogs_account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="cfg_cogs",
        verbose_name="حساب تكلفة البضاعة المباعة (COGS)",
        null=True,
        blank=True,
    )
    cash_account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="cfg_cash",
        verbose_name="حساب الصندوق/البنك",
        null=True,
        blank=True,
    )

    retained_earnings_account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="cfg_retained",
        verbose_name="حساب الأرباح المرحلة (Retained Earnings)",
        null=True,
        blank=True,
    )

    def __str__(self):
        return "Accounting Config"

    @classmethod
    def get_config(cls):
        cfg = cls.objects.first()
        if not cfg:
            raise ValidationError("لا يوجد AccountingConfig. يرجى إدخاله من الـ Admin أولاً.")
        return cfg


# =======================
# القيود اليومية (Multi-line)
# =======================
class JournalEntry(models.Model):
    serial_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="الرقم المسلسل",
    )

    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, verbose_name="البيان")
    reference = models.CharField(max_length=100, blank=True)

    period = models.ForeignKey(
        "AccountingPeriod",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="الفترة المحاسبية",
    )

    is_reversed = models.BooleanField(default=False, verbose_name="تم عمل قيد عكسي؟")
    reversed_entry = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="original_entry",
        verbose_name="القيد العكسي",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def _ensure_period_open(self):
        if self.period_id:
            if self.period.is_closed:
                raise ValidationError("لا يمكن الإضافة/التعديل/الحذف داخل فترة محاسبية مقفلة")
            return

        p = AccountingPeriod.get_for_date(self.date)
        if p and p.is_closed:
            raise ValidationError(f"لا يمكن الإضافة/التعديل: الفترة {p.name} مقفلة حسب تاريخ القيد")

    def save(self, *args, **kwargs):
        self._ensure_period_open()

        if self._state.adding and not self.serial_number:
            seq = DocumentSequence.next("JE", period=self.period if self.period_id else None)
            period_part = self.period.name if self.period_id else "NO-PERIOD"
            self.serial_number = f"JE-{period_part}-{seq:06d}"

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._ensure_period_open()
        super().delete(*args, **kwargs)

    def total_debit(self):
        return sum(line.debit for line in self.lines.all())

    def total_credit(self):
        return sum(line.credit for line in self.lines.all())

    def is_balanced(self):
        return self.total_debit() == self.total_credit()

    def clean(self):
        if self.total_debit() != self.total_credit():
            raise ValidationError("مجموع المدين يجب أن يساوي مجموع الدائن")

    def __str__(self):
        sn = self.serial_number or str(self.id)
        return f"قيد رقم {sn} - {self.date}"


class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, related_name="lines", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)

    def _ensure_period_open(self):
        if not self.entry_id:
            return

        p = self.entry.period if self.entry.period_id else AccountingPeriod.get_for_date(self.entry.date)
        if p and p.is_closed:
            raise ValidationError("لا يمكن تعديل/حذف سطور قيد داخل فترة محاسبية مقفلة")

    def save(self, *args, **kwargs):
        self._ensure_period_open()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._ensure_period_open()
        super().delete(*args, **kwargs)

    def clean(self):
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("لا يمكن إدخال مدين ودائن في نفس السطر")
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("يجب إدخال قيمة مدين أو دائن")

    def __str__(self):
        return f"{self.account} | مدين {self.debit} | دائن {self.credit}"


# =======================
# فواتير المشتريات
# =======================
class PurchaseInvoice(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    supplier = models.ForeignKey("Supplier", on_delete=models.PROTECT)
    date = models.DateField(default=timezone.now)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    journal_entry = models.OneToOneField(
        "JournalEntry",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_invoice",
        verbose_name="القيد الناتج عن الفاتورة",
    )

    def recalc_total(self):
        # ممنوع إعادة احتساب/تعديل الإجمالي إذا الفاتورة مرحّلة
        if self.pk and self.journal_entry_id:
            raise ValidationError("لا يمكن تعديل فاتورة مرحّلة إلى القيود.")

        tot = sum((i.line_total() for i in self.items.all()), decimal.Decimal("0"))
        tot = tot.quantize(decimal.Decimal("0.01"))

        if self.total != tot:
            self.total = tot
            super(PurchaseInvoice, self).save(update_fields=["total"])

        return self.total



    def _ensure_period_open(self):
        p = AccountingPeriod.get_for_date(self.date)
        if not p:
            raise ValidationError("لا توجد فترة محاسبية تغطي تاريخ الفاتورة. أنشئي فترة أولاً.")
        if p.is_closed:
            raise ValidationError(f"لا يمكن الإضافة/التعديل: الفترة {p.name} مقفلة")
        return p

    def save(self, *args, **kwargs):
        if self.pk and self.journal_entry_id:
            raise ValidationError("لا يمكن تعديل فاتورة مرحّلة إلى القيود.")

        self._ensure_period_open()

        if self._state.adding and not self.invoice_number:
            seq = DocumentSequence.next("PI", period=None)
            self.invoice_number = f"PI-{seq:06d}"

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.journal_entry_id:
            raise ValidationError("لا يمكن حذف فاتورة مرحّلة لأن لها قيد مرتبط.")
        self._ensure_period_open()
        super().delete(*args, **kwargs)

    @transaction.atomic
    def post_to_journal(self, user=None):
        if self.journal_entry_id:
            return self.journal_entry

        period = self._ensure_period_open()
        cfg = AccountingConfig.get_config()

        if self.items.count() == 0:
            raise ValidationError("لا يمكن ترحيل فاتورة مشتريات بدون بنود أصناف.")

        total = sum((i.line_total() for i in self.items.all()), decimal.Decimal("0")).quantize(decimal.Decimal("0.01"))
        if total <= 0:
            raise ValidationError("إجمالي الفاتورة يجب أن يكون أكبر من صفر.")

        if self.total != total:
            self.total = total
            super(PurchaseInvoice, self).save(update_fields=["total"])

        je = JournalEntry.objects.create(
            period=period,
            date=self.date,
            reference=self.invoice_number or "",
            description=f"قيد فاتورة مشتريات رقم {self.invoice_number}",
            created_by=user,
        )

        debit_account = cfg.inventory_account or cfg.purchases_account
        if not debit_account:
            raise ValidationError("يرجى تحديد حساب المخزون أو المشتريات ضمن إعدادات المحاسبة.")

        JournalLine.objects.create(entry=je, account=debit_account, debit=total, credit=0, note=f"مشتريات - {self.supplier.name}")
        JournalLine.objects.create(entry=je, account=cfg.ap_account, debit=0, credit=total, note="ذمم دائنين")

        for item in self.items.select_related("product"):
            _stock_in(item.product, item.qty, item.price, related_invoice=self.invoice_number or "")

        PurchaseInvoice.objects.filter(id=self.id, journal_entry__isnull=True).update(journal_entry=je)
        self.journal_entry = je
        return je

    def __str__(self):
        return self.invoice_number or f"PI-{self.id}"



class PurchaseItem(models.Model):
    purchase = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=14, decimal_places=4)
    price = models.DecimalField(max_digits=14, decimal_places=4)

    def line_total(self):
        return self.qty * self.price

    def _check_parent_editable(self):
        # ممنوع تعديل/حذف بنود فاتورة مرحّلة
        if self.purchase_id and self.purchase.journal_entry_id:
            raise ValidationError("لا يمكن تعديل/حذف بنود فاتورة مرحّلة إلى القيود.")
        # ممنوع تعديل إذا الفترة مقفلة
        self.purchase._ensure_period_open()

    def save(self, *args, **kwargs):
        if self.pk:
            self._check_parent_editable()
        else:
            # حتى عند الإضافة: ممنوع إذا الفاتورة مرحّلة أو الفترة مقفلة
            self._check_parent_editable()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._check_parent_editable()
        return super().delete(*args, **kwargs)


# =======================
# فواتير المبيعات
# =======================
class SalesInvoice(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    customer = models.ForeignKey("Customer", on_delete=models.PROTECT)
    date = models.DateField(default=timezone.now)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    journal_entry = models.OneToOneField(
        "JournalEntry",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sales_invoice",
        verbose_name="القيد الناتج عن الفاتورة",
    )

    def recalc_total(self):
        # ممنوع إعادة احتساب/تعديل الإجمالي إذا الفاتورة مرحّلة
        if self.pk and self.journal_entry_id:
            raise ValidationError("لا يمكن تعديل فاتورة مرحّلة إلى القيود.")

        tot = sum((i.line_total() for i in self.items.all()), decimal.Decimal("0"))
        tot = tot.quantize(decimal.Decimal("0.01"))

        if self.total != tot:
            self.total = tot
            super(SalesInvoice, self).save(update_fields=["total"])

        return self.total



    def _ensure_period_open(self):
        p = AccountingPeriod.get_for_date(self.date)
        if not p:
            raise ValidationError("لا توجد فترة محاسبية تغطي تاريخ الفاتورة. أنشئي فترة أولاً.")
        if p.is_closed:
            raise ValidationError(f"لا يمكن الإضافة/التعديل: الفترة {p.name} مقفلة")
        return p

    def save(self, *args, **kwargs):
        if self.pk and self.journal_entry_id:
            raise ValidationError("لا يمكن تعديل فاتورة مرحّلة إلى القيود.")

        self._ensure_period_open()

        if self._state.adding and not self.invoice_number:
            seq = DocumentSequence.next("SI", period=None)
            self.invoice_number = f"SI-{seq:06d}"

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.journal_entry_id:
            raise ValidationError("لا يمكن حذف فاتورة مرحّلة لأن لها قيد مرتبط.")
        self._ensure_period_open()
        super().delete(*args, **kwargs)

    @transaction.atomic
    def post_to_journal(self, user=None):
        if self.journal_entry_id:
            return self.journal_entry

        period = self._ensure_period_open()
        cfg = AccountingConfig.get_config()

        if self.items.count() == 0:
            raise ValidationError("لا يمكن ترحيل فاتورة مبيعات بدون بنود أصناف.")

        total = sum((i.line_total() for i in self.items.all()), decimal.Decimal("0")).quantize(decimal.Decimal("0.01"))
        if total <= 0:
            raise ValidationError("إجمالي الفاتورة يجب أن يكون أكبر من صفر.")

        if self.total != total:
            self.total = total
            super(SalesInvoice, self).save(update_fields=["total"])

        je = JournalEntry.objects.create(
            period=period,
            date=self.date,
            reference=self.invoice_number or "",
            description=f"قيد فاتورة مبيعات رقم {self.invoice_number}",
            created_by=user,
        )

        JournalLine.objects.create(entry=je, account=cfg.ar_account, debit=total, credit=0, note=f"ذمم عملاء - {self.customer.name}")
        JournalLine.objects.create(entry=je, account=cfg.sales_account, debit=0, credit=total, note="إيراد مبيعات")

        if cfg.cogs_account and cfg.inventory_account:
            total_cost = decimal.Decimal("0")
            for item in self.items.select_related("product"):
                cost, _avg = _fifo_consume(item.product, item.qty, related_invoice=self.invoice_number or "")
                total_cost += cost

            total_cost = total_cost.quantize(decimal.Decimal("0.01"))
            if total_cost > 0:
                JournalLine.objects.create(entry=je, account=cfg.cogs_account, debit=total_cost, credit=0, note="تكلفة بضاعة مباعة")
                JournalLine.objects.create(entry=je, account=cfg.inventory_account, debit=0, credit=total_cost, note="تخفيض مخزون")

        SalesInvoice.objects.filter(id=self.id, journal_entry__isnull=True).update(journal_entry=je)
        self.journal_entry = je
        return je

    def __str__(self):
        return self.invoice_number or f"SI-{self.id}"



class SalesItem(models.Model):
    sales = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=14, decimal_places=4)
    price = models.DecimalField(max_digits=14, decimal_places=4)

    def line_total(self):
        return self.qty * self.price

    def _check_parent_editable(self):
        # ممنوع تعديل/حذف بنود فاتورة مرحّلة
        if self.sales_id and self.sales.journal_entry_id:
            raise ValidationError("لا يمكن تعديل/حذف بنود فاتورة مرحّلة إلى القيود.")
        # ممنوع أي تعديل إذا الفترة مقفلة
        self.sales._ensure_period_open()

    def save(self, *args, **kwargs):
        # إضافة أو تعديل: لازم تكون الفاتورة غير مرحّلة والفترة مفتوحة
        self._check_parent_editable()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._check_parent_editable()
        return super().delete(*args, **kwargs)



# =======================
# سندات قبض/صرف (Payment)
# =======================
class Payment(models.Model):
    RECEIPT = "RECEIPT"
    DISBURSE = "DISBURSE"

    PAYMENT_TYPES = [
        (RECEIPT, "Receipt"),
        (DISBURSE, "Disbursement"),
    ]

    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    date = models.DateField(default=timezone.now)

    customer = models.ForeignKey("Customer", on_delete=models.PROTECT, null=True, blank=True)
    supplier = models.ForeignKey("Supplier", on_delete=models.PROTECT, null=True, blank=True)

    voucher_number = models.CharField(max_length=30, unique=True, blank=True, null=True)
    is_locked = models.BooleanField(default=False)

    cash_account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments_cash",
        verbose_name="حساب الصندوق/البنك",
    )

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)

    journal_entry = models.OneToOneField(
        "JournalEntry",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payment_doc",
        verbose_name="القيد الناتج عن السند",
    )

    # -----------------------
    # Helpers
    # -----------------------
    def _doc_type(self) -> str:
        return "RC" if self.payment_type == self.RECEIPT else "PV"

    def _ensure_period_open(self):
        period = AccountingPeriod.get_period_for_date(self.date) or AccountingPeriod.get_for_date(self.date)
        if not period:
            raise ValidationError("لا توجد فترة محاسبية تغطي هذا التاريخ.")
        if period.is_closed:
            raise ValidationError("الفترة المحاسبية مقفلة. لا يمكن إضافة/تعديل سندات.")
        return period

    # -----------------------
    # Validations
    # -----------------------
    def clean(self):
        if self.payment_type == self.RECEIPT and not self.customer_id:
            raise ValidationError("سند القبض يجب أن يكون مرتبطًا بعميل.")
        if self.payment_type == self.DISBURSE and not self.supplier_id:
            raise ValidationError("سند الصرف يجب أن يكون مرتبطًا بمورد.")
        if self.payment_type == self.RECEIPT and self.supplier_id:
            raise ValidationError("سند القبض لا يجب ربطه بمورد.")
        if self.payment_type == self.DISBURSE and self.customer_id:
            raise ValidationError("سند الصرف لا يجب ربطه بعميل.")
        if (self.amount or 0) <= 0:
            raise ValidationError("قيمة السند يجب أن تكون أكبر من صفر.")

        # منع التعديل بعد الترحيل/القفل
        if self.pk:
            old = Payment.objects.filter(pk=self.pk).values("journal_entry_id", "is_locked").first()
            if old and (old["journal_entry_id"] or old["is_locked"]):
                raise ValidationError("لا يمكن تعديل السند بعد ترحيله. لإجراء تعديل: اعكسي القيد وأنشئي سندًا جديدًا.")

        # منع الإضافة/التعديل داخل فترة مقفلة
        if self.date:
            period = AccountingPeriod.get_period_for_date(self.date) or AccountingPeriod.get_for_date(self.date)
            if period and period.is_closed:
                raise ValidationError("لا يمكن إنشاء/تعديل سند داخل فترة محاسبية مقفلة.")

    # -----------------------
    # Save + auto numbering
    # -----------------------
    def save(self, *args, **kwargs):
        # حماية إضافية ضد التعديل بعد الترحيل
        if self.pk:
            old = Payment.objects.filter(pk=self.pk).values("journal_entry_id", "is_locked").first()
            if old and (old["journal_entry_id"] or old["is_locked"]):
                raise ValidationError("لا يمكن تعديل السند بعد ترحيله. لإجراء تعديل: اعكسي القيد وأنشئي سندًا جديدًا.")

        period = None
        if self.date:
            period = AccountingPeriod.get_period_for_date(self.date) or AccountingPeriod.get_for_date(self.date)
            if period and period.is_closed:
                raise ValidationError("الفترة المحاسبية مقفلة. لا يمكن إضافة/تعديل سندات.")

        # ترقيم عند الإضافة فقط
        if self._state.adding and not self.voucher_number:
            if not period:
                period = self._ensure_period_open()
            seq = DocumentSequence.next(self._doc_type(), period=period)
            self.voucher_number = f"{self._doc_type()}-{period.name}-{seq:06d}"

        self.full_clean()
        super().save(*args, **kwargs)

    # -----------------------
    # Post to Journal
    # -----------------------
    @transaction.atomic
    def post_to_journal(self, user=None):
        if self.journal_entry_id:
            return self.journal_entry

        period = self._ensure_period_open()
        cfg = AccountingConfig.get_config()

        # تأكدي أنه عنده رقم سند
        if not self.voucher_number:
            seq = DocumentSequence.next(self._doc_type(), period=period)
            self.voucher_number = f"{self._doc_type()}-{period.name}-{seq:06d}"
            Payment.objects.filter(id=self.id).update(voucher_number=self.voucher_number)

        cash_acc = self.cash_account or cfg.cash_account
        if not cash_acc:
            raise ValidationError("يرجى تحديد حساب الصندوق/البنك ضمن إعدادات المحاسبة أو داخل السند.")

        je = JournalEntry.objects.create(
            period=period,
            date=self.date,
            reference=self.voucher_number or "",
            description=("سند قبض" if self.payment_type == self.RECEIPT else "سند صرف") + (f" - {self.note}" if self.note else ""),
            created_by=user,
        )

        if self.payment_type == self.RECEIPT:
            if not cfg.ar_account:
                raise ValidationError("يرجى تحديد حساب الذمم المدينة (AR) ضمن إعدادات المحاسبة.")
            JournalLine.objects.create(entry=je, account=cash_acc, debit=self.amount, credit=0, note="قبض")
            JournalLine.objects.create(entry=je, account=cfg.ar_account, debit=0, credit=self.amount, note=f"سداد من {self.customer.name}")
        else:
            if not cfg.ap_account:
                raise ValidationError("يرجى تحديد حساب الذمم الدائنة (AP) ضمن إعدادات المحاسبة.")
            JournalLine.objects.create(entry=je, account=cfg.ap_account, debit=self.amount, credit=0, note=f"سداد إلى {self.supplier.name}")
            JournalLine.objects.create(entry=je, account=cash_acc, debit=0, credit=self.amount, note="صرف")

        Payment.objects.filter(id=self.id, journal_entry__isnull=True).update(journal_entry=je, is_locked=True)
        self.journal_entry = je
        self.is_locked = True
        return je

    def __str__(self):
        who = self.customer.name if self.customer_id else (self.supplier.name if self.supplier_id else "")
        return f"{self.get_payment_type_display()} - {who} - {self.amount}"


# =======================
# Opening Balances
# =======================
class OpeningBalance(models.Model):
    period = models.ForeignKey(
        "AccountingPeriod",
        on_delete=models.PROTECT,
        related_name="opening_balances",
        verbose_name="الفترة"
    )
    account = models.ForeignKey(
        "Account",
        on_delete=models.PROTECT,
        related_name="opening_balances",
        verbose_name="الحساب"
    )

    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = ("period", "account")
        ordering = ("account__code",)

    def clean(self):
        if (self.debit or 0) > 0 and (self.credit or 0) > 0:
            raise ValidationError("لا يمكن إدخال مدين ودائن معًا في الافتتاحي.")
        if (self.debit or 0) == 0 and (self.credit or 0) == 0:
            raise ValidationError("أدخلي قيمة مدين أو دائن.")

    def __str__(self):
        return f"Opening {self.period.name} - {self.account.code}"
