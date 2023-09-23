import datetime
from decimal import Decimal
import json
from django.http import HttpResponse
from django.shortcuts import *
from .forms import * 
from .models import *
from django.http import JsonResponse
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
from django.db import connection

#this is for HomePage
def home(request):
    return render(request,'home.html')

# itemMaster List view
def itemList(request):
    itemList = ItemMaster.objects.all().order_by('id')
    return render(request, 'item_lists.html', {'itemList': itemList})

# itemMaster crud operations start from here
def create_or_update_item(request, action=None, item_id=None):
    form = ItemForm()
    if action == 'save':
        if request.method == 'POST':
            form = ItemForm(request.POST)
            if form.is_valid():
                ItemMaster.objects.create(item_name=request.POST['item_name'],
                                          item_code=request.POST['item_code'],
                                          price=request.POST['price'])
                return redirect('items_list')

    elif action == 'update':
        item = get_object_or_404(ItemMaster, pk=item_id)
        if request.method == 'POST':
            form = ItemForm(request.POST, instance=item)
            if form.is_valid():
                ItemMaster.objects.filter(pk=item_id).update(item_name=request.POST['item_name'],
                                                             item_code=request.POST['item_code'],
                                                             price=request.POST['price'],
                                                             status=request.POST['status'])
                return redirect('items_list')
        return render(request, 'update_item.html', {'form': form, 'action': action, 'item': item})

    elif action == 'delete':
        item = get_object_or_404(ItemMaster, pk=item_id)
        item.delete()
        return redirect('items_list')
    return render(request, 'item_form.html', {'form': form, 'action': action})

# ItemMaster crud end here

# Supplier list view
def supplier_lists(request):
    supplierList = Supplier.objects.all().order_by('id')
    # supplierList=Supplier.objects.filter(status=1).order_by('id')
    return render(request, 'supplier_lists.html', {'supplierList': supplierList})

# Supplier curd operation start from here
def save_update_delete_supplier(request, action, supplier_id=None):
    form = SupplierForm
    if action == 'save':
        if request.method == 'POST':
            form = SupplierForm(request.POST)
            if form.is_valid():
                Supplier.objects.create(supplier_name=request.POST['supplier_name'],
                                        mobile_no=request.POST['mobile_no'],
                                        address=request.POST['address'])
                return redirect('supplier_list')

    elif action == 'update':
        supplier = get_object_or_404(Supplier, pk=supplier_id)
        if request.method == 'POST':
            form = SupplierForm(request.POST, instance=supplier)
            if form.is_valid():
                Supplier.objects.filter(pk=supplier_id).update(supplier_name=request.POST['supplier_name'],
                                                               mobile_no=request.POST['mobile_no'],
                                                               address=request.POST['address'],
                                                               status=request.POST['status'])
                return redirect('supplier_list')
        return render(request, 'supplier_update.html', {'action': action, 'form': form, 'supplier': supplier})
    elif action == 'delete':
        supplier = get_object_or_404(Supplier, pk=supplier_id)
        supplier.delete()
        return redirect('supplier_list')
    return render(request, 'supplier_form.html', {'form': form, 'action': action})
# end of Supplier curd operations

# To auto generate invoice number for purchase
def generate_invoice_number():
    prefix = "SSPL-PURCHASE"  # Replace with your desired prefix
    last_invoice = PurchaseMaster.objects.filter(
        invoice_no__startswith=f"{prefix}-"
    ).order_by('-invoice_no').first()

    if last_invoice is None:
        return f"{prefix}-001"

    last_invoice_number = int(last_invoice.invoice_no.split('-')[2])
    next_invoice_number = last_invoice_number + 1

    return f"{prefix}-{next_invoice_number:03d}"
# lst of auto generate invoice number

# To auto generate invoice number for sale
def generate_invoice_sale():
    prefix = "SSPL-SALE"  # Replace with your desired prefix
    last_invoice = SaleMaster.objects.filter(
        invoice_no__startswith=f"{prefix}-"
    ).order_by('-invoice_no').first()

    if last_invoice is None:
        return f"{prefix}-001"

    last_invoice_number = int(last_invoice.invoice_no.split('-')[2])
    next_invoice_number = last_invoice_number + 1

    return f"{prefix}-{next_invoice_number:03d}"

