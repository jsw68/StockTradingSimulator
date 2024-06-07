import requests, bs4
res = requests.get("https://www.cnbc.com/dow-30/")
soup = bs4.BeautifulSoup(res.text)
tds = soup.find_all("td", class_="BasicTable-symbol")
[print(td.a.text) for td in tds]
