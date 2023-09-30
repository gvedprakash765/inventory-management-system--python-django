
import json
from django import forms
from .models import *

class ItemForm(forms.ModelForm):
    class Meta:
        model=ItemMaster
        fields=['item_name','item_code','price']

class SupplierForm(forms.ModelForm):
    class Meta:
        model=Supplier
        fields=['supplier_name','mobile_no','address']

class PurchaseMasterForm(forms.ModelForm):
    forms.ModelChoiceField(queryset=Supplier.objects.all(), empty_label='Select Supplier')
    class Meta:
        model=PurchaseMaster
        fields=['supplier','invoice_no','invoice_date','total_amount']
   
class PurchaseDetailForm(forms.ModelForm):
    forms.ModelChoiceField(queryset=ItemMaster.objects.all(),empty_label='select item')

    class Meta:
        model=PurchaseDetail
        fields=['item','quantity','amount','price']

class SaleMasterForm(forms.ModelForm):
    class Meta:
        model=SaleMaster
        fields=['customer_name','number','invoice_date','total_amount']

class SaleDetailsForm(forms.ModelForm):
    forms.ModelChoiceField(queryset=ItemMaster.objects.all(), empty_label='Select Item')
    class Meta:
        model=SaleDetails
        fields=['item','qty','price','amount']

