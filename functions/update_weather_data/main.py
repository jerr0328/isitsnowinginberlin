import os

import requests
from google.cloud import firestore

DARKSKY_URL = "https://api.darksky.net/forecast/{key}/{coords}".format(
    key=os.getenv("DARKSKY_KEY"), coords="52.52,13.37"
)
DARKSKY_PAYLOAD = {"units": "si", "exclude": "[minutely,hourly,flags,alerts]"}
db = firestore.Client()


def fetch_weather_data():
    r = requests.get(DARKSKY_URL, params=DARKSKY_PAYLOAD)
    r.raise_for_status()
    return r.json()


def update_weather_data(data, context):
    doc_ref = db.collection("darksky").document("data")
    wx = fetch_weather_data()
    doc_ref.set(wx)

