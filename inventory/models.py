from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User

# inventory/models.py
from django.db import models

class Product(models.Model):
    TYPE_RAW = "raw"
    TYPE_FINISHED = "finished"
    TYPE_CHOICES = [
        (TYPE_RAW, "مواد خام"),
        (TYPE_FINISHED, "منتج نهائي"),
    ]

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, blank=True, default="")
    unit = models.CharField(max_length=50, blank=True, default="")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_RAW)

    # ✅ مهم لتفادي IntegrityError لأن العمود موجود بالـ DB وممنوع يكون NULL
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    # ✅ إذا كان عندك price بالـ DB ومش موجود بالموديل (نفس فكرة quantity)
    price = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    def __str__(self):
        return self.name



class StockLayer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='layers')
    qty_remaining = models.DecimalField(max_digits=14, decimal_places=4, verbose_name="الكمية المتبقية")
    cost = models.DecimalField(max_digits=14, decimal_places=4, verbose_name="تكلفة الوحدة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "طبقة مخزون"
        verbose_name_plural = "طبقات المخزون"

    def __str__(self):
        return f"Layer {self.id} - {self.product.sku} ({self.qty_remaining})"


class StockMovement(models.Model):
    MOVEMENT_TYPE = [('in', 'IN'), ('out', 'OUT')]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPE)
    qty = models.DecimalField(max_digits=14, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    related_invoice = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "حركة مخزون"
        verbose_name_plural = "حركات المخزون"

    def __str__(self):
        return f"{self.movement_type} {self.product.sku} {self.qty}"


class Warehouse(models.Model):
    code = models.CharField("الكود", max_length=20, unique=True)
    name = models.CharField("اسم المستودع", max_length=100)
    location = models.CharField("الموقع", max_length=200)
    manager = models.ForeignKey(User, verbose_name="المسؤول", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class WarehouseStock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} في {self.warehouse.name}"



class WarehouseMovement(models.Model):
    MOVEMENT_TYPE = (
        ('إضافة', 'إضافة'),
        ('سحب', 'سحب'),
        ('نقل', 'نقل'),
    )

    warehouse = models.ForeignKey(Warehouse, verbose_name="المستودع", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="المنتج", on_delete=models.CASCADE)
    movement_type = models.CharField("نوع الحركة", max_length=10, choices=MOVEMENT_TYPE)
    quantity = models.IntegerField("الكمية")
    date = models.DateTimeField("التاريخ", auto_now_add=True)
    notes = models.TextField("ملاحظات", blank=True, null=True)

    def __str__(self):
        return f"{self.movement_type} - {self.product.name} - {self.warehouse.name}"


class Item(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return f"{self.name} ({self.quantity})"
