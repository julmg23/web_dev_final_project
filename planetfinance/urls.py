
from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("transaction", views.transaction, name="transaction"),
    path("account", views.account, name="account"),
    path('networth_chart/', views.networth_chart, name='networth_chart'),
    path("transaction_list", views.transaction_list, name="transaction_list"),
    path("budget", views.budget, name="budget"),
    path('cashflow_chart/', views.cashflow_chart, name='cashflow_chart'),
    path('createbudget', views.createbudget, name='createbudget'),
    path('cashflow', views.cashflow, name='cashflow'),
    path('budget_chart/', views.budget_chart, name='budget_chart')

]

