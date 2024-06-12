import requests
import json

def download_rate():
    res = requests.get("https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo")
    with open("./dags/data/res.json", "w") as sd:
        sd.write(res.text)

download_rate()

print("done")