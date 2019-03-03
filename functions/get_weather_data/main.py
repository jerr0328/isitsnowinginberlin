import os

import flask
from google.cloud import firestore

db = firestore.Client()


def get_weather_data(request):
    doc_ref = db.collection("darksky").document("data")
    wx = doc_ref.get().to_dict()
    return flask.jsonify(wx)
