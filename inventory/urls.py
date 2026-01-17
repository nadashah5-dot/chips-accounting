from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path('', views.inventory_home, name='inventory_home'),

    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),

   # inventory/urls.py
    path("products/export/csv/", views.export_products_csv, name="export_products_csv"),
    path("products/export/excel/", views.export_products_excel, name="export_products_excel"),
    path("products/export/pdf/", views.export_products_pdf, name="export_products_pdf"),
    


    path('export_all_warehouses/', views.export_all_warehouses, name='export_all_warehouses'),

    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/add/', views.warehouse_add, name='warehouse_add'),
    path('warehouses/<int:pk>/edit/', views.warehouse_edit, name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', views.warehouse_delete, name='warehouse_delete'),
    path('warehouses/<int:pk>/', views.warehouse_detail, name='warehouse_detail'),
    path('warehouses/<int:pk>/transfer/', views.warehouse_transfer, name='warehouse_transfer'),
    path('warehouses/<int:pk>/movements/export/pdf/', views.export_warehouse_movements_pdf, name='export_warehouse_movements_pdf'),
   
    path('warehouses/<int:pk>/movement/add/', views.warehouse_movement_add, name='warehouse_movement_add'),
    path('warehouses/<int:pk>/stock/add/', views.warehouse_stock_add, name='warehouse_stock_add'),
    path('warehouses/stock/<int:pk>/edit/', views.warehouse_stock_edit, name='warehouse_stock_edit'),
    path('warehouses/stock/<int:pk>/delete/', views.warehouse_stock_delete, name='warehouse_stock_delete'),
    path('warehouses/<int:pk>/remove/', views.warehouse_stock_remove, name='warehouse_stock_remove'),

    path('warehouses/<int:pk>/export/csv/', views.export_warehouse_csv, name='export_warehouse_csv'),
    path('warehouses/<int:pk>/export/excel/', views.export_warehouse_excel, name='export_warehouse_excel'),
    path('warehouses/<int:pk>/export/pdf/', views.export_warehouse_pdf, name='export_warehouse_pdf'),

    path('export_all_warehouses/csv/', views.export_all_warehouses_csv, name='export_all_warehouses_csv'),
    path('export_all_warehouses/excel/', views.export_all_warehouses_excel, name='export_all_warehouses_excel'),
    path('export_all_warehouses/pdf/', views.export_all_warehouses_pdf, name='export_all_warehouses_pdf'),
    path("products/<int:product_id>/layers/export/csv/", views.export_layers_csv, name="export_layers_csv"),
    path("product/<int:product_id>/movements/export/csv/", views.export_movements_csv, name="export_movements_csv"),




   
]
