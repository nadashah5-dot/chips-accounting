# inventory/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.paginator import Paginator
from .utils import build_warehouse_excel



from openpyxl import Workbook

from .models import Product, Warehouse, WarehouseStock, WarehouseMovement, StockMovement
from .forms import ProductForm, WarehouseForm, WarehouseStockForm, WarehouseMovementForm
from .utils import export_warehouse_pdf_build, export_all_warehouses_pdf


# =========================
# Home
# =========================
def inventory_home(request):
    warehouses = Warehouse.objects.all()
    total_stock = WarehouseStock.objects.aggregate(total=Sum('quantity'))['total'] or 0
    return render(request, 'inventory/home.html', {
        'warehouses': warehouses,
        'total_stock': total_stock,
    })


# =========================
# Products
# =========================
def product_list(request):
    products = Product.objects.all().order_by("name")
    return render(request, 'inventory/product_list.html', {'products': products})



def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request, 'تمت إضافة المنتج بنجاح.')
            return redirect('inventory:product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/product_add.html', {'form': form})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'inventory/product_detail.html', {'product': product})


def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES or None, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل المنتج بنجاح.')
            return redirect('inventory:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/product_form.html', {'form': form})


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'تم حذف المنتج.')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})


def stock_movements(request, pk):
    """stock_movements.html"""
    product = get_object_or_404(Product, pk=pk)
    movements = StockMovement.objects.filter(product=product).order_by('-created_at')
    return render(request, 'inventory/stock_movements.html', {
        'product': product,
        'movements': movements,
    })


# inventory/views.py

from io import BytesIO
from openpyxl import Workbook


from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .utils_exports import build_products_pdf, build_products_csv, build_products_excel

from .models import Product

def export_products_pdf(request):
    products = Product.objects.all().order_by("name")
    rows = []
    for p in products:
        rows.append({
            "name": p.name,
            "sku": getattr(p, "sku", "") or "",
            "unit": getattr(p, "unit", "") or "",
            "type_label": "مواد خام" if getattr(p, "type", "") == "raw" else "منتج نهائي",
        })
    return build_products_pdf(rows, title="تقرير المنتجات")


def export_products_csv(request):
    products = Product.objects.all().order_by("name")
    rows = []
    for p in products:
        rows.append({
            "name": p.name,
            "sku": getattr(p, "sku", "") or "",
            "unit": getattr(p, "unit", "") or "",
            "type_label": "مواد خام" if getattr(p, "type", "") == "raw" else "منتج نهائي",
        })
    return build_products_csv(products)  # ✅ بدون title  
    


def export_products_excel(request):
    from openpyxl import Workbook
    products = Product.objects.all().order_by("name")
    rows = []
    for p in products:
        rows.append({
            "name": p.name,
            "sku": getattr(p, "sku", "") or "",
            "unit": getattr(p, "unit", "") or "",
            "type_label": "مواد خام" if getattr(p, "type", "") == "raw" else "منتج نهائي",
        })

    wb = Workbook()
    build_products_excel(wb, rows, title="تقرير المنتجات")

    resp = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = 'attachment; filename="products.xlsx"'
    wb.save(resp)
    return resp


# =========================
# Warehouses
# =========================
def warehouse_list(request):
    sort = request.GET.get('sort', 'name')
    order = request.GET.get('order', 'asc')
    page_number = request.GET.get('page', 1)

    # ✅ العلاقة عندك: warehousestock
    qs = Warehouse.objects.annotate(
        total_qty=Coalesce(Sum('warehousestock__quantity'), 0)
    )

    # فرز مسموح
    if sort == 'name':
        sort_field = 'name'
    elif sort == 'quantity':
        sort_field = 'total_qty'
    elif sort == 'date':
        # ما عندك created_at حسب الأخطاء، نخليه ID كبديل
        sort_field = 'id'
    else:
        sort_field = 'name'

    if order == 'desc':
        sort_field = f'-{sort_field}'

    qs = qs.order_by(sort_field)

    paginator = Paginator(qs, 10)
    warehouses = paginator.get_page(page_number)

    return render(request, 'inventory/warehouse_list.html', {
        'warehouses': warehouses,
        'sort': sort,
        'order': order,
        'page': warehouses.number,
    })
    



