from http.client import REQUEST_ENTITY_TOO_LARGE
from multiprocessing import context
from telnetlib import STATUS
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
import requests
from django.core.paginator import Paginator

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate , login
# from django.contrib.messages import constants as messages
from django.contrib import messages
from datetime import date, datetime, timezone
import json
import os
from .utils import *
from dncctaxpay.models import Transaction, User
from django.db.models import Sum
from django.conf import settings

url = settings.API_URL

  
MESSAGE_TAGS = {
        messages.DEBUG: 'alert-secondary',
        messages.INFO: 'alert-info',
        messages.SUCCESS: 'alert-success',
        messages.WARNING: 'alert-warning',
        messages.ERROR: 'alert-danger',
 }


def index(request):
    
    if "User_Email" in request.session :
        # print(datetime.now())
        context=getUser(request.session["User_Email"])
        return render(request,"home.html",  context=context)
    else:
       return redirect('login')







def taxValidation(request):

    context ={}
  
    if "User_Email" in request.session :
        if(request.method == 'GET'):
            return redirect('landing')
        if(request.method=="POST"):

            data1 = {}
            # data1["USERID"] = "50154800"
            # data1["POLICY"] = request.POST["policynum"]
            data1["taxno"] = request.POST["taxno"]
            data1["qtr"] = request.POST["qtr"]
            data1["frm"] = settings.API_USERNAME
            response=requests.get(url + "holding_data_chk_ver6.aspx",data = data1).text


            # trnidgen = 'MBL-DNCC-TAX-' + str(data1["taxno"]) + str(data1["qtr"])
            resp = response.split('|')

            # ss = 'alert-success alert-dismissable'
            
            # Invalid Details / Amount
            # Already Paid

            # STATUS 0
            # Description 1
            # Amount 2
            # Name 3
            # Address 4
            # Address 5
            # Address 6
            # Row No 7



            if(resp[1]=='Invalid Details / Amount'):
                messages.error(request,"Invalid Details provided please check and submit again. ")

                context["message"] = "Please enter a date in order for searching."
                context['classes'] = 'alert alert-danger alert-dismissable'
                return redirect('landing')

            elif(resp[1]=='Already Paid'):
                messages.info(request,  "Payment Complete already. " ) 

                context["message"] = "Please enter a date in order for searching."
                context['classes'] = 'alert alert-danger alert-dismissable'
                return redirect('landing')

            else:
                if(resp[0]=='00'):
                    messages.success(request, resp[1])
                    try:
                        newtxn = Transaction.objects.get(tax_no =data1["taxno"], qtr=data1["qtr"] )
                        user = User.objects.get(email=request.session["User_Email"])
                        newtxn.rowNo = resp[7]
                        newtxn.input_user= user
                        newtxn.branch = user.branchname
                        newtxn.save()
                        return redirect('confirmation', txn = newtxn.txnId)
                    except Exception as e:
                        newtxn = Transaction(tax_no =data1["taxno"],qtr=str(data1["qtr"]))
                        # newtxn.tax_no=data1["taxno"]
                        newtxn.description=resp[1]
                        newtxn.amount=resp[2]
                        newtxn.name = resp[3]
                        newtxn.payermobile_no = request.POST['payermobileno']
                        # newtxn.address1 = resp[4]
                        # newtxn.address2 = resp[5]
                        # newtxn.address3 = resp[6]
                        newtxn.address = resp[4]+ ' ' + resp[5] + ' ' + resp[6]
                        newtxn.rowNo = resp[7]
                        # newtxn.qtr = data1["qtr"]
                        newtxn.txnId = 'MBL-DNCC-TAX-' + str(data1["taxno"]) +'-'+ str(data1["qtr"])
                        user = User.objects.get(email=request.session["User_Email"])
                        newtxn.input_user= user
                        newtxn.branch = user.branchname
                        newtxn.save()
                    # context['txn'] = newtxn

                        return redirect('confirmation', txn = newtxn.txnId)
                    
                    # return render(request, 'confirmation.html',context=context )
    else:
        return redirect('login')



def confirmation(request, txn):

    if "User_Email" in request.session :
        context =getUser(request.session["User_Email"])
        
        context['txn'] = Transaction.objects.get(txnId=txn)
        return render(request, 'confirmation.html',context=context )
    else:
        return redirect('login')
            

def submitTax(request, txn):
    if "User_Email" in request.session :
        context =getUser(request.session["User_Email"])
        currentTxn = Transaction.objects.get(txnId=txn)
        if(currentTxn.status is not True):

            data ={}
            data['taxno'] = currentTxn.tax_no
            data['amt'] = currentTxn.amount
            data['qtr'] = currentTxn.qtr
            data['mobno'] = currentTxn.payermobile_no
            data['tstatus'] = currentTxn.tstatus
            # data['ntranno'] = '2292'
            data['ntranno'] = currentTxn.txnId
            data['frm'] = settings.API_USERNAME
            data['rowid'] = currentTxn.rowNo

            print(data)
            
            response=requests.get(url + "holding_data_chk_return_ver6.aspx",data = data).text
            print(response)
            if(response =='00'):
                currentTxn.status = True
                currentTxn.save()
        

            # taxno=30990005606382019&amt=20&
            # qtr=3&mobno=01937148058&
            # tstatus=pp&
            # ntranno=3333&
            # frm=MRCT1001&
            # rowid=11B5D34D-0064-4D04-9774-EC3D60D9C557
            
       


        return redirect('confirmation', txn=txn)
    else:
        return redirect('login')
    
    # response=requests.post(url,data = data1)
    # print(response.json())


   
