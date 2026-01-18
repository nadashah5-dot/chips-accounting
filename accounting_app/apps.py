# accounting_app/apps.py

from django.apps import AppConfig


class AccountingAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounting_app"

    def ready(self):
        # تشغيل seed مرة وحدة عند الإقلاع (لو الداتابيس فاضية)
        try:
            from .seed_accounts import seed_accounts_if_empty
            seed_accounts_if_empty()
        except Exception:
            # ما بدنا نكسر تشغيل السيرفر لأي سبب
            pass
