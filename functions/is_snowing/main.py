import os

import flask
from google.cloud import firestore

db = firestore.Client()

def get_weather():
    doc_ref = db.collection("darksky").document("data")
    return doc_ref.get().to_dict()

def is_snowing(request):
    wx = get_weather()
    obj = {
        'isSnowing': wx['currently']['icon'] == 'snow',
        'dataUpdated': wx['currently']['time'],
        'temperature': wx['currently']['temperature']
    }
    response = flask.jsonify(obj)
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set('Access-Control-Allow-Methods', 'GET')
    return response