# fetch particular item price
def get_item_price(request):
    item_id_str = request.GET.get('item')#converting str to int type
    print(item_id_str)
    item_id=int(item_id_str)
    print(type(item_id))
    try:
        item = ItemMaster.objects.get(id=item_id)
        price = item.price
        id = item.id
        data = {'price': price, }
        return JsonResponse(data)
    except ItemMaster.DoesNotExist:
        return JsonResponse({'price': 0})

#for getting particular item quantity stock 
def get_item_details(request):
    if request.method == 'GET':
        item_id_str = request.GET.get('item')

        try:
            item_id = int(item_id_str)  # Convert the item_id_str to an integer
        except (ValueError, TypeError):
            # Handle the case where 'item' is not a valid integer or is None
            return JsonResponse({'error': 'Invalid item ID'}, status=400)

        try:
            # Retrieve the PurchaseDetail object for the selected item
            purchase_detail_list = PurchaseDetail.objects.filter(
                item__id=item_id)
            total_purchase_quantity = 0
            for purchase_details in purchase_detail_list:
                total_purchase_quantity += purchase_details.quantity
                price = purchase_details.price
            print(total_purchase_quantity)

            sale_detail_list=SaleDetails.objects.filter(item__id=item_id)
            total_sale_quantity = 0
            for sale_detail in sale_detail_list:
                total_sale_quantity += sale_detail.qty
            
            total_quantity=total_purchase_quantity-total_sale_quantity
            print(total_quantity)
            sale_price=price+2000

            # Construct a JSON response with the item details
            data = {
                'price': sale_price,
                'quantity': total_quantity,
            }

            return JsonResponse(data)
        except PurchaseDetail.DoesNotExist:
            # Handle the case where the item doesn't exist
            return JsonResponse({'error': 'Item not found'}, status=404)

# code for purchasing items
def purchase_items(request):
    form = PurchaseMasterForm()
    if request.method == 'POST':
        form = PurchaseMasterForm(request.POST)
        if form.is_valid():
            # Generate invoice number
            invoice_no = generate_invoice_number()

            # Get supplier and total amount from the form
            supplier_id = request.POST['supplier']
            # print(supplier_id)
            total_amount = request.POST['total_amount']

            try:
                # save data PurchaseMaster db
                purchase_master = PurchaseMaster.objects.create(
                    invoice_no=invoice_no,
                    total_amount=total_amount,
                    supplier=Supplier.objects.get(id=supplier_id)
                )
                # Parse the JSON item list
                item_list_json = request.POST.get('item_list')
                item_list = json.loads(item_list_json)

                # Create PurchaseDetail objects for each item in the list
                for item_data in item_list:
                    # print(item_data)
                    item_id = item_data['item_id']
                    quantity = item_data['quantity']
                    price = item_data['price']
                    amount = item_data['amount']

                    PurchaseDetail.objects.create(
                        item=ItemMaster.objects.get(id=item_id),
                        quantity=quantity,
                        price=price,
                        amount=amount,
                        purchase_master=purchase_master
                    )
                invoice_no
                purchase_detalis = """
                SELECT
                pm.total_amount AS total_purchase_amount,pm.invoice_date AS invoice_date ,pm.invoice_no AS invlice_no,
                sm.supplier_name AS supplier_name,
                sm.mobile_no,sm.address,im.item_name,pd.quantity,pd.price,pd.amount
                FROM tbl_purchase_mstr AS pm
                JOIN tbl_supplier_mstr AS sm ON pm.supplier_id = sm.id
                JOIN tbl_purchase_details AS pd ON pm.id = pd.purchase_master_id
                JOIN tbl_item_mstr AS im ON pd.item_id = im.id
                WHERE pm.invoice_no = %s;
                """
                with connection.cursor() as cursor:
                    cursor.execute(purchase_detalis, [invoice_no])
                    purchase_result = cursor.fetchall()
                print(type(purchase_result))

                return render(request, 'purchase_details_template.html', {'purchase_details': purchase_result})
            
                return HttpResponse("Purchase saved successfully.")
            except Exception as e:
                return HttpResponse(f"Error: {str(e)}")
    else:
        form = PurchaseMasterForm()
        form1 = PurchaseDetailForm()
        return render(request, 'purchase_item_form.html', {'form': form, 'form1': form1})


