from django.shortcuts import HttpResponseRedirect, render, reverse
from . import forms
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
from django.db import IntegrityError
from .models import User, StocksRecord
import requests
import json
import re
import plotly.express as px
import plotly.offline as po
import yfinance as yf
import numpy as np
import pandas as pd
import decimal
import datetime
pd.options.plotting.backend = "plotly"

DOW_30_SYMBOLS = ["AXP","AMGN","AAPL","BA","CAT","CSCO","CVX","GS","HD","HON","IBM","INTC","JNJ","KO","JPM","MCD","MMM","MRK","MSFT","NKE","PG","TRV","UNH","CRM","VZ","V","WBA","WMT","DIS","DOW"]
TOKEN = "TOKEN GOES HERE"
def get_data(ticker):
    # base url components
    url_begin = "https://cloud.iexapis.com/stable/stock/market/batch?symbols="
    url_end = "&types=quote&token="+TOKEN
    # add ticker to url
    full_url = url_begin + ticker + url_end
    res = requests.get(full_url)
    # check status code
    res.raise_for_status()
    # change to dict and return the value
    res_dict = json.loads(res.text)
    res_dict = res_dict[ticker]
    return res_dict

def welcome_page(request):
    if request.user.is_authenticated:
        if request.method == "GET":
            # get all the stocks of the user that have not been sold
            stocks = StocksRecord.objects.filter(user_id=request.user.id, sold_at=None).values()
            # get the info for each stock and change it to a dict
            stocks = [dict(stock) for stock in stocks.values()]
            # initiate new_stocks which will contain the symbol, info, and current price of each stock
            new_stocks = []
            # add symbol and info to new_stocks
            [new_stocks.append([stock["symbol"], stock]) for stock in stocks]               
            # base url components
            url_begin = "https://cloud.iexapis.com/stable/stock/market/batch?symbols="
            url_end = "&types=quote&token="+TOKEN
            # get all the symbols needed and remove doubles
            stock_symbols = list(set([stock["symbol"] for stock in stocks]))
            # get info for all stocks
            full_url = url_begin + ",".join(stock_symbols) + url_end
            res = requests.get(full_url)
            # check status code
            res.raise_for_status()
            # change to dict
            res_dict = json.loads(res.text)
            # initiate prices which will hold the current prices for all the stocks
            prices = {}
            # add the current price to the prices dict for each entry
            for key, value in res_dict.items():
                prices[key] = value["quote"]["latestPrice"]
            # add current price to each entry of new_stocks
            [stock.append(prices[stock[0]]) for stock in new_stocks]
            portfolio_value = 0
            # calculate a portfolio value by multiplying the curent price of each asset by the amount owned
            for stock in new_stocks:
                portfolio_value += (stock[1]["amount"]*stock[2])
            return render(request, "open.html",{
                "username": request.user.username,
                "money": request.user.money,
                "portfolio_value": portfolio_value,
                "stocks": new_stocks,
                "x": range(len(new_stocks))
            })
        elif request.method == "POST":
            # if it is a post request on this page the user is trying to sell
            # get stock object they are selling
            stock = StocksRecord.objects.get(id=request.POST["id"])
            # get the amount they want to sell and the total amount they have
            amount_sold = int(request.POST.get("amount", 1))
            total_amount = int(stock.amount)
            # get symbol they are selling
            symbol = stock.symbol
            # get the current price of the stock they are selling
            res_dict = get_data(symbol)
            latest_price = res_dict["quote"]["latestPrice"]
            # if they want to sell all of it
            if amount_sold == total_amount:
                # change the column in databse for sold_at from null to amount that it is worth currently
                stock.sold_at = latest_price
                stock.save()
                # add the amount of money they sold it at * how many they sold to the users total cash
                user = User.objects.get(username=request.user.username)
                user.money += decimal.Decimal(latest_price*amount_sold)
                user.save()
            # if they dont want to sell all of their shares, we will create a new object with the same info just less shares
            else:
                # the amount of shares that will be in the new object
                amount_remaining = total_amount - amount_sold
                # sell the current object using current value
                stock.sold_at = latest_price
                stock.amount = amount_sold
                # add a new row to thte database
                form = forms.StockForm()
                new_stock = form.save(commit=False)
                # same as old stock object but with less shares
                new_stock.amount = amount_remaining
                new_stock.bought_at = stock.bought_at
                new_stock.symbol = stock.symbol
                new_stock.user_id = stock.user_id
                new_stock.save()
                stock.save()
                # give the user the money they earned
                user = User.objects.get(username=request.user.username)
                user.money += decimal.Decimal(latest_price*amount_sold)
                user.save()
            return HttpResponseRedirect(reverse('home'))
    else:
        return HttpResponseRedirect(reverse("login"))
        

