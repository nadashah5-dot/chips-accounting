# manufacturing_app/views.py
from django.utils import timezone
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404, redirect

from inventory.models import Product, Warehouse, WarehouseStock, WarehouseMovement
from .models import BillOfMaterials, BillOfMaterialsItem, ProductionOrder
from .forms import BOMForm, BOMItemFormSet, ProductionOrderForm



@login_required(login_url="/login/")
def manufacturing_home(request):
    return render(request, "manufacturing/home.html")


# -------------------------
# BOM (الوصفات)
# -------------------------
@login_required(login_url="/login/")
def bom_list(request):
    boms = BillOfMaterials.objects.select_related("product").order_by("product__name")
    return render(request, "manufacturing/bom_list.html", {"boms": boms})


@login_required(login_url="/login/")
@transaction.atomic
def bom_create(request):
    if request.method == "POST":
        form = BOMForm(request.POST)
        if form.is_valid():
            # منع تكرار BOM لنفس المنتج
            product = form.cleaned_data["product"]
            if BillOfMaterials.objects.filter(product=product).exists():
                messages.error(request, "يوجد وصفة بالفعل لهذا المنتج.")
                return redirect("manufacturing_app:bom_list")

            bom = form.save()
            formset = BOMItemFormSet(request.POST, instance=bom)
            if formset.is_valid():
                formset.save()
                messages.success(request, "✅ تم إنشاء الوصفة بنجاح.")
                return redirect("manufacturing_app:bom_detail", pk=bom.pk)
            else:
                # إذا العناصر فيها خطأ — ارجع عالصفحة مع نفس البيانات
                return render(request, "manufacturing/bom_form.html", {"form": form, "formset": formset, "mode": "create"})
        else:
            formset = BOMItemFormSet(request.POST)
    else:
        form = BOMForm()
        formset = BOMItemFormSet()

    return render(request, "manufacturing/bom_form.html", {"form": form, "formset": formset, "mode": "create"})


@login_required(login_url="/login/")
def bom_detail(request, pk):
    bom = get_object_or_404(
        BillOfMaterials.objects.select_related("product").prefetch_related(
            Prefetch("items", queryset=BillOfMaterialsItem.objects.select_related("component").order_by("component__name"))
        ),
        pk=pk
    )
    return render(request, "manufacturing/bom_detail.html", {"bom": bom})


@login_required(login_url="/login/")
@transaction.atomic
def bom_edit(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk)

    if request.method == "POST":
        form = BOMForm(request.POST, instance=bom)
        formset = BOMItemFormSet(request.POST, instance=bom)

        if form.is_valid() and formset.is_valid():
            # لو تم تغيير المنتج، تأكد ما بصير duplicate
            new_product = form.cleaned_data["product"]
            if BillOfMaterials.objects.exclude(pk=bom.pk).filter(product=new_product).exists():
                messages.error(request, "لا يمكن تغيير المنتج لأن لديه وصفة أخرى.")
                return redirect("manufacturing_app:bom_edit", pk=bom.pk)

            form.save()
            formset.save()
            messages.success(request, "✅ تم تعديل الوصفة بنجاح.")
            return redirect("manufacturing_app:bom_detail", pk=bom.pk)

    else:
        form = BOMForm(instance=bom)
        formset = BOMItemFormSet(instance=bom)

    return render(request, "manufacturing/bom_form.html", {"form": form, "formset": formset, "mode": "edit", "bom": bom})


@login_required(login_url="/login/")
@transaction.atomic
def bom_delete(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk)
    if request.method == "POST":
        bom.delete()
        messages.success(request, "تم حذف الوصفة.")
        return redirect("manufacturing_app:bom_list")
    return render(request, "manufacturing/bom_confirm_delete.html", {"bom": bom})


# -------------------------
# Production Orders (أوامر الإنتاج)
# -------------------------
@login_required(login_url="/login/")
def production_order_list(request):
    orders = ProductionOrder.objects.select_related(
        "product", "source_warehouse", "destination_warehouse"
    ).order_by("-created_at")

    # ✅ اسم التمبلت الصحيح عندك
    return render(request, "manufacturing/orders_list.html", {"orders": orders})



@login_required(login_url="/login/")
@transaction.atomic
def production_order_create(request):
    if request.method == "POST":
        form = ProductionOrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, "✅ تم إنشاء أمر الإنتاج.")
            return redirect("manufacturing_app:production_order_detail", pk=order.pk)
    else:
        form = ProductionOrderForm()
    return render(request, "manufacturing/order_form.html", {"form": form, "mode": "create"})


@login_required(login_url="/login/")
def production_order_detail(request, pk):
    order = get_object_or_404(
        ProductionOrder.objects.select_related("product", "source_warehouse", "destination_warehouse"),
        pk=pk
    )
    bom = BillOfMaterials.objects.filter(product=order.product).first()
    bom_items = []
    if bom:
        bom_items = list(
            bom.items.select_related("component").order_by("component__name")
        )

    return render(request, "manufacturing/order_detail.html", {
        "order": order,
        "bom": bom,
        "bom_items": bom_items,
    })


