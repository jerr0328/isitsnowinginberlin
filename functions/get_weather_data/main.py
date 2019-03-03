import os

import flask
from google.cloud import firestore

db = firestore.Client()


def get_weather_data(request):
    doc_ref = db.collection("darksky").document("data")
    wx = doc_ref.get().to_dict()
    response = flask.jsonify(wx)
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set('Access-Control-Allow-Methods', 'GET')
    return response
