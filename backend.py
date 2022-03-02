#!/usr/bin/env python3
import os
from flask import Flask, jsonify, request
from math import sqrt
from json import loads, dumps
from flask_cors import CORS
from ast import literal_eval
import paho.mqtt.client as mqtt
import json
import time
#import random


global pot_state
global client
#mgclient = pymongo.MongoClient("mongodb://localhost:27017/")
#mgdb = mgclient["pot"]
#mgstates = mgdb["potstates"]
pot_state = {}
client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))


def on_message(client, userdata, message):
    global pot_state

    print("Received message:{} on topic {}".format(
        message.payload, message.topic))
    msg = json.loads(message.payload)
#    mgstates.insert_one(msg)
    pot_state = msg


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'development key'


# -- receive states from pot ------------------------------------------------
# states: {
#   umidity,
#   tempurature,
#   lightness,
#   weight,
#   ph,
#   ...
# }


# -- send state of pot ------------------------------------------------------
# states: {
#   umidity,
#   tempurature,
#   lightness,
#   weight,
#   ph,
#   ...
# }


@ app.route('/pot', methods=['GET'])
def send_state():
    global pot_state

    return jsonify(pot_state)


# -- receive command to control the pot ----------------------------------------
@ app.route('/types', methods=['POST'])
def command():
    global client
    type = request.json.get('type')
    payload = json.dumps(type)
    MSG_INFO = client.publish("IC.embedded/hexfuture/type", payload, qos=2)
    mqtt.error_string(MSG_INFO.rc)
    print(type)
    return {}

# -- check if server is online ------------------------------------------------


@ app.route('/check', methods=['GET'])
def check_server():
    return {}


if __name__ == '__main__':
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("broker.mqttdashboard.com", 1883)
    client.loop_start()

    client.subscribe("IC.embedded/hexfuture/#", qos=2)
    app.run(host='0.0.0.0', port=8000, debug=True)
