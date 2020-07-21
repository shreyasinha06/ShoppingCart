from django.http import HttpResponse
from django.shortcuts import render
from .models import Product,Contact,Orders,OrderUpdate
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from paytm import checksum
MERCHANT_KEY= 'kbzk1DSbJiV_O3p5'

def index(request):

    allProds=[]
    catprods=Product.objects.values('category','id')
    cats={item['category'] for item in catprods}
    for cat in cats:
        prod=Product.objects.filter(category=cat)
        n=len(prod)
        nSlides = n // 4 + ceil((n / 4) + (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])

    params={'allProds':allProds}
    return render(request,'shop/index.html',params)
def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False


def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]

        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
           allProds.append([prod, range(1, nSlides), nSlides])


    params = {'allProds': allProds,"msg":""}

    if len(allProds) == 0 or len(query) < 4:
        params = {'msg': "Please make sure to enter relevant search query"}
    return render(request, 'shop/search.html', params)


def tracker(request):

 if request.method == "POST":
    orderId = request.POST.get('orderId', '')
    email = request.POST.get('email', '')

    try:
        order = Orders.objects.filter(order_id=orderId, email=email)
        if len(order) > 0:
            update = OrderUpdate.objects.filter(order_id=orderId)
            updates = []
            for item in update:
                updates.append({'text': item.update_desc, 'time': item.timestamp})
                response = json.dumps({"status":"success","updates": updates,"itemsJson":order[0].items_json}, default=str)
            return HttpResponse(response)
        else:
            return HttpResponse('{"status":"no item"}')
    except Exception as e:
        return HttpResponse('{"status":"error"}')
 return render(request,'shop/tracker.html')
def aboutUs(request):
    return render(request,'shop/aboutUs.html')
def contact(request):
    thank = False
    if request.method=="POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        thank=True
        print(name, email, phone, desc)
    return render(request, 'shop/contact.html',{'thank':thank})
def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        amount = request.POST.get('amount', '')
        zip_code = request.POST.get('zip_code', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')

        order = Orders(items_json=items_json, name=name, email=email, phone=phone, address=address,amount=amount, zip_code=zip_code,state=state,city=city)
        order.save()
        thank = True
        id = order.order_id
        update=OrderUpdate(order_id=order.order_id,update_desc="order has been placed")
        update.save()
        #return render(request, 'shop/checkout.html',{'thank':thank,'id':id})
        param_dict = {

            'MID': 'WorldP64425807474247',
            'ORDER_ID': str(order.order_id),
            'TXN_AMOUNT': str(amount),
            'CUST_ID': email,
            'INDUSTRY_TYPE_ID': 'Retail',
            'WEBSITE': 'WEBSTAGING',
            'CHANNEL_ID': 'WEB',
            'CALLBACK_URL': 'http://127.0.0.1:8000/shop/handlerequest/',

        }
        param_dict['CHECKSUMHASH'] = checksum.generate_checksum(param_dict, MERCHANT_KEY)
        return render(request, 'shop/paytm.html', {'param_dict': param_dict})

    return render(request, 'shop/checkout.html')
    return render(request, 'shop/checkout.html')
def prov(request,id):
    print(Product.objects.all())
    product = Product.objects.filter(id=id)

    return render(request,'shop/prodview.html',{'product':product[0]})
@csrf_exempt
def handleRequest(request):
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum1 = form[i]

    verify = checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum1)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print('order successful')
        else:
            print('order was not successful because' + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})
