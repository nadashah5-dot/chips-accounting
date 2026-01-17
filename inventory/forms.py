from django import forms
from .models import Product, StockMovement
from .models import Warehouse, WarehouseStock, WarehouseMovement

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "type", "sku", "unit"]  # ✅ لا تضيفي quantity/price
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "sku": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-select"}),
        }
class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['movement_type', 'qty', 'unit_cost', 'related_invoice']
        widgets = {
            'movement_type': forms.Select(attrs={'class':'form-control'}),
            'qty': forms.NumberInput(attrs={'class':'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class':'form-control'}),
            'related_invoice': forms.TextInput(attrs={'class':'form-control'}),
        }

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['code', 'name', 'location', 'manager']
        labels = {
            'code': 'الكود',
            'name': 'اسم المستودع',
            'location': 'الموقع',
            'manager': 'المسؤول',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
        }

class WarehouseStockForm(forms.ModelForm):
    class Meta:
        model = WarehouseStock
        fields = ['warehouse', 'product', 'quantity']
        labels = {
            'warehouse': 'المستودع',
            'product': 'المنتج',
            'quantity': 'الكمية',
        }
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class WarehouseMovementForm(forms.ModelForm):
    class Meta:
        model = WarehouseMovement
        fields = ['product', 'movement_type', 'quantity', 'notes']  # 🔹 حذف 'warehouse' لأنه نمرره من الـ view
        labels = {
            'product': 'المنتج',
            'movement_type': 'نوع الحركة',
            'quantity': 'الكمية',
            'notes': 'ملاحظات',
        }
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

from django import forms
from .models import Warehouse, Product

class WarehouseTransferForm(forms.Form):
    to_warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), label="إلى مستودع")
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label="المنتج")
    quantity = forms.IntegerField(min_value=1, label="الكمية")
    notes = forms.CharField(required=False, label="ملاحظات")
