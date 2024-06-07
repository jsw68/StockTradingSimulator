"""Test1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.welcome_page, name='home'),
    path("form", views.form_page, name="form"),
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path("stock/<str:ticker>", views.ticker, name="ticker"),
    path("history", views.history, name="history"),
    path("logout", views.logout_view, name="logout"),
    # TODO add route that takes info from stock/{ticker} as parameter and uses that as ticker and shows info for that ticker
]
