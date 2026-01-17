# accounting_app/signals.py
"""Signals (Disabled by default)

ملاحظة: هذا الملف **غير محمّل تلقائياً** لأن AccountingAppConfig.ready() لا يستورد signals.
السبب: منع تحديث WarehouseStock تلقائياً عند إنشاء PurchaseItem، لأن النظام يعتمد FIFO عبر StockLayer/StockMovement
ويتم تحديث المخزون عند الترحيل post_to_journal فقط.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PurchaseItem

# من كان يستخدمه سابقاً:
# from inventory.utils import receive_product


@receiver(post_save, sender=PurchaseItem)
def create_stock_on_purchase_item(sender, instance, created, **kwargs):
    """Disabled: no automatic warehouse stock updates."""
    # if created:
    #     receive_product(
    #         instance.product,
    #         instance.qty,
    #         instance.price,
    #         related_invoice=f"PO:{instance.purchase.invoice_number}",
    #     )
    return
