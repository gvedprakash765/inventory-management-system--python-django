from django.db import models

# Create your models here.
class ItemMaster(models.Model):
    id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=20, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(default=1)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta():
        db_table ='tbl_item_mstr'
    def __str__(self):
        return self.item_name
    
class Supplier(models.Model):
    id = models.AutoField(primary_key=True)
    supplier_name = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=10)  # Assuming mobile numbers as strings
    address = models.CharField(max_length=10)
    datetime = models.DateTimeField(auto_now_add=True)  # Date and time when the record was created
    status = models.CharField(default=1)

    class Meta():
        db_table='tbl_supplier_mstr'

    def __str__(self):
        return self.supplier_name


class PurchaseMaster(models.Model):
    invoice_no = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=1)

    class Meta():
        db_table='tbl_purchase_mstr'

    # def __str__(self):
    #     return self.invoice_no
    

class PurchaseDetail(models.Model):
    item = models.ForeignKey(ItemMaster, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_master = models.ForeignKey(PurchaseMaster, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=1)  # You can use choices for status values

    class Meta():
        db_table='tbl_purchase_details'
    

    # def __str__(self):
    #     return f"{self.item.id} - {self.purchase_master.invoice_no}" 

class SaleMaster(models.Model):
    id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=255)
    number = models.CharField(max_length=10)
    invoice_no = models.CharField(max_length=20, unique=True)
    invoice_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=1)

    class Meta():
        db_table='tbl_sale_mstr'
    # def __str__(self):
    #     return self.invoice_no

class SaleDetails(models.Model):
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE)
    qty = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sale_mstr = models.ForeignKey(SaleMaster, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=1)

    class Meta():
        db_table='tbl_sale_details'
