from django.urls import path
from . import views

app_name = "account"

urlpatterns = [
    # Auth / Dashboard
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Home
    path("", views.accounting_home, name="accounting_home"),

    # =========================
    # Journal
    # =========================
    path("journal_entries/", views.journal_entries, name="journal_entries"),
    path("journal/reverse/<int:entry_id>/", views.reverse_journal_entry, name="reverse_journal_entry"),
    path("journal/export/pdf/", views.export_journal_pdf, name="export_journal_pdf"),
    path("journal_entries/export_excel/", views.export_journal_excel, name="export_journal_excel"),
    path("journal/<int:entry_id>/export/pdf/", views.export_single_journal_pdf, name="export_single_journal_pdf"),

    # =========================
    # Ledger
    # =========================
    path("general_ledger/", views.general_ledger, name="general_ledger"),
    path("ledger/account/", views.general_ledger, name="ledger_account"),

    # =========================
    # Invoices
    # =========================
    path("sales_invoices/", views.sales_invoices, name="sales_invoices"),
    path("purchase_invoices/", views.purchase_invoices, name="purchase_invoices"),
    path("sales-invoices/<int:invoice_id>/post/", views.post_sales_invoice, name="post_sales_invoice"),
    path("purchase-invoices/<int:invoice_id>/post/", views.post_purchase_invoice, name="post_purchase_invoice"),

    # =========================
    # Reports
    # =========================
    path("trial_balance/", views.trial_balance, name="trial_balance"),
    path("income_statement/", views.income_statement, name="income_statement"),
    path("balance_sheet/", views.balance_sheet, name="balance_sheet"),

    # =========================
    # Cash
    # =========================
    path("cash_management/", views.cash_management, name="cash_management"),

    # =========================
    # Customers / Suppliers
    # =========================
    path("customer_accounts/", views.customer_accounts, name="customer_accounts"),
    path("supplier_accounts/", views.supplier_accounts, name="supplier_accounts"),

    # =========================
    # Chart of Accounts
    # =========================
    path("chart_of_accounts/", views.chart_of_accounts, name="chart_of_accounts"),
    path("add_account/", views.add_account, name="add_account"),
    path("add_subaccount/<int:parent_id>/", views.add_subaccount, name="add_subaccount"),
    path("edit_account/<int:account_id>/", views.edit_account, name="edit_account"),
    path("delete_account/<int:account_id>/", views.delete_account, name="delete_account"),

 
    # =========================
    # Payments ✅
    # =========================
    path("payments/", views.payments, name="payments"),
    path("payments/<int:payment_id>/post/", views.post_payment, name="post_payment"),
    path("payments/<int:pk>/print/", views.payment_print, name="payment_print"),  # ✅
    path("payments/<int:pk>/pdf/", views.payment_pdf, name="payment_pdf"),

        # =========================
    # Payments Reports ✅✅
    # =========================
    path("payments/receipts-report/", views.receipts_report, name="receipts_report"),
    path("payments/receipts-report/pdf/", views.receipts_report_pdf, name="receipts_report_pdf"),
    path("payments/receipts-report/excel/", views.receipts_report_excel, name="receipts_report_excel"),

    path("payments/disbursements-report/", views.disbursements_report, name="disbursements_report"),
    path("payments/disbursements-report/pdf/", views.disbursements_report_pdf, name="disbursements_report_pdf"),
    path("payments/disbursements-report/excel/", views.disbursements_report_excel, name="disbursements_report_excel"),
    
    path("journal/", views.journal_entries, name="journal_entries"),
    path("ajax/account-name/", views.get_account_name, name="get_account_name"),
     path("reports/sales-invoices/", views.sales_invoices_report, name="sales_invoices_report"),
    path("reports/purchase-invoices/", views.purchase_invoices_report, name="purchase_invoices_report"),

    # مستندات غير مرحّلة + عكس مستندات
    path("reports/unposted/", views.unposted_documents, name="unposted_documents"),
    path("sales-invoices/<int:invoice_id>/reverse/", views.reverse_sales_invoice, name="reverse_sales_invoice"),
    path("purchase-invoices/<int:invoice_id>/reverse/", views.reverse_purchase_invoice, name="reverse_purchase_invoice"),
    path("payments/<int:payment_id>/reverse/", views.reverse_payment, name="reverse_payment"),

    # =========================
    # Opening balances + Periods
    # =========================
    path("opening-balances/", views.opening_balances, name="opening_balances"),
    path("periods/", views.periods_list, name="periods_list"),
    path("periods/new/", views.period_create, name="period_create"),
    path("periods/<int:period_id>/toggle/", views.period_toggle_close, name="period_toggle_close"),

    # إذا فعلاً عندك هدول views
    path("period/<int:period_id>/close/", views.close_period, name="close_period"),
    path("period/<int:period_id>/reopen/", views.reopen_period, name="reopen_period"),

    # ترحيل الافتتاحي لقيد
    path("period/<int:period_id>/opening/post/", views.post_opening_to_journal, name="post_opening_to_journal"),
    path("sales-invoices/<int:invoice_id>/pdf/", views.export_sales_invoice_pdf, name="sales_invoice_pdf"),
    path("purchase-invoices/<int:invoice_id>/pdf/", views.export_purchase_invoice_pdf, name="purchase_invoice_pdf"),


    # Ajax
    path("ajax/account-name/", views.get_account_name, name="get_account_name"),
    path("reports/customer-statement/<int:customer_id>/", views.customer_statement, name="customer_statement"),
    path("reports/supplier-statement/<int:supplier_id>/", views.supplier_statement, name="supplier_statement"),

]