def form_page(request, stuff=None):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    if request.method == "GET":
        url_begin = "https://cloud.iexapis.com/stable/stock/market/batch?symbols="
        url_end = "&types=quote&token="+TOKEN
        full_url = url_begin + ",".join(DOW_30_SYMBOLS) + url_end
        res = requests.get(full_url)
        res.raise_for_status()
        res_dict = json.loads(res.text)
        print(type(res_dict), "type")
        stocks = {}
        prices = {}
        change = {}
        for key, value in res_dict.items():
            print(key, value["quote"]["latestPrice"])
            stocks[key] = [value["quote"]["latestPrice"], value["quote"]["change"]]
            prices[key] = value["quote"]["latestPrice"]
            change[key] = value["quote"]["change"]
        print(change)
        return render(request, "form.html", {
            "form": forms.StockForm(),
            "prices": prices,
            "change": change,
            "stocks": stocks,
        })
    else:
        form = forms.StockForm()
        form = form.save(commit=False)
        form.amount = request.POST.get("amount", default=1)
        form.symbol = request.POST.get("symbol")
        form.bought_at = request.POST.get("price")
        form.user = request.user
        new_balance = float(request.user.money) - float(float(form.amount)*float(form.bought_at))
        user = User.objects.get(username=request.user.username)
        user.money = new_balance
        user.save()
        form.save()
        return HttpResponseRedirect(reverse('home'))


def ticker(request, ticker):
    ticker = ticker.upper()
    if ticker in DOW_30_SYMBOLS:
        # API call
        res_dict = get_data(ticker)
        quote = res_dict["quote"]

        # turn camel case into nice title w spaces and remove empty data points
        quote = {re.sub(r'(?<!^)(?=[A-Z])', ' ', category).title(): data for category, data in quote.items() if (data != 0 and data != None)}
        
        # get historical data for ticker

        # days back
        periods = [1825, 365, 180]
        # these periods are too small to go by date so we take the last x number of entries. This accounts for weekends and not market days unlike the other periods
        smaller_periods = [30, 5]
        plots = []
        df = yf.download(ticker, period="max")
        df = df[["Close"]]
        df = df.reset_index()
        a = datetime.datetime(datetime.datetime.now().year, 1, 1)
        now = datetime.datetime.now()

        for period in periods:
            print(period)
            filtered = df.loc[df["Date"] >= (now-datetime.timedelta(days=period))]
            filtered = filtered.set_index("Date", drop=True)
            fig = filtered.plot()
            graph_div = po.plot(fig, auto_open = False, output_type="div")
            plots.append(graph_div)
        for period in smaller_periods:
            filtered = df.tail(period)
            filtered = filtered.set_index("Date", drop=True)
            fig = filtered.plot()
            graph_div = po.plot(fig, auto_open = False, output_type="div")
            plots.append(graph_div)
        ytd = df.loc[df["Date"] >= a]
        ytd = ytd.set_index("Date", drop=True)
        fig = ytd.plot()
        graph_div = po.plot(fig, auto_open = False, output_type="div")
        plots.insert(0, graph_div)
        df = df.set_index("Date", drop=True)
        fig = df.plot()
        graph_div = po.plot(fig, auto_open = False, output_type="div")
        plots.insert(0, graph_div)
        return render(request, "ticker.html", {
            "ticker": ticker,
            "data": quote,
            "plots": plots,
        })
    else:
        return render(request, "ticker.html")


def history(request):
    if request.user.is_authenticated:
        my_stocks = StocksRecord.objects.filter(user_id=request.user.id).exclude(sold_at=None).values()
        return render(request, "history.html", {
            "stocks": my_stocks
        })
    return HttpResponseRedirect(reverse("register"))


def login(request):
    if request.method == "POST":
        if request.method == "POST":      

        # Attempt to sign user in
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)

            # Check if authentication successful
        if user is not None:
            auth_login(request, user)
            return HttpResponseRedirect(reverse("home"))
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        money = 10000
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password, money=money)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        auth_login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "index.html")
    
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))
