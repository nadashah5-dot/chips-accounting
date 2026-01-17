# manufacturing_app/forms.py
from django import forms
from django.forms import inlineformset_factory
from inventory.models import Product
from .models import BillOfMaterials, BillOfMaterialsItem, ProductionOrder

class BOMForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterials
        fields = ["product"]
        widgets = {"product": forms.Select(attrs={"class": "form-select"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # المنتج النهائي فقط
        self.fields["product"].queryset = Product.objects.filter(type=Product.TYPE_FINISHED).order_by("name")


class BOMItemForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterialsItem
        fields = ["component", "quantity"]
        widgets = {
            "component": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # المواد الخام فقط
        self.fields["component"].queryset = Product.objects.filter(type=Product.TYPE_RAW).order_by("name")


BOMItemFormSet = inlineformset_factory(
    BillOfMaterials,
    BillOfMaterialsItem,
    form=BOMItemForm,
    extra=1,
    can_delete=True
)


class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ["product", "quantity", "source_warehouse", "destination_warehouse", "notes"]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "source_warehouse": forms.Select(attrs={"class": "form-select"}),
            "destination_warehouse": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # أوامر الإنتاج لازم تكون للمنتجات النهائية فقط
        self.fields["product"].queryset = Product.objects.filter(type=Product.TYPE_FINISHED).order_by("name")
