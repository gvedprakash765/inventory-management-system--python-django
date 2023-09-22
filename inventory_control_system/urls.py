
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
    path('datewise_report/', views.datewise_report, name='datewise_report'),
]

