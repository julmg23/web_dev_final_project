from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.forms import ModelForm
from datetime import datetime, timedelta
from django.contrib import messages

from django.urls.base import clear_url_caches

from .models import User, Transaction, Account, Budget

@login_required(login_url="login")
def index(request):

    #Get the last 6 transactions
    get_transactions = Transaction.objects.filter(user=request.user).order_by("-date")[:6]

    # Get the accounts
    get_accounts = Account.objects.filter(user=request.user)
    
    return render(request, "planetfinance/index.html", {
        "get_accounts" : get_accounts,
        "get_transactions" : get_transactions
        })

def networth_chart(request):
    labels = []
    data = []
    networth = 0

    # Retrieve dates of last 6 months
    last_six_months = datetime.today() - timedelta(days=182)

    # Filter transactions and then calculate the networth
    queryset = Transaction.objects.filter(date__gte=last_six_months, user=request.user).order_by('date')
    for entry in queryset:
        if entry.tran_type == "Income":
            labels.append(entry.date.strftime('%m/%d'))
            networth += entry.amount
            data.append(networth)

        if entry.tran_type == "Expense":
            labels.append(entry.date.strftime('%m/%d'))
            networth -= entry.amount
            data.append(networth)

    
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

@login_required(login_url="login")
def transaction_list(request):

    #Get all transactions
    get_transactions = Transaction.objects.filter(user=request.user).order_by("-date")

    # Get the accounts
    get_accounts = Account.objects.filter(user=request.user)
    
    return render(request, "planetfinance/transaction_list.html", {
        "get_accounts" : get_accounts,
        "get_transactions" : get_transactions
        })


@login_required(login_url="login")
def transaction(request):
    if request.method == "POST":
        tran_type = request.POST["tran_type"]
        date_id = request.POST["date"]
        amount = request.POST["amount"]
        account_id = request.POST["account"]
        account_id = Account.objects.get(pk = account_id)
        user_id = request.user

        transaction = Transaction.objects.create(tran_type=tran_type, amount=amount, account=account_id, user=user_id, date=date_id)
        transaction.save()

        return HttpResponseRedirect(reverse("index"))


@login_required(login_url="login")
def budget(request):
    # Retrieve the current month
    mydate = datetime.now()
    current_month = mydate.strftime("%B")

    # Get current month's cash flow 
    income_total = 0
    expenses_total = 0

    today = datetime.now()
    queryset = Transaction.objects.filter(date__month=today.month, date__year=today.year, user=request.user).order_by('date')
    for entry in queryset:
        if entry.tran_type == "Income":
            income_total += entry.amount

        if entry.tran_type == "Expense":
            expenses_total += entry.amount

    # Retrieve this month's budget
    try: 
        monthly_budget = Budget.objects.get(month=today.month, year=today.year, user=request.user)
        if monthly_budget.number > expenses_total:
            budget_percent = expenses_total / monthly_budget.number * 100
        else:
            budget_percent = 0
    except:
        monthly_budget = None
        budget_percent = None



    return render(request, "planetfinance/budget.html", {
        'current_month': current_month,
        'monthly_budget': monthly_budget,
        'income_total': income_total,
        'expenses_total': expenses_total,
        'budget_percent': budget_percent
        })

@login_required(login_url="login")
def cashflow(request):
    # Retrieve the current month
    mydate = datetime.now()
    current_month = mydate.strftime("%B")

    # Get current month's cash flow 
    income_total = 0
    expenses_total = 0

    today = datetime.now()
    queryset = Transaction.objects.filter(date__month=today.month, date__year=today.year, user=request.user).order_by('date')
    for entry in queryset:
        if entry.tran_type == "Income":
            income_total += entry.amount

        if entry.tran_type == "Expense":
            expenses_total += entry.amount

    total_cashflow = income_total-expenses_total

    # Format Cash flow
    if total_cashflow < 0:
        total_cashflow = "-$" + str(abs(total_cashflow))
    else:
        total_cashflow = "+$" + str(total_cashflow)

    # Retrieve this month's budget
    try: 
        monthly_budget = Budget.objects.get(month=today.month, year=today.year, user=request.user)
        budget_difference = monthly_budget.number - expenses_total
        abs_budget_diff = abs(budget_difference)
    except:
        monthly_budget = None
        budget_difference = None
        abs_budget_diff = None


    return render(request, "planetfinance/cashflow.html", {
        'current_month': current_month,
        'total_cashflow': total_cashflow,
        'monthly_budget': monthly_budget,
        'income_total': income_total,
        'expenses_total': expenses_total,
        'budget_difference': budget_difference,
        'abs_budget_diff': abs_budget_diff
        })

def budget_chart(request):
    # Retrieve the current month
    mydate = datetime.now()
    current_month = mydate.strftime("%B")

    # Get current month's cash flow 
    income_total = 0
    expenses_total = 0

    today = datetime.now()
    queryset = Transaction.objects.filter(date__month=today.month, date__year=today.year, user=request.user).order_by('date')
    for entry in queryset:
        if entry.tran_type == "Income":
            income_total += entry.amount

        if entry.tran_type == "Expense":
            expenses_total += entry.amount

    # Retrieve this month's budget
    try: 
        monthly_budget = Budget.objects.get(month=today.month, year=today.year, user=request.user)
        if monthly_budget.number > expenses_total:
            budget_percent = expenses_total / monthly_budget.number * 100
        else:
            budget_percent = 0

        data = [budget_percent, 100-budget_percent]

    except:
        data = [None, None]


    
    return JsonResponse(data={
        'data': data,
    })


@login_required(login_url='login')
def createbudget(request):
    if request.method == "POST":

       month = request.POST["month"]
       year = request.POST["year"]
       number = request.POST["number"]

       # Check to make sure that there isn't a budget for this month already
       try: 
            monthly_budget = Budget.objects.get(month=month, year=year, user=request.user)
       except:
            return HttpResponseRedirect(reverse("budget"))


       # Create a new budget and save it
       newbudget = Budget(
           user = request.user,
           month = month,
           year = year,
           number = number
           )
            
       newbudget.save()

       # Return to budget
       return HttpResponseRedirect(reverse("budget"))

    return HttpResponseRedirect(reverse("budget"))


def cashflow_chart(request):
    labels = ['Expenses', 'Income']
    data = []
    income_total = 0
    expenses_total = 0

    today = datetime.now()

    # Filter transactions for this month and year
    queryset = Transaction.objects.filter(date__month=today.month, date__year=today.year, user=request.user).order_by('date')
    for entry in queryset:
        if entry.tran_type == "Income":
            income_total += entry.amount

        if entry.tran_type == "Expense":
            expenses_total += entry.amount
    
    data.append(expenses_total)
    data.append(income_total)

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    }) 

@login_required(login_url="login")
def account(request):
    if request.method == "POST":
        name = request.POST["name"]
        user_id = request.user

        account = Account.objects.create(name=name, user=user_id)
        account.save()

        return HttpResponseRedirect(reverse("index"))

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "planetfinance/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "planetfinance/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "planetfinance/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, password)
            user.save()
        except IntegrityError:
            return render(request, "planetfinance/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "planetfinance/register.html")