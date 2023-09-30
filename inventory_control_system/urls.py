
from django.urls import path, re_path
from .views import *
from . import views

urlpatterns = [
    path('',views.home,name='home_page' ),
    path('item/list/',views.itemList,name='items_list' ),
    re_path(r'^item/(?P<action>\w+)/(?P<item_id>(.*)+|)$', views.create_or_update_item, name='item_from'),
    path('supplier/list/',views.supplier_lists,name='supplier_list'),
    re_path(r'^supplier/(?P<action>\w+)/(?P<supplier_id>(.*)+|)$', views.save_update_delete_supplier, name='supp_all'),
    path('purchase-items/', views.purchase_items, name='purchase_items'),
    path('sale-items/', views.sale_items, name='sale_items'),
    path('get_item_price/', views.get_item_price, name='get_item_price'),
    path('get_item_details/', views.get_item_details, name='get_item_details'),
    # path('datewise_report/', views.datewise_report, name='datewise_report'),
    # path('item-wise-_stock_report/', views.item_wise_report, name='item_wise_report'),
    re_path(r'^purchase_records/(?P<selected_date>\d{4}-\d{2}-\d{2})/(?P<purchase_id>\d+)/$', 
             views.purchase_records, name='purchase_records'),  
    path('purchase_records/', views.purchase_records, name='purchase_records'),
    path('view_item_details/<int:purchase_id>/', views.view_item_details, name='view_item_details'),
    path('view_sale_item_details/<int:sale_id>/', views.view_sale_item_details, name='view_sale_item_details'),
    path('sale_records/', views.sale_records_within_date_range, name='sale-records'),
    path('date-wise-item-report/', views.date_wise_item_report, name='date_wise_item_report'),
    path('profit-loss/', views.profit_loss_report, name='profit_loss_report'),
    path('date_wise_profit-loss-report/', views.date_wise_profit_loss_report, name='date_wise_profit_loss_report'),
    path('item_stock_report/', views.item_stock_report,name='item_stock_report'),
    path('all_item_stock_report/', views.all_item_stock_report,name='all_item_stock_report'),
    path('invoice-report/', views.invoice_report, name='invoice_report'),




]