def warehouse_add(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تمت إضافة المستودع بنجاح.')
            return redirect('inventory:warehouse_list')
    else:
        form = WarehouseForm()
    return render(request, 'inventory/warehouse_form.html', {'form': form})


def warehouse_edit(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل المستودع.')
            return redirect('inventory:warehouse_list')
    else:
        form = WarehouseForm(instance=warehouse)
    return render(request, 'inventory/warehouse_form.html', {'form': form})


def warehouse_delete(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        warehouse.delete()
        messages.success(request, 'تم حذف المستودع.')
        return redirect('inventory:warehouse_list')  # ✅ مهم
    return render(request, 'inventory/warehouse_confirm_delete.html', {'warehouse': warehouse})


def warehouse_detail(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)

    stocks_qs = WarehouseStock.objects.filter(
        warehouse=warehouse
    ).select_related('product').order_by('product__name')

    movements_qs = WarehouseMovement.objects.filter(
        warehouse=warehouse
    ).select_related('product').order_by('-date')

    mov_page = request.GET.get('mov_page', 1)
    paginator = Paginator(movements_qs, 10)
    movements = paginator.get_page(mov_page)

    total_qty = stocks_qs.aggregate(total=Sum('quantity'))['total'] or 0

    return render(request, 'inventory/warehouse_detail.html', {
        'warehouse': warehouse,
        'stocks': stocks_qs,
        'movements': movements,
        'total_qty': total_qty,
    })


# =========================
# Stock operations
# =========================
from django.db import transaction

@transaction.atomic
def warehouse_stock_add(request, pk=None, warehouse_pk=None):
    warehouse_id = warehouse_pk or pk
    warehouse = get_object_or_404(Warehouse, pk=warehouse_id)

    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity') or 0)

        if not product_id or quantity <= 0:
            messages.error(request, "الرجاء اختيار منتج وإدخال كمية صحيحة.")
            return redirect('inventory:warehouse_stock_add', pk=warehouse.pk)

        product = get_object_or_404(Product, pk=product_id)

        ws, _ = WarehouseStock.objects.get_or_create(
            warehouse=warehouse,
            product=product,
            defaults={'quantity': 0}
        )
        ws.quantity += quantity
        ws.save()

        WarehouseMovement.objects.create(
            warehouse=warehouse,
            product=product,
            movement_type='إضافة',
            quantity=quantity,
            notes='إضافة عبر واجهة المستودعات'
        )

        messages.success(request, "✅ تمت إضافة المخزون بنجاح.")
        return redirect('inventory:warehouse_detail', pk=warehouse.pk)

    form = WarehouseStockForm(initial={'warehouse': warehouse.pk})
    return render(request, 'inventory/warehouse_stock_add.html', {'form': form, 'warehouse': warehouse})


def warehouse_stock_edit(request, pk):
    stock_item = get_object_or_404(WarehouseStock, pk=pk)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity') or 0)
        stock_item.quantity = quantity
        stock_item.save()
        messages.success(request, "تم تعديل الكمية.")
        return redirect('inventory:warehouse_detail', pk=stock_item.warehouse.pk)

    form = WarehouseStockForm(instance=stock_item)
    return render(request, 'inventory/warehouse_stock_form.html', {
        'form': form,
        'warehouse': stock_item.warehouse
    })


def warehouse_stock_delete(request, pk):
    stock_item = get_object_or_404(WarehouseStock, pk=pk)
    warehouse_pk = stock_item.warehouse.pk

    if request.method == 'POST':
        stock_item.delete()
        messages.success(request, "تم حذف الصنف من المستودع.")
        return redirect('inventory:warehouse_detail', pk=warehouse_pk)  # ✅ مهم

    return render(request, 'inventory/warehouse_stock_confirm_delete.html', {'stock': stock_item})


@transaction.atomic
def warehouse_stock_remove(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity') or 0)
        reason = request.POST.get('reason', '')

        product = get_object_or_404(Product, pk=int(product_id))
        ws = WarehouseStock.objects.filter(warehouse=warehouse, product=product).first()

        if not ws or ws.quantity < quantity:
            messages.error(request, "لا توجد كمية كافية للصنف في المستودع.")
            return redirect('inventory:warehouse_detail', pk=warehouse.pk)

        ws.quantity -= quantity
        ws.save()

        WarehouseMovement.objects.create(
            warehouse=warehouse,
            product=product,
            movement_type='سحب',
            quantity=quantity,
            notes=reason
        )

        messages.success(request, "✅ تم السحب وتسجيل الحركة.")
        return redirect('inventory:warehouse_detail', pk=warehouse.pk)

    stocks = WarehouseStock.objects.filter(warehouse=warehouse).select_related('product')
    return render(request, 'inventory/warehouse_stock_remove.html', {
        'warehouse': warehouse,
        'stocks': stocks
    })


@transaction.atomic
def warehouse_movement_add(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == 'POST':
        product_id = request.POST.get('product')
        movement_type = request.POST.get('movement_type')  # "إضافة" أو "سحب"
        quantity = int(request.POST.get('quantity') or 0)
        notes = request.POST.get('notes', '')

        product = get_object_or_404(Product, pk=int(product_id))
        ws, _ = WarehouseStock.objects.get_or_create(
            warehouse=warehouse, product=product, defaults={'quantity': 0}
        )

        if movement_type == 'إضافة':
            ws.quantity += quantity
        else:
            ws.quantity = max(0, ws.quantity - quantity)

        ws.save()

        WarehouseMovement.objects.create(
            warehouse=warehouse,
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            notes=notes
        )

        messages.success(request, "✅ تم تسجيل الحركة.")
        return redirect('inventory:warehouse_detail', pk=warehouse.pk)

    form = WarehouseMovementForm()
    return render(request, 'inventory/warehouse_movement_form.html', {
        'form': form,
        'warehouse': warehouse
    })


# =========================
# Exports (Single warehouse)
# =========================
def export_warehouse_csv(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    stock = WarehouseStock.objects.filter(warehouse=warehouse)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="warehouse_{warehouse.id}.csv"'
    writer = csv.writer(response)

    writer.writerow(["شركة المحبة للصناعات الغذائية"])
    writer.writerow(["الأردن - عمّان - أبو علندا"])
    writer.writerow([f"المستودع: {warehouse.name}"])
    writer.writerow([])
    writer.writerow(["#", "اسم المنتج", "الكمية"])

    for i, s in enumerate(stock, 1):
        writer.writerow([i, s.product.name, s.quantity])

    return response


def export_warehouse_excel(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    stock = WarehouseStock.objects.filter(warehouse=warehouse).select_related("product")

    rows = []
    for s in stock:
        rows.append({
            "product_name": getattr(s.product, "name", ""),
            "quantity": s.quantity,
            "code": getattr(s.product, "code", "") or getattr(s.product, "sku", "") or "",
        })

    return build_warehouse_excel(
        warehouse_name=warehouse.name,
        rows=rows,
        filename=f"warehouse_{warehouse.id}.xlsx"
    )

def export_warehouse_pdf(request, pk):
    """PDF مستودع واحد - عربي من utils"""
    warehouse = get_object_or_404(Warehouse, pk=pk)
    stock = WarehouseStock.objects.filter(warehouse=warehouse).select_related("product")

    rows = []
    for s in stock:
        rows.append({
            "product_name": getattr(s.product, "name", ""),
            "quantity": s.quantity,
            # ✅ لا تفترضي code موجود:
            "code": getattr(s.product, "code", getattr(s.product, "sku", "")),
        })

    return export_warehouse_pdf_build(warehouse, rows)


# =========================
# Export ALL warehouses
# =========================
def export_all_warehouses_csv(request):
    warehouses = Warehouse.objects.all()
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="warehouses_all.csv"'
    writer = csv.writer(response)
    writer.writerow(['اسم المستودع', 'عدد الأصناف', 'إجمالي الكمية'])

    for w in warehouses:
        stock = WarehouseStock.objects.filter(warehouse=w)
        total_qty = stock.aggregate(total=Sum('quantity'))['total'] or 0
        writer.writerow([w.name, stock.count(), total_qty])

    return response


def export_all_warehouses_excel(request):
    warehouses = Warehouse.objects.all()
    wb = Workbook()
    ws = wb.active
    ws.title = "المستودعات"
    ws.append(['اسم المستودع', 'عدد الأصناف', 'إجمالي الكمية'])

    for w in warehouses:
        stock = WarehouseStock.objects.filter(warehouse=w)
        total_qty = stock.aggregate(total=Sum('quantity'))['total'] or 0
        ws.append([w.name, stock.count(), total_qty])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="warehouses_all.xlsx"'
    wb.save(response)
    return response


from .utils import export_all_warehouses_pdf as export_all_warehouses_pdf_util

def export_all_warehouses_pdf(request):
    warehouses = Warehouse.objects.all()
    data = {}

    for w in warehouses:
        stock = WarehouseStock.objects.filter(warehouse=w).select_related("product")
        rows = [{
            'product_name': getattr(s.product, "name", ""),
            'quantity': s.quantity,
            'code': getattr(s.product, 'code', getattr(s.product, 'sku', '')),
        } for s in stock]
        data[w.name] = rows

    return export_all_warehouses_pdf_util(data)


# للتوافق إذا عندك رابط قديم بالـ template:
def export_all_warehouses(request):
    return export_all_warehouses_csv(request)


from .forms import WarehouseTransferForm

@transaction.atomic
def warehouse_transfer(request, pk):
    from_warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == "POST":
        form = WarehouseTransferForm(request.POST)
        if form.is_valid():
            to_wh = form.cleaned_data["to_warehouse"]
            product = form.cleaned_data["product"]
            qty = form.cleaned_data["quantity"]
            notes = form.cleaned_data.get("notes") or ""

            if to_wh.pk == from_warehouse.pk:
                messages.error(request, "لا يمكن التحويل لنفس المستودع.")
                return redirect("inventory:warehouse_transfer", pk=from_warehouse.pk)

            from_stock = WarehouseStock.objects.filter(warehouse=from_warehouse, product=product).first()
            if not from_stock or from_stock.quantity < qty:
                messages.error(request, "لا توجد كمية كافية للتحويل.")
                return redirect("inventory:warehouse_transfer", pk=from_warehouse.pk)

            # subtract from source
            from_stock.quantity -= qty
            from_stock.save()

            # add to destination
            to_stock, _ = WarehouseStock.objects.get_or_create(
                warehouse=to_wh,
                product=product,
                defaults={"quantity": 0}
            )
            to_stock.quantity += qty
            to_stock.save()

            # movements log (سحب من المصدر + إضافة للهدف)
            WarehouseMovement.objects.create(
                warehouse=from_warehouse,
                product=product,
                movement_type="سحب",
                quantity=qty,
                notes=f"تحويل إلى {to_wh.name}. {notes}".strip()
            )
            WarehouseMovement.objects.create(
                warehouse=to_wh,
                product=product,
                movement_type="إضافة",
                quantity=qty,
                notes=f"تحويل من {from_warehouse.name}. {notes}".strip()
            )

            messages.success(request, "✅ تم التحويل بنجاح وتسجيل الحركات.")
            return redirect("inventory:warehouse_detail", pk=from_warehouse.pk)

    else:
        form = WarehouseTransferForm()

    return render(request, "inventory/warehouse_transfer.html", {
        "warehouse": from_warehouse,
        "form": form
    })

def export_warehouse_movements_pdf(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    movements = WarehouseMovement.objects.filter(warehouse=warehouse).select_related("product").order_by("-date")

    # إذا عندك في utils دوال عربي جاهزة، بنستفيد منها
    # هون رح نعمل PDF سريع بنفس reportlab لكن بدون تعقيد
    import os, io
    from datetime import datetime
    from django.conf import settings
    
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import arabic_reshaper
    from bidi.algorithm import get_display

    def ar(t):
        return get_display(arabic_reshaper.reshape(str(t or "")))

    company_name = "شركة المحبة للصناعات الغذائية"
    company_address = "الأردن - عمّان - أبو علندا"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # خط عربي
    font_path = os.path.join(settings.BASE_DIR, "inventory", "static", "inventory", "fonts", "Amiri-Regular.ttf")
    if not os.path.exists(font_path):
        font_path = r"C:\Windows\Fonts\arial.ttf"
    pdfmetrics.registerFont(TTFont("AR", font_path))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=70, bottomMargin=50)
    styles = getSampleStyleSheet()
    s_title = ParagraphStyle("t", parent=styles["Title"], fontName="AR", fontSize=18, alignment=1)
    s_norm = ParagraphStyle("n", parent=styles["Normal"], fontName="AR", fontSize=11, alignment=1)

    elements = []
    elements.append(Paragraph(ar(company_name), s_title))
    elements.append(Paragraph(ar(company_address), s_norm))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(ar(f"سجل حركات المستودع: {warehouse.name}"), s_title))
    elements.append(Paragraph(ar(f"تاريخ الطباعة: {now_str}"), s_norm))
    elements.append(Spacer(1, 12))

    data = [[ar("التاريخ"), ar("المنتج"), ar("نوع الحركة"), ar("الكمية"), ar("ملاحظات")]]
    for m in movements:
        data.append([
            ar(m.date.strftime("%Y-%m-%d %H:%M")),
            ar(getattr(m.product, "name", "")),
            ar(m.movement_type),
            ar(m.quantity),
            ar(m.notes),
        ])

    table = Table(data, colWidths=[120, 200, 120, 90, 260], repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "AR"),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2f3b46")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="warehouse_{warehouse.id}_movements.pdf"'
    response.write(pdf)
    return response


from django.contrib.auth.decorators import login_required

import csv

from .models import Product, StockLayer
@login_required
def export_layers_csv(request, product_id: int):
    product = Product.objects.get(pk=product_id)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    filename = f"stock_layers_product_{product_id}_{timezone.now().date()}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(["Layer ID", "Product", "Qty", "Unit Cost", "Remaining", "Created At"])

    layers = StockLayer.objects.filter(product=product).order_by("id")
    for layer in layers:
        writer.writerow([
            layer.id,
            getattr(product, "name", str(product)),
            getattr(layer, "qty", ""),
            getattr(layer, "unit_cost", ""),
            getattr(layer, "remaining", ""),
            getattr(layer, "created_at", ""),
        ])

    return response






from .models import Product, StockMovement

@login_required
def export_movements_csv(request, product_id: int):
    product = Product.objects.get(pk=product_id)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    filename = f"stock_movements_product_{product_id}_{timezone.now().date()}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(["Movement ID", "Product", "Type", "Qty", "Unit Cost", "Reference", "Created At"])

    movements = StockMovement.objects.filter(product=product).order_by("id")
    for m in movements:
        writer.writerow([
            m.id,
            getattr(product, "name", str(product)),
            getattr(m, "movement_type", getattr(m, "type", "")),
            getattr(m, "qty", ""),
            getattr(m, "unit_cost", ""),
            getattr(m, "reference", ""),
            getattr(m, "created_at", ""),
        ])

    return response
