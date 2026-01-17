from django.urls import path
from . import views

app_name = "manufacturing_app"

urlpatterns = [
    path("", views.manufacturing_home, name="manufacturing_home"),

    path("bom/", views.bom_list, name="bom_list"),
    path("bom/add/", views.bom_create, name="bom_create"),
    path("bom/<int:pk>/", views.bom_detail, name="bom_detail"),
    path("bom/<int:pk>/edit/", views.bom_edit, name="bom_edit"),
    path("bom/<int:pk>/delete/", views.bom_delete, name="bom_delete"),

    path("orders/", views.production_order_list, name="production_order_list"),
    path("orders/add/", views.production_order_create, name="production_order_create"),
    path("orders/<int:pk>/", views.production_order_detail, name="production_order_detail"),
    path("orders/<int:pk>/edit/", views.production_order_edit, name="production_order_edit"),
    path("orders/<int:pk>/delete/", views.production_order_delete, name="production_order_delete"),
    path("orders/<int:pk>/execute/", views.production_order_execute, name="production_order_execute"),
]
