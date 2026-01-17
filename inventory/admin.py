# inventory/admin.py
from django.contrib import admin
from .models import Product, Warehouse, WarehouseStock, WarehouseMovement


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "sku", "unit")
    list_filter = ("type",)
    search_fields = ("name", "sku")


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "location", "manager")
    search_fields = ("name", "location")


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ("id", "warehouse", "product", "quantity")
    list_filter = ("warehouse",)
    search_fields = ("warehouse__name", "product__name")


@admin.register(WarehouseMovement)
class WarehouseMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "warehouse", "product", "movement_type", "quantity", "date")
    list_filter = ("warehouse", "movement_type")
    search_fields = ("warehouse__name", "product__name", "notes")