@login_required(login_url="/login/")
@transaction.atomic
def production_order_edit(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)

    if order.status in [ProductionOrder.STATUS_COMPLETED]:
        messages.error(request, "لا يمكن تعديل أمر مكتمل.")
        return redirect("manufacturing_app:production_order_detail", pk=order.pk)

    if request.method == "POST":
        form = ProductionOrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ تم تعديل أمر الإنتاج.")
            return redirect("manufacturing_app:production_order_detail", pk=order.pk)
    else:
        form = ProductionOrderForm(instance=order)

    return render(request, "manufacturing/order_form.html", {"form": form, "mode": "edit", "order": order})


@login_required(login_url="/login/")
@transaction.atomic
def production_order_delete(request, pk):
    order = get_object_or_404(ProductionOrder, pk=pk)
    if request.method == "POST":
        order.delete()
        messages.success(request, "تم حذف أمر الإنتاج.")
        return redirect("manufacturing_app:production_order_list")
    return render(request, "manufacturing/order_confirm_delete.html", {"order": order})


# -------------------------
# Execute Production Order (تنفيذ الأمر)
# -------------------------
@login_required(login_url="/login/")
@transaction.atomic
def production_order_execute(request, pk):
    order = get_object_or_404(
        ProductionOrder.objects.select_related("product", "source_warehouse", "destination_warehouse"),
        pk=pk
    )

    if order.status == ProductionOrder.STATUS_COMPLETED:
        messages.info(request, "هذا الأمر مكتمل بالفعل.")
        return redirect("manufacturing_app:production_order_detail", pk=order.pk)

    if request.method != "POST":
        return redirect("manufacturing_app:production_order_detail", pk=order.pk)

    # تحقق وجود BOM
    bom = BillOfMaterials.objects.filter(product=order.product).first()
    if not bom:
        messages.error(request, "لا يوجد وصفة (BOM) لهذا المنتج. أنشئي وصفة أولاً.")
        return redirect("manufacturing_app:production_order_detail", pk=order.pk)

    # تحقق مستودعات
    if not order.source_warehouse or not order.destination_warehouse:
        messages.error(request, "يجب تحديد مستودع مصدر ومستودع وجهة لتنفيذ الأمر.")
        return redirect("manufacturing_app:production_order_detail", pk=order.pk)

    qty_to_make = Decimal(order.quantity or 0)
    if qty_to_make <= 0:
        messages.error(request, "كمية أمر الإنتاج غير صحيحة.")
        return redirect("manufacturing_app:production_order_detail", pk=order.pk)

    # تجميع احتياجات الخام
    items = list(bom.items.select_related("component"))
    required = []
    for it in items:
        req_qty = (Decimal(it.quantity) * qty_to_make)
        required.append((it.component, req_qty))

    # تحقق توفر الخام في المستودع المصدر
    shortages = []
    for comp, req_qty in required:
        stock = WarehouseStock.objects.filter(warehouse=order.source_warehouse, product=comp).first()
        available = Decimal(stock.quantity) if stock else Decimal("0")
        if available < req_qty:
            shortages.append(f"{comp.name} (المطلوب {req_qty} والمتوفر {available})")

    if shortages:
        messages.error(request, "لا توجد كميات كافية للمواد الخام: " + "، ".join(shortages))
        return redirect("manufacturing_app:production_order_detail", pk=order.pk)

    # تنفيذ السحب من المصدر
    for comp, req_qty in required:
        stock = WarehouseStock.objects.get(warehouse=order.source_warehouse, product=comp)
        stock.quantity = Decimal(stock.quantity) - req_qty
        stock.save()

        WarehouseMovement.objects.create(
            warehouse=order.source_warehouse,
            product=comp,
            movement_type="سحب",
            quantity=req_qty,
            notes=f"سحب مواد خام لتنفيذ أمر إنتاج PO#{order.id} لصالح {order.product.name}"
        )

    # إضافة المنتج النهائي للوجهة
    finished_stock, _ = WarehouseStock.objects.get_or_create(
        warehouse=order.destination_warehouse,
        product=order.product,
        defaults={"quantity": 0}
    )
    finished_stock.quantity = Decimal(finished_stock.quantity) + qty_to_make
    finished_stock.save()

    WarehouseMovement.objects.create(
        warehouse=order.destination_warehouse,
        product=order.product,
        movement_type="إضافة",
        quantity=qty_to_make,
        notes=f"إضافة منتج نهائي من تنفيذ أمر إنتاج PO#{order.id}"
    )

    # تحديث حالة الأمر
    order.status = ProductionOrder.STATUS_COMPLETED
    order.executed_at = order.executed_at or timezone.now()
    order.save()

    messages.success(request, "✅ تم تنفيذ أمر الإنتاج وتحديث المخزون وتسجيل الحركات.")
    return redirect("manufacturing_app:production_order_detail", pk=order.pk)
