# accounting_app/seed_accounts.py

from django.db import transaction
from django.db.utils import OperationalError, ProgrammingError

from .models import Account


def seed_accounts_if_empty():
    """
    Seeds default Chart of Accounts only if there are NO accounts yet.
    Safe to call multiple times; it will do nothing once accounts exist.
    """
    try:
        # لو الجدول مش موجود لسا (قبل migrate) رح يرمي خطأ
        if Account.objects.exists():
            return
    except (OperationalError, ProgrammingError):
        return

    def upsert(code, name, account_type, normal_balance, parent=None):
        obj, created = Account.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "parent": parent,
                "account_type": account_type,
                "normal_balance": normal_balance,
            },
        )
        if not created:
            changed = False
            if obj.name != name:
                obj.name = name
                changed = True
            if obj.parent_id != (parent.id if parent else None):
                obj.parent = parent
                changed = True
            if obj.account_type != account_type:
                obj.account_type = account_type
                changed = True
            if obj.normal_balance != normal_balance:
                obj.normal_balance = normal_balance
                changed = True
            if changed:
                obj.save()
        return obj

    A, L, E, R, X = (
        Account.ASSET,
        Account.LIABILITY,
        Account.EQUITY,
        Account.REVENUE,
        Account.EXPENSE,
    )
    D, C = Account.DEBIT, Account.CREDIT

    # لضمان التنفيذ كله مرة وحدة وبشكل آمن
    with transaction.atomic():
        # ============== ROOTS ==============
        assets = upsert("1000", "الأصول", A, D)
        liabilities = upsert("2000", "الخصوم", L, C)
        equity = upsert("3000", "حقوق الملكية", E, C)
        revenue = upsert("4000", "الإيرادات", R, C)
        expense = upsert("5000", "المصاريف", X, D)

        # ============== ASSETS ==============
        current_assets = upsert("1100", "أصول متداولة", A, D, assets)

        cash_bank = upsert("1110", "النقد والبنوك", A, D, current_assets)
        upsert("1111", "الصندوق", A, D, cash_bank)
        upsert("1112", "بنك - حساب جاري", A, D, cash_bank)
        upsert("1113", "بنك - دولار", A, D, cash_bank)
        upsert("1114", "حوالات قيد التحصيل", A, D, cash_bank)

        ar = upsert("1120", "الذمم المدينة (العملاء)", A, D, current_assets)
        upsert("1121", "عملاء محليين", A, D, ar)
        upsert("1122", "عملاء تصدير", A, D, ar)
        upsert("1123", "شيكات عند التحصيل", A, D, ar)

        inventory = upsert("1130", "المخزون", A, D, current_assets)
        upsert("1131", "مواد خام (ذرة/زيت/نكهات)", A, D, inventory)
        upsert("1132", "مواد تعبئة (أكياس/كرتون/لاصق)", A, D, inventory)
        upsert("1133", "إنتاج تحت التشغيل (WIP)", A, D, inventory)
        upsert("1134", "بضاعة تامة الصنع", A, D, inventory)
        upsert("1135", "توالف مواد خام", A, D, inventory)
        upsert("1136", "توالف إنتاج", A, D, inventory)

        prepaid = upsert("1140", "مصاريف مدفوعة مقدمًا", A, D, current_assets)
        upsert("1141", "إيجار مدفوع مقدمًا", A, D, prepaid)
        upsert("1142", "تأمينات مدفوعة مقدمًا", A, D, prepaid)

        fixed_assets = upsert("1200", "أصول غير متداولة", A, D, assets)
        ppe = upsert("1210", "الأصول الثابتة", A, D, fixed_assets)
        upsert("1211", "خطوط إنتاج", A, D, ppe)
        upsert("1212", "ماكينات تعبئة", A, D, ppe)
        upsert("1213", "سيارات", A, D, ppe)
        upsert("1214", "أثاث ومكاتب", A, D, ppe)

        # مجمع الإهلاك: حساب أصول لكن طبيعي دائن (Contra-Asset)
        acc_dep = upsert("1220", "مجمع الإهلاك", A, C, fixed_assets)
        upsert("1221", "مجمع إهلاك خطوط الإنتاج", A, C, acc_dep)
        upsert("1222", "مجمع إهلاك السيارات", A, C, acc_dep)

        # ============== LIABILITIES ==============
        current_liab = upsert("2100", "خصوم متداولة", L, C, liabilities)

        ap = upsert("2110", "الذمم الدائنة (الموردين)", L, C, current_liab)
        upsert("2111", "موردين مواد خام", L, C, ap)
        upsert("2112", "موردين مواد تعبئة", L, C, ap)

        accrued = upsert("2120", "مصاريف مستحقة", L, C, current_liab)
        upsert("2121", "رواتب مستحقة", L, C, accrued)
        upsert("2122", "كهرباء ومياه مستحقة", L, C, accrued)

        upsert("2130", "قروض قصيرة الأجل", L, C, current_liab)

        long_liab = upsert("2200", "خصوم طويلة الأجل", L, C, liabilities)
        upsert("2211", "قرض معدات", L, C, long_liab)
        upsert("2212", "قرض سيارات", L, C, long_liab)

        # ============== EQUITY ==============
        upsert("3110", "رأس المال", E, C, equity)
        upsert("3120", "أرباح محتجزة", E, C, equity)
        upsert("3130", "صافي ربح/خسارة السنة", E, C, equity)

        # ============== REVENUE ==============
        sales = upsert("4100", "المبيعات", R, C, revenue)
        upsert("4111", "مبيعات محلية", R, C, sales)
        upsert("4112", "مبيعات تصدير", R, C, sales)

        # مردودات: Contra-Revenue طبيعي مدين
        returns = upsert("4200", "مردودات ومسموحات المبيعات", R, D, revenue)
        upsert("4211", "مردود مبيعات", R, D, returns)

        # ============== EXPENSE ==============
        # بما إنك ما عندك COGS كنوع مستقل، بنحطه كفرع تحت المصاريف
        cogs = upsert("5100", "تكلفة التصنيع / تكلفة المبيعات", X, D, expense)
        upsert("5111", "استهلاك مواد خام", X, D, cogs)
        upsert("5112", "استهلاك مواد تعبئة", X, D, cogs)
        upsert("5113", "أجور عمال الإنتاج", X, D, cogs)
        upsert("5114", "كهرباء خط الإنتاج", X, D, cogs)
        upsert("5115", "توالف إنتاج", X, D, cogs)

        admin = upsert("5200", "مصاريف إدارية وعمومية", X, D, expense)
        upsert("5211", "رواتب إدارية", X, D, admin)
        upsert("5212", "إنترنت واتصالات", X, D, admin)
        upsert("5213", "قرطاسية", X, D, admin)

        selling = upsert("5300", "مصاريف بيع وتوزيع", X, D, expense)
        upsert("5311", "نقل وتوصيل", X, D, selling)
        upsert("5312", "عمولات مندوبين", X, D, selling)
        upsert("5313", "تسويق وإعلانات", X, D, selling)

        other = upsert("5400", "مصاريف أخرى", X, D, expense)
        upsert("5411", "صيانة", X, D, other)
        upsert("5412", "إهلاك", X, D, other)