def login(request):

    if request.method=="GET":
        return render(request, "registration\login.html")
    if request.method=="POST":
        domainmail = request.POST["username"]
        domainpass = request.POST["password"]
        domainmail = domainMailCheck(domainMail=domainmail)
        if ldapcheck(domainmail, domainpass):
            if checkAuthUser(domainmail):
                user = User.objects.get(email=domainmail)
                request.session['User_Email'] = user.email
                return redirect('landing')
            else:
                # return redirect('login')
                message = "Access Denied : You're Not Authorised !"
                return render( request, 'exceptions/val_error.html', {'err_message': message})
        else:
            message = "Invalid username or password"
            return render( request, 'exceptions/val_error.html', {'err_message': message})
            # return HttpResponse('<h1> vul password </h1> <h2>password: {}</h2> <h2> username {}</h2>'.format(domainpass, domainmail))

def logout(request):
    try:
        del request.session['User_Email']
    except KeyError:
        message = "Could not logout please try again"
        return render( request, 'exceptions/val_error.html', {'err_message': message})
    return redirect('login')


def register(request):
    if request.session.get("User_Email",True):
        user = User.objects.get(email=request.session["User_Email"])
        if user.is_staff():
            if request.method=="POST":
                email = request.POST['email']
                if "admin" in request.POST:
                    new_user = User.objects.create(email = email, is_admin=1)
                else:
                    new_user = User.objects.create(email = email)

                if "branch" not in request.POST:
                    message = "To create user, user must provide branch name."
                    return redirect('register', message=message)
                # print(request.POST["branch"])
                branchObject = Branch.objects.get(branch_name=request.POST["branch"])
                new_user.branchname= branchObject
                new_user.save()


                
                message = " user {} creater successfully the users id is: {}".format(email, new_user.id)
                # print(user)
                
                return render(request, "registration/register.html", context={'message':message, 'user_info':user,"branchlist":getBranchNameList() })
            context=getUser(request.session["User_Email"])
            context["branchlist"] = getBranchNameList()
            return render(request, "registration/register.html", context=context)
        # return HttpResponse("<h1> You are not admin!</h1>")  
        message = "Only admin privilaged individuals can do this operation"
        return render( request, 'exceptions/val_error.html', {'err_message': message})



def generate_report(request):
    if request.session.get("User_Email",True):
        context=getUser(request.session["User_Email"])

        if(context['user_info'].is_admin):
            queryset = Transaction.objects.all().order_by('-txn_date')
        else:
            queryset = Transaction.objects.filter(branch=context["user_info"].branchname, txn_date__date=datetime.today()).order_by('-txn_date')
        context["total_txn"] = len(queryset.filter(status=True))
        q = queryset.filter(status=True)
        context["sum"] = q.aggregate(Sum('amount'))["amount__sum"]
        context["date"] = datetime.today()
        context["branch_name"] = context["user_info"].branchname
        
        paginator = Paginator(queryset, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context["txns"] =page_obj
        # print(paginator.page_range())
        return render(request, "table_pages/txnlist.html", context=context)


def getUserProfile(request):
    
    context = getUser(request.session["User_Email"])
    
    return render(request, "userprofile/profile.html", context=context)

def postdatabydate(request):
    if request.session.get("User_Email",True):
        context=getUser(request.session["User_Email"])
        if "ajke" not in context:
            context["ajke"] =str(datetime.today()).split(' ')[0]
        # print(request.POST)
        if request.method =='GET':
            
            return render(request, "table_pages/datepicker.html", context= context)

        if request.method == 'POST':
            if "datesearch" in request.POST:
                date = request.POST["datesearch"]
                try:
                    day = datetime.strptime(date, "%Y-%m-%d").date()
                except Exception as e:
                    context["message"] = "Please enter a date in order for searching."
                    context['classes'] = 'alert alert-danger alert-dismissable'
                    return render(request, "table_pages/datepicker.html" , context=context) 
            else:
                day = datetime.today()
            
            # print(day)

            if(context['user_info'].is_admin):
                queryset = Transaction.objects.filter(txn_date__date=day).order_by('-txn_date')
            else:
                queryset = Transaction.objects.filter(branch=context["user_info"].branchname, txn_date__date=day).order_by('-txn_date')

            # queryset = Transaction.objects.filter(txn_date__date=day).order_by('-txn_date')
            # print(queryset)
            context["total_txn"] = len(queryset.filter(status=True))
            q = queryset.filter(status=True)
            context["sum"] = q.aggregate(Sum('amount'))["amount__sum"]
            # context["date"] = datetime.today()
            context["branch_name"] = context["user_info"].branchname

            paginator = Paginator(queryset, 20)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context["txns"] =queryset
            context["date"] =day
            context["ajke"] =str(day).split(' ')[0]
            # print(paginator.page_range())

            return render(request, "table_pages/datepicker.html", context=context) 
    else:
        raise PermissionError

def reportWdatepicker(request):
    if request.session.get("User_Email",True):
        context=getUser(request.session["User_Email"])
        if "date" in request.GET:
            date = request.GET["date"]
            day = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            day = datetime.today()
        
        # print(day)
        queryset = Transaction.objects.filter(txn_date__date=day)
        print(queryset)

        paginator = Paginator(queryset, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context["txns"] =page_obj
        context["date"] =day
        # print(paginator.page_range())
        return render(request, "table_pages/datepicker.html", context=context)