from django.contrib import admin
from .models import BillOfMaterials, BillOfMaterialsItem, ProductionOrder


class BillOfMaterialsItemInline(admin.TabularInline):
    model = BillOfMaterialsItem
    extra = 0


@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "created_at")
    search_fields = ("product__name",)
    inlines = [BillOfMaterialsItemInline]


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "quantity", "status", "source_warehouse", "destination_warehouse", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("product__name",)
