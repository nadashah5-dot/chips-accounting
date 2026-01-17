from django.apps import AppConfig


class AccountingAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounting_app"

    # ملاحظة:
    # تم تعطيل تحميل signals بشكل افتراضي حتى لا يحدث تحديث مخزون WarehouseStock تلقائياً
    # عند إنشاء PurchaseItem. نظام المحاسبة يعتمد على FIFO (StockLayer/StockMovement)
    # ويتم تحديث المخزون عند الترحيل post_to_journal فقط.
    def ready(self):
        # لا تستورد signals هنا
        return
