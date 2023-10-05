from decimal import Decimal
import json
from django.http import HttpResponse, HttpResponseBadRequest
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
            print(sale_price)

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
            print(request.POST)
            invoice_no = request.POST['invoice_no'] 
            invoice_date = request.POST['invoice_date'] 

            # Get supplier and total amount from the form
            supplier_id = request.POST['supplier'] 
            # print(supplier_id)
            total_amount = request.POST['total_amount']

            try:
                # save data PurchaseMaster db
                purchase_master = PurchaseMaster.objects.create(
                    invoice_no=invoice_no,
                    invoice_date=invoice_date,
                    total_amount=total_amount,
                    supplier=Supplier.objects.get(id=supplier_id)
                )
                print(purchase_master)
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
        if form1.is_valid():
            invoice_no=generate_invoice_sale()
            invoice_date= request.POST['invoice_date']
            

            saleMaster = SaleMaster.objects.create(
                invoice_no=invoice_no,
                invoice_date=invoice_date,
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
            invoice_no
            sale_details="""
                            SELECT 
                    sm.total_amount AS total_sale_amount,
                    sm.invoice_date AS invoice_date,
                    sm.invoice_no AS invoice_no,
                    sm.customer_name AS customerr_name,
                    sm.number,
                    im.item_name,
                    sd.qty,
                    sd.price,
                    sd.amount
                FROM tbl_sale_mstr AS sm
                JOIN tbl_sale_details AS sd ON sm.id = sd.sale_mstr_id
                JOIN tbl_item_mstr AS im ON sd.item_id = im.id
                WHERE sm.invoice_no = %s;
            """
            with connection.cursor() as cursor:
                    cursor.execute(sale_details, [invoice_no])
                    sale_result = cursor.fetchall()
            print(type(sale_result))
            return render(request, 'sale_details_template.html', {'sale_details': sale_result})
            return HttpResponse("Sale done")
    else:
        form = SaleDetailsForm()
        form1 = SaleMasterForm()
    return render(request, 'sale_items_form.html', {'form': form, 'form1': form1})

def purchase_records(request):
    if request.method == 'GET':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        # Define the SQL query to fetch distinct purchase records between two dates
        sql_query = """
            SELECT DISTINCT
                pm.invoice_date AS invoice_date,
                pm.invoice_no AS invoice_no,
                pm.total_amount AS total_amount,
                sm.supplier_name AS supplier_name,
                pm.id AS purchase_master_id
            FROM tbl_purchase_mstr AS pm
            JOIN tbl_supplier_mstr AS sm ON pm.supplier_id = sm.id
            JOIN tbl_purchase_details AS pd ON pm.id = pd.purchase_master_id
            WHERE pm.invoice_date BETWEEN %s AND %s;
        """

        # Execute the SQL query with the date range
        with connection.cursor() as cursor:
            cursor.execute(sql_query, [start_date, end_date])
            distinct_purchase_records = cursor.fetchall()
        print(distinct_purchase_records)

        context = {
            'start_date': start_date,
            'end_date': end_date,
            'distinct_purchase_records': distinct_purchase_records,  
        }
        return render(request, 'purchase_records_by_date.html', context)
    else:
        return HttpResponseBadRequest("Invalid HTTP method. Please use GET.")


def view_item_details(request, purchase_id):
    sql_query = """
        SELECT
            pm.invoice_no AS invoice_no,
            pm.invoice_date AS invoice_date,
            sm.supplier_name AS supplier_name,
            im.item_name AS item_name,
            pd.price AS price,
            pd.quantity AS quantity,
            pd.amount AS amount
        FROM
            tbl_purchase_mstr AS pm
        JOIN
            tbl_supplier_mstr AS sm ON pm.supplier_id = sm.id
        JOIN
            tbl_purchase_details AS pd ON pm.id = pd.purchase_master_id
        JOIN
            tbl_item_mstr AS im ON pd.item_id = im.id
        WHERE
            pd.purchase_master_id = %s;
    """
    # Execute the SQL query with the provided purchase_id
    with connection.cursor() as cursor:
        cursor.execute(sql_query, [purchase_id])
        item_details = cursor.fetchall()

    # Calculate the total amount for the purchase
    total_amount = sum(item[6] for item in item_details) 
    total_qty = sum(item[5] for item in item_details)  

    context = {
        'item_details': item_details,
        'total_amount': total_amount,
    }
    print('hello')
    print(type(item_details))
    print(total_amount)
    print(total_qty)

    # Render the item_details.html template with the context data
    return render(request, 'purchase_item_details.html', context)

def sale_records_within_date_range(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Define the SQL query to retrieve records within the date range
    sql_query = """
        SELECT DISTINCT
                sm.invoice_date AS invoice_date ,sm.invoice_no AS invoice_no,
                sm.total_amount AS total_amount,
                sm.customer_name AS customer_name,
				sm.number AS customer_number,
                sm.id AS sale_mstr_id
                FROM tbl_sale_mstr AS sm
                JOIN tbl_sale_details AS sd ON sm.id = sd.sale_mstr_id
                WHERE sm.invoice_date between %s and %s
        
    """

    # Execute the SQL query with the provided date range
    with connection.cursor() as cursor:
        cursor.execute(sql_query, [start_date, end_date])
        records = cursor.fetchall()

    context = {
        'records': records,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'sale_records_within_date_range.html', context)

def view_sale_item_details(request, sale_id):
    # Get the purchase record using purchase_id
    sql_query = """
        SELECT
             sm.invoice_date AS invoice_date,
                sm.invoice_no AS invoice_no,
                sm.customer_name AS customer_name,
                sm.number AS customer_number,
                sd.amount AS amount,
                sd.price AS price,
                sd.qty AS quantity,
                im.item_name AS item_name
            FROM
                tbl_sale_mstr AS sm
            JOIN
                tbl_sale_details AS sd ON sm.id = sd.sale_mstr_id
            JOIN
                tbl_item_mstr AS im ON sd.item_id = im.id
            WHERE
            sd.sale_mstr_id = %s;
                """
    # Execute the SQL query with the provided purchase_id
    with connection.cursor() as cursor:
        cursor.execute(sql_query, [sale_id])
        sale_item_details = cursor.fetchall()

    # Calculate the total amount for the purchase
    total_amount = sum(item[4] for item in sale_item_details)  # Sum of amounts in the result

    context = {
        'item_details': sale_item_details,
        'total_amount': total_amount,
    }
    print(sale_item_details)
    print(total_amount)

    # Render the item_details.html template with the context data
    return render(request, 'sale_item_details.html', context)

def date_wise_item_report(request):
    start_date = None
    end_date = None

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        # Validate that both start_date and end_date are provided
        if not start_date or not end_date:
            return HttpResponse("Please select both start date and end date.")

    with connection.cursor() as cursor:
        # Get a list of unique dates from both purchase and sale data
        cursor.execute("""
            SELECT DISTINCT pm.invoice_date
            FROM tbl_purchase_mstr AS pm
            WHERE pm.invoice_date BETWEEN %s AND %s
        """, [start_date, end_date])
        purchase_dates = [date[0] for date in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT sm.invoice_date
            FROM tbl_sale_mstr AS sm
            WHERE sm.invoice_date BETWEEN %s AND %s
        """, [start_date, end_date])
        sale_dates = [date[0] for date in cursor.fetchall()]

        # Combine the unique dates
        unique_dates = set(purchase_dates + sale_dates)
        report_data = []
        for date in unique_dates:
            cursor.execute("""
                SELECT 
                    pd.amount AS purchase_amount, pd.quantity AS purchase_quantity,
                    im.item_name AS item_name
                FROM tbl_item_mstr AS im 
                JOIN tbl_purchase_details AS pd ON im.id = pd.item_id
                JOIN tbl_purchase_mstr AS pm ON pm.id = pd.purchase_master_id
                WHERE pm.invoice_date = %s Order by pm.invoice_date asc
            """, [date])
            purchase_data = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    sd.amount AS sale_amount, sd.qty AS sale_quantity,
                    im.item_name AS item_name
                FROM tbl_item_mstr AS im 
                JOIN tbl_sale_details AS sd ON im.id = sd.item_id
                JOIN tbl_sale_mstr AS sm ON sm.id = sd.sale_mstr_id
                WHERE sm.invoice_date = %s  Order by sm.invoice_date asc
            """, [date])
            sale_data = cursor.fetchall()

            # Create a dictionary to store summed values for each item
            item_totals = {}

            # Iterate through the purchase data for the current date
            for purchase_item in purchase_data:
                item_name = purchase_item[2]
                purchase_quantity = purchase_item[1]
                purchase_amount = purchase_item[0]

                if item_name not in item_totals:
                    item_totals[item_name] = {
                        'date': date,
                        'item_name': item_name,
                        'purchase_quantity': purchase_quantity,
                        'purchase_amount': purchase_amount,
                        'sale_quantity': 0,
                        'sale_amount': 0,
                    }
                else:
                    item_totals[item_name]['purchase_quantity'] += purchase_quantity
                    item_totals[item_name]['purchase_amount'] += purchase_amount

            # Iterate through the sale data for the current date
            for sale_item in sale_data:
                item_name = sale_item[2]
                sale_quantity = sale_item[1]
                sale_amount = sale_item[0]

                if item_name not in item_totals:
                    item_totals[item_name] = {
                        'date': date,
                        'item_name': item_name,
                        'purchase_quantity': 0,
                        'purchase_amount': 0,
                        'sale_quantity': sale_quantity,
                        'sale_amount': sale_amount,
                    }
                else:
                    item_totals[item_name]['sale_quantity'] += sale_quantity
                    item_totals[item_name]['sale_amount'] += sale_amount

            # Calculate profit for each item and add it to the report data
            for item_name, item_data in item_totals.items():
                purchase_amount = item_data['purchase_amount']
                sale_amount = item_data['sale_amount']
                profit = sale_amount - purchase_amount
                item_data['profit'] = profit
                report_data.append(item_data)

    context = {
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'date_wise_item_report.html', context)

def profit_loss_report(request):
    # Retrieve all sales and purchase data
    sales = SaleMaster.objects.all()
    purchases = PurchaseMaster.objects.all()

    # Calculate total revenue
    total_sale_amount = sum(sale.total_amount for sale in sales)

    # Calculate total expenses
    total_purchase_amount = sum(purchase.total_amount for purchase in purchases)

    # Calculate profit or loss
    profit_or_loss = total_sale_amount - total_purchase_amount
    

    context = {
        'total_sale_amount': total_sale_amount,
        'total_purchase_amount': total_purchase_amount,
        'profit_or_loss': profit_or_loss,
    }

    return render(request, 'profit_loss_report.html', context)


def date_wise_profit_loss_report(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Query the database to calculate total sale and purchase amounts
        total_sale_amount = SaleMaster.objects.filter(date__range=[start_date, end_date]).aggregate(
            total_sale_amount=models.Sum('amount'))['total_sale_amount'] or 0
        total_purchase_amount = PurchaseMaster.objects.filter(date__range=[start_date, end_date]).aggregate(
            total_purchase_amount=models.Sum('amount'))['total_purchase_amount'] or 0

        profit_or_loss = total_sale_amount - total_purchase_amount

        context = {
            'total_sale_amount': total_sale_amount,
            'total_purchase_amount': total_purchase_amount,
            'profit_or_loss': profit_or_loss,
        }

        return render(request, 'date_wise_profit_loss_report.html', context)

    return render(request, 'date_wise_profit_loss_report.html')


#stock report item wise
# def item_stock_report(request):
#     if request.method == 'GET':
#         # Fetch item names from the database
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT item_name FROM tbl_item_mstr;")
#             item_names = [row[0] for row in cursor.fetchall()]

#         # Get the selected item name from the form
#         item_name = request.GET.get('item_name', item_names[0] if item_names else '')  # Default to the first item if available

#         # Fetch stock data for the selected item name
#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 WITH sales_data AS (
#                     SELECT
#                         sd.item_id,
#                         SUM(sd.qty) AS sale_quantity
#                     FROM tbl_sale_details AS sd
#                     GROUP BY sd.item_id
#                 ),
#                 purchase_data AS (
#                     SELECT
#                         pd.item_id,
#                         SUM(pd.quantity) AS purchase_quantity
#                     FROM tbl_purchase_details AS pd
#                     GROUP BY pd.item_id
#                 ),
#                 item_master AS (
#                     SELECT
#                         im.id AS item_id,
#                         im.item_name
#                     FROM tbl_item_mstr AS im
#                 )
#                 SELECT
#                     item_master.item_name,
#                     COALESCE(purchase_quantity, 0) AS purchase_quantity,
#                     COALESCE(sale_quantity, 0) AS sale_quantity,
#                     (COALESCE(purchase_quantity, 0) - COALESCE(sale_quantity, 0)) AS stock
#                 FROM item_master
#                 LEFT JOIN purchase_data ON item_master.item_id = purchase_data.item_id
#                 LEFT JOIN sales_data ON item_master.item_id = sales_data.item_id
#                 WHERE item_name = %s
#                 ORDER BY item_master.item_name;
#             """, [item_name])
#             stock_data = cursor.fetchall()

#         context = {
#             'item_names': item_names,
#             'item_name': item_name,
#             'stock_data': stock_data,
#         }
#         return render(request, 'stock_item_report.html', context)
#     else:
#         return HttpResponseBadRequest("NOT FOUND")


def item_stock_report(request):
    if request.method == 'GET':
        # Fetch item names from the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT item_name FROM tbl_item_mstr;")
            item_names = [row[0] for row in cursor.fetchall()]

        # Get the selected item name from the form
        item_name = request.GET.get('item_name', item_names[0] if item_names else '')
          # Default to the first item if available
        if not item_name:
            return HttpResponse("<h1>Please select an item.</h1>")

        # Fetch stock data
        with connection.cursor() as cursor:
            if item_name == "All Items":
                # Query to fetch stock data for all items
                cursor.execute("""
                    WITH sales_data AS (
                    SELECT
                        sd.item_id,
                        SUM(sd.qty) AS sale_quantity
                    FROM tbl_sale_details AS sd
                    GROUP BY sd.item_id
                ),
                purchase_data AS (
                    SELECT
                        pd.item_id,
                        SUM(pd.quantity) AS purchase_quantity
                    FROM tbl_purchase_details AS pd
                    GROUP BY pd.item_id
                ),
                item_master AS (
                    SELECT
                        im.id AS item_id,
                        im.item_name
                    FROM tbl_item_mstr AS im
                )
                SELECT
                    item_master.item_name,
                    COALESCE(purchase_quantity, 0) AS purchase_quantity,
                    COALESCE(sale_quantity, 0) AS sale_quantity,
                    (COALESCE(purchase_quantity, 0) - COALESCE(sale_quantity, 0)) AS stock
                FROM item_master
                LEFT JOIN purchase_data ON item_master.item_id = purchase_data.item_id
                LEFT JOIN sales_data ON item_master.item_id = sales_data.item_id
                ORDER BY item_master.item_name;
                """)
            else:
                # Query to fetch stock data for a specific item
                cursor.execute("""
                    WITH sales_data AS (
                    SELECT
                        sd.item_id,
                        SUM(sd.qty) AS sale_quantity
                    FROM tbl_sale_details AS sd
                    GROUP BY sd.item_id
                ),
                purchase_data AS (
                    SELECT
                        pd.item_id,
                        SUM(pd.quantity) AS purchase_quantity
                    FROM tbl_purchase_details AS pd
                    GROUP BY pd.item_id
                ),
                item_master AS (
                    SELECT
                        im.id AS item_id,
                        im.item_name
                    FROM tbl_item_mstr AS im
                )
                SELECT
                    item_master.item_name,
                    COALESCE(purchase_quantity, 0) AS purchase_quantity,
                    COALESCE(sale_quantity, 0) AS sale_quantity,
                    (COALESCE(purchase_quantity, 0) - COALESCE(sale_quantity, 0)) AS stock
                FROM item_master
                LEFT JOIN purchase_data ON item_master.item_id = purchase_data.item_id
                LEFT JOIN sales_data ON item_master.item_id = sales_data.item_id
                WHERE item_name = %s
                ORDER BY item_master.item_name;
                """, [item_name])
                
            stock_data = cursor.fetchall()

        context = {
            'item_names': item_names,
            'item_name': item_name,
            'stock_data': stock_data,
        }
        return render(request, 'stock_item_report.html', context)
    else:
        return HttpResponseBadRequest("NOT FOUND")

    
#All items Stcok report
def all_item_stock_report(request):
    if request.method == 'GET':
        # Fetch item names from the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT item_name FROM tbl_item_mstr;")
            item_names = [row[0] for row in cursor.fetchall()]

        # Get the selected item name from the form
        item_name = request.GET.get('item_name', item_names[0] if item_names else '')
        print(item_name)
          # Default to the first item if available

        # Rest of your code for fetching stock data remains the same
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH sales_data AS (
                    SELECT
                        sd.item_id,
                        SUM(sd.qty) AS sale_quantity
                    FROM tbl_sale_details AS sd
                    GROUP BY sd.item_id
                ),
                purchase_data AS (
                    SELECT
                        pd.item_id,
                        SUM(pd.quantity) AS purchase_quantity
                    FROM tbl_purchase_details AS pd
                    GROUP BY pd.item_id
                ),
                item_master AS (
                    SELECT
                        im.id AS item_id,
                        im.item_name
                    FROM tbl_item_mstr AS im
                )
                SELECT
                    item_master.item_name,
                    COALESCE(purchase_quantity, 0) AS purchase_quantity,
                    COALESCE(sale_quantity, 0) AS sale_quantity,
                    (COALESCE(purchase_quantity, 0) - COALESCE(sale_quantity, 0)) AS stock
                FROM item_master
                LEFT JOIN purchase_data ON item_master.item_id = purchase_data.item_id
                LEFT JOIN sales_data ON item_master.item_id = sales_data.item_id
                ORDER BY item_master.item_name;
            """)
            stock_data = cursor.fetchall()

        context = {
            'item_names': item_names,
            'item_name': item_name,
            'stock_data': stock_data,
        }
        return render(request, 'all_item_stock_report.html', context)
    else:
        return HttpResponseBadRequest("NOT FOUND")

#date profit sale
def invoice_report(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if not start_date or not end_date:
            return HttpResponseBadRequest("Please provide both start and end dates.")

        with connection.cursor() as cursor:
            cursor.execute("""
                WITH sales_data AS (
                    SELECT
                        DATE(invoice_date) AS transaction_date,
                        SUM(total_amount) AS sale_amount
                    FROM tbl_sale_mstr
                    WHERE DATE(invoice_date) BETWEEN %s AND %s
                    GROUP BY DATE(invoice_date)
                ),
                purchase_data AS (
                    SELECT
                        DATE(invoice_date) AS transaction_date,
                        SUM(total_amount) AS purchase_amount
                    FROM tbl_purchase_mstr
                    WHERE DATE(invoice_date) BETWEEN %s AND %s
                    GROUP BY DATE(invoice_date)
                )
                SELECT
                    COALESCE(sales_data.transaction_date, purchase_data.transaction_date) AS transaction_date,
                    COALESCE(sale_amount, 0) AS sale_amount,
                    COALESCE(purchase_amount, 0) AS purchase_amount,
                    (COALESCE(sale_amount, 0) - COALESCE(purchase_amount, 0)) AS profit_or_loss
                FROM sales_data
                FULL OUTER JOIN purchase_data
                ON sales_data.transaction_date = purchase_data.transaction_date
                ORDER BY COALESCE(sales_data.transaction_date, purchase_data.transaction_date);
            """, [start_date, end_date, start_date, end_date])
            result = cursor.fetchall()
        print(type(result))
        print(result)

        # Calculate the sum of sale amount, purchase amount, and profit/loss
        sum_sale_amount = sum(row[1] for row in result)
        sum_purchase_amount = sum(row[2] for row in result)
        sum_profit_loss = sum(row[3] for row in result)

        context = {
            'start_date':start_date,
            'end_date':end_date,
            'report_data': result,
            'sum_sale_amount': sum_sale_amount,
            'sum_purchase_amount': sum_purchase_amount,
            'sum_profit_loss': sum_profit_loss,
        }
        return render(request, 'invoice_report.html', context)

    return render(request, 'invoice_report.html')
