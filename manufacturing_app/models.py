from django.db import models
from django.utils import timezone
from inventory.models import Product, Warehouse


class BillOfMaterials(models.Model):
    """وصفة تصنيع (BOM) لمنتج نهائي واحد"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="bom")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"BOM - {self.product.name}"


class BillOfMaterialsItem(models.Model):
    """مكون داخل الوصفة"""
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name="items")
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="bom_components")
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        unique_together = ("bom", "component")

    def __str__(self):
        return f"{self.component.name} x {self.quantity}"


class ProductionOrder(models.Model):
    """أمر إنتاج: يسحب خامات من مستودع ويضيف المنتج النهائي لمستودع آخر"""
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "قيد الانتظار"),
        (STATUS_IN_PROGRESS, "قيد التنفيذ"),
        (STATUS_COMPLETED, "مكتمل"),
        (STATUS_CANCELLED, "ملغي"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="production_orders")
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    source_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="production_source_orders",
        null=True, blank=True
    )
    destination_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="production_destination_orders",
        null=True, blank=True
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    executed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return f"PO#{self.id} - {self.product.name}"
