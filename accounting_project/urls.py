from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path("admin/", admin.site.urls),

    # إعادة توجيه أي مستخدم يدخل على root إلى صفحة تسجيل الدخول
    path("", lambda request: redirect("account:login")),

    # apps
    path("ui/", include(("ui_templates.urls", "ui"), namespace="ui")),

    # ✅ accounting with namespace
    path("account/", include(("accounting_app.urls", "account"), namespace="account")),

    path("inventory/", include("inventory.urls")),
    path("manufacturing/", include("manufacturing_app.urls")),
]