def sale_items(request):
    if request.method == 'POST':
        print(request.POST)
        form = SaleDetailsForm(request.POST)
        form1 = SaleMasterForm(request.POST)
        print('hello')

        if form1.is_valid():
            print('is valid')
            # customer_name = request.POST['customer_name']
            # number = request.POST['number']
            # total_amount = request.POST['total_amount']
            print('save')

            saleMaster = SaleMaster.objects.create(
                invoice_no=generate_invoice_sale(),
                customer_name=request.POST['customer_name'],
                number=request.POST['number'],
                total_amount=request.POST['total_amount'],
                
            )

            item_list_json = request.POST.get('item_list')
            item_list = json.loads(item_list_json)

            for item_data in item_list:
                item_id = item_data['item_id']
                qty = item_data['quantity']
                price = item_data['price']
                amount = item_data['amount']

                SaleDetails.objects.create(
                    item=ItemMaster.objects.get(id=item_id),
                    qty=qty,
                    price=price,
                    amount=amount,
                    sale_mstr=saleMaster
                )

            return HttpResponse("Sale done")
    else:
        form = SaleDetailsForm()
        form1 = SaleMasterForm()
    return render(request, 'sale_items_form.html', {'form': form, 'form1': form1})


def datewise_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    # Define the SQL queries
    purchase_query = """
        SELECT
            im.item_name,
            SUM(pd.quantity) AS purchase_quantity,
            SUM(pm.total_amount) AS purchase_amount
        FROM tbl_purchase_mstr AS pm
        JOIN tbl_purchase_details AS pd ON pm.id = pd.purchase_master_id
        JOIN tbl_item_mstr AS im ON pd.item_id = im.id
        WHERE
            pm.invoice_date BETWEEN %s AND %s
        GROUP BY
            im.item_name;
    """

    sale_query = """
        SELECT
            im.item_name,
            SUM(sd.qty) AS sale_quantity,
            SUM(sm.total_amount) AS sale_amount
        FROM tbl_sale_mstr AS sm
        JOIN tbl_sale_details AS sd ON sm.id = sd.sale_mstr_id
        JOIN tbl_item_mstr AS im ON sd.item_id = im.id
        WHERE
            sm.invoice_date BETWEEN %s AND %s
        GROUP BY
            im.item_name;
    """

    # Execute the purchase SQL query
    with connection.cursor() as cursor:
        cursor.execute(purchase_query, [start_date, end_date])
        purchase_result = cursor.fetchall()

    # Execute the sale SQL query
    with connection.cursor() as cursor:
        cursor.execute(sale_query, [start_date, end_date])
        sale_result = cursor.fetchall()

    # Process the purchase result
    purchase_data = [{'item_name': row[0], 'purchase_quantity': row[1],
                       'purchase_amount': row[2]} for row in purchase_result]
    print(purchase_data)
    
    # Process the sale result
    sale_data = [{'item_name': row[0], 'sale_quantity': row[1], 'sale_amount': row[2]} for row in sale_result]
    print(sale_data)

    datewise_report_data = {}
    for purchase_entry in purchase_data:
        item_name = purchase_entry['item_name']
        purchase_quantity = purchase_entry['purchase_quantity']
        purchase_amount = purchase_entry['purchase_amount']
        if item_name not in datewise_report_data:
            datewise_report_data[item_name] = {'purchase_quantity': 0, 'purchase_amount': Decimal('0.00'),
                                               'sale_quantity': 0, 'sale_amount': Decimal('0.00')}
        datewise_report_data[item_name]['purchase_quantity'] += purchase_quantity
        datewise_report_data[item_name]['purchase_amount'] += purchase_amount

    for sale_entry in sale_data:
        item_name = sale_entry['item_name']
        sale_quantity = sale_entry['sale_quantity']
        sale_amount = sale_entry['sale_amount']
        if item_name not in datewise_report_data:
            datewise_report_data[item_name] = {'purchase_quantity': 0, 'purchase_amount': Decimal('0.00'),
                                               'sale_quantity': 0, 'sale_amount': Decimal('0.00')}
        datewise_report_data[item_name]['sale_quantity'] += sale_quantity
        datewise_report_data[item_name]['sale_amount'] += sale_amount

    # Calculate stock quantity and profit/loss
    for item_name, data in datewise_report_data.items():
        data['stock_quantity'] = data['purchase_quantity'] - data['sale_quantity']
        data['profit_loss'] = data['sale_amount'] - data['purchase_amount']

    return render(request, 'date_wise_report.html', {'datewise_report_data': datewise_report_data})
