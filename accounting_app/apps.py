from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AccountingAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounting_app"

    def ready(self):
        from .seed_accounts import seed_accounts_if_empty

        def run_seed(sender, **kwargs):
            seed_accounts_if_empty()

        post_migrate.connect(run_seed, sender=self)
