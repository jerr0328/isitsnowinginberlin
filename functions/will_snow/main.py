import os
from datetime import datetime

import flask
from google.cloud import firestore

db = firestore.Client()

def get_weather():
    doc_ref = db.collection("darksky").document("data")
    return doc_ref.get().to_dict()


def check_if_will_snow(wx):
    now = datetime.now()
    next_forecast = next(data for data in wx['daily']['data'] if now < datetime.fromtimestamp(data['time']))
    return next_forecast['icon'] == 'snow'


def will_snow(request):
    wx = get_weather()
    obj = {
        'willSnow': wx['currently']['icon'] == 'snow',
        'dataUpdated': wx['currently']['time'],
    }
    response = flask.jsonify(obj)
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set('Access-Control-Allow-Methods', 'GET')
    return response
