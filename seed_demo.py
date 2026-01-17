import decimal
from datetime import timedelta
from django.utils import timezone

from accounting_app.models import (
    Account, AccountingPeriod, AccountingConfig,
    Customer, Supplier,
    OpeningBalance, Payment,
    PurchaseInvoice, PurchaseItem,
    SalesInvoice, SalesItem,
    JournalEntry, JournalLine
)
from inventory.models import Product, StockLayer, StockMovement

D = decimal.Decimal

def get_account(code: str) -> Account:
    acc = Account.objects.filter(code=code).first()
    if not acc:
        raise RuntimeError(f"Account code {code} not found. Run: python manage.py seed_accounts")
    return acc

def ensure_period_open() -> AccountingPeriod:
    today = timezone.now().date()
    start = today.replace(day=1)

    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1, day=1)
    else:
        next_month = start.replace(month=start.month + 1, day=1)

    end = next_month - timedelta(days=1)

    p, _ = AccountingPeriod.objects.get_or_create(
        name=f"{start.year}-{start.month:02d}",
        defaults={"start_date": start, "end_date": end, "is_closed": False},
    )
    p.start_date = start
    p.end_date = end
    p.is_closed = False
    p.save(update_fields=["start_date", "end_date", "is_closed"])
    return p

def ensure_config():
    cash = get_account("1100")
    bank = Account.objects.filter(code="1200").first()
    ar = get_account("1300")
    inv = get_account("1400")
    ap = get_account("2100")
    sales = get_account("4100")
    cogs = get_account("5100")
    retained = get_account("3200")

    cfg = AccountingConfig.objects.first()
    if not cfg:
        cfg = AccountingConfig.objects.create(
            ar_account=ar,
            ap_account=ap,
            sales_account=sales,
            purchases_account=inv,
            inventory_account=inv,
            cogs_account=cogs,
            cash_account=(bank or cash),
            retained_earnings_account=retained,
        )
    else:
        cfg.ar_account = ar
        cfg.ap_account = ap
        cfg.sales_account = sales
        cfg.purchases_account = inv
        cfg.inventory_account = inv
        cfg.cogs_account = cogs
        cfg.cash_account = (bank or cash)
        cfg.retained_earnings_account = retained
        cfg.save()
    return cfg

def ensure_parties():
    cust, _ = Customer.objects.get_or_create(
        name="عميل تجريبي - سوبرماركت عمان",
        defaults={"contact": "0790000000"},
    )
    supp, _ = Supplier.objects.get_or_create(
        name="مورد تجريبي - مواد أولية",
        defaults={"contact": "0780000000"},
    )
    return cust, supp

def ensure_product():
    p, _ = Product.objects.get_or_create(
        sku="CHIPS-TEST-001",
        defaults={
            "name": "شيبس تجريبي - Cheese",
            "unit": "bag",
            "type": "finished",
            "quantity": 0,
            "price": D("0.000"),
        },
    )
    p.name = "شيبس تجريبي - Cheese"
    p.unit = "bag"
    p.type = "finished"
    p.price = D("0.500")
    p.save()
    return p

def add_opening_balance(period: AccountingPeriod):
    cash = get_account("1100")
    capital = get_account("3100") if Account.objects.filter(code="3100").exists() else get_account("3200")

    OpeningBalance.objects.filter(period=period, account__code__in=[cash.code, capital.code]).delete()
    OpeningBalance.objects.create(period=period, account=cash, debit=D("500.00"), credit=D("0"), note="Opening Cash")
    OpeningBalance.objects.create(period=period, account=capital, debit=D("0"), credit=D("500.00"), note="Opening Capital")

def demo_purchase(supplier, product):
    pi = PurchaseInvoice.objects.create(
        supplier=supplier,
        date=timezone.now().date(),
        total=D("0"),
    )
    PurchaseItem.objects.create(purchase=pi, product=product, qty=D("100.0000"), price=D("0.2000"))
    je = pi.post_to_journal(user=None)
    return pi, je

def demo_sale(customer, product):
    si = SalesInvoice.objects.create(
        customer=customer,
        date=timezone.now().date(),
        total=D("0"),
    )
    SalesItem.objects.create(sales=si, product=product, qty=D("20.0000"), price=D("0.5000"))
    je = si.post_to_journal(user=None)
    return si, je

def demo_payments(customer, supplier):
    pr = Payment.objects.create(payment_type=Payment.RECEIPT, customer=customer, amount=D("50.00"), note="قبض تجريبي")
    pr.post_to_journal(user=None)

    pd = Payment.objects.create(payment_type=Payment.DISBURSE, supplier=supplier, amount=D("30.00"), note="صرف تجريبي")
    pd.post_to_journal(user=None)
    return pr, pd

def demo_manual_journal(period):
    cash = get_account("1100")
    other_rev = get_account("4200") if Account.objects.filter(code="4200").exists() else get_account("4100")

    je = JournalEntry.objects.create(
        period=period,
        date=timezone.now().date(),
        reference="MANUAL-DEMO",
        description="قيد يدوي تجريبي",
        created_by=None,
    )
    JournalLine.objects.create(entry=je, account=cash, debit=D("10.00"), credit=D("0"), note="زيادة نقدية")
    JournalLine.objects.create(entry=je, account=other_rev, debit=D("0"), credit=D("10.00"), note="إيراد تجريبي")
    return je

def main():
    period = ensure_period_open()
    ensure_config()
    cust, supp = ensure_parties()
    prod = ensure_product()

    add_opening_balance(period)
    pi, _ = demo_purchase(supp, prod)
    si, _ = demo_sale(cust, prod)
    pr, pd = demo_payments(cust, supp)
    je_manual = demo_manual_journal(period)

    print("=== DONE SEED DEMO ===")
    print("Period:", period.name)
    print("PurchaseInvoice:", pi.id, "JE:", pi.journal_entry_id)
    print("SalesInvoice:", si.id, "JE:", si.journal_entry_id)
    print("Payment Receipt:", pr.id, "posted:", bool(pr.journal_entry_id))
    print("Payment Disburse:", pd.id, "posted:", bool(pd.journal_entry_id))
    print("Manual JE:", je_manual.id)
    print("StockLayers:", StockLayer.objects.filter(product=prod).count())
    print("StockMovements:", StockMovement.objects.filter(product=prod).count())

main()
