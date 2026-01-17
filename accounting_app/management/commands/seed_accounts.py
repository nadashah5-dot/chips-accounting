from django.core.management.base import BaseCommand
from accounting_app.models import Account

class Command(BaseCommand):
    help = 'إضافة الحسابات الرئيسية والفرعية لمصنع الشيبس'

    def handle(self, *args, **options):
        # ==========================
        # الحسابات الرئيسية
        # ==========================
        assets, created = Account.objects.get_or_create(code='1000', name='الأصول')
        liabilities, created = Account.objects.get_or_create(code='2000', name='الخصوم')
        equity, created = Account.objects.get_or_create(code='3000', name='رأس المال')
        revenue, created = Account.objects.get_or_create(code='4000', name='الإيرادات')
        expenses, created = Account.objects.get_or_create(code='5000', name='المصروفات')

        # ==========================
        # الحسابات الفرعية تحت الأصول
        # ==========================
        Account.objects.get_or_create(code='1100', name='النقدية', parent=assets)
        Account.objects.get_or_create(code='1200', name='البنك', parent=assets)
        Account.objects.get_or_create(code='1300', name='المدينون', parent=assets)
        Account.objects.get_or_create(code='1400', name='المخزون', parent=assets)
        Account.objects.get_or_create(code='1500', name='المصاريف المدفوعة مقدماً', parent=assets)
        Account.objects.get_or_create(code='1600', name='الأصول الثابتة', parent=assets)

        # ==========================
        # الحسابات الفرعية تحت الخصوم
        # ==========================
        Account.objects.get_or_create(code='2100', name='الدائنون', parent=liabilities)
        Account.objects.get_or_create(code='2200', name='القروض طويلة الأجل', parent=liabilities)
        Account.objects.get_or_create(code='2300', name='المصروفات المستحقة', parent=liabilities)

        # ==========================
        # الحسابات الفرعية تحت رأس المال
        # ==========================
        Account.objects.get_or_create(code='3100', name='رأس المال المستثمر', parent=equity)
        Account.objects.get_or_create(code='3200', name='الأرباح المحتجزة', parent=equity)

        # ==========================
        # الحسابات الفرعية تحت الإيرادات
        # ==========================
        Account.objects.get_or_create(code='4100', name='مبيعات الشيبس', parent=revenue)
        Account.objects.get_or_create(code='4200', name='إيرادات أخرى', parent=revenue)

        # ==========================
        # الحسابات الفرعية تحت المصروفات
        # ==========================
        Account.objects.get_or_create(code='5100', name='تكلفة البضاعة المباعة', parent=expenses)
        Account.objects.get_or_create(code='5200', name='المصروفات الإدارية', parent=expenses)
        Account.objects.get_or_create(code='5300', name='المصروفات البيعية', parent=expenses)
        Account.objects.get_or_create(code='5400', name='المصروفات الأخرى', parent=expenses)

        self.stdout.write(self.style.SUCCESS('تم إضافة الحسابات الرئيسية والفرعية بنجاح'))
