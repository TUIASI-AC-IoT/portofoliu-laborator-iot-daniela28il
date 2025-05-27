import json
import os
import random
from threading import Thread, Lock
from serial import Serial
from flask import Flask, jsonify
from flask import request
from os.path import exists
from time import sleep

PORT = 'COM3'
BAUDRATE = 115200
serial_port = Serial(PORT, BAUDRATE, timeout=0)
mutex = Lock()

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def read_sensor_data():
    global last_temp
    while 1:
        data = serial_port.read()
        mutex.acquire()
        last_temp = data
        mutex.release()

sensor_thread = Thread(target=read_sensor_data, args=())
sensor_thread.start()

VALID_SCALES = ['Celsius', 'Fahrenheit', 'Kelvin']


def convert_temperature(value_celsius, scale):
    if scale == "Fahrenheit":
        return round(value_celsius * 9 / 5 + 32, 2)
    elif scale == "Kelvin":
        return round(value_celsius + 273.15, 2)
    return round(value_celsius, 2)


@app.route('/sensors', methods=['GET'])
def list_sensors():
    sensors = []
    for filename in os.listdir(BASE_DIR):
        if filename.endswith('_config.json'):
            sensor_id = filename.split('_config.json')[0]
            sensors.append(sensor_id)
    return jsonify({"sensors": sensors})


@app.route('/sensor/<sensor_id>', methods=['GET'])
def read_sensor(sensor_id):
    config_path = os.path.join(BASE_DIR, f"{sensor_id}_config.json")
    scale = "Celsius"
    if exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
            scale = config.get("scale", "Celsius")
    value_celsius = round(random.uniform(20.0, 30.0), 2)
    mutex.acquire()
    value_converted = convert_temperature(value_celsius, scale)
    mutex.release()
    return jsonify({
        "sensor_id": sensor_id,
        "value": value_converted,
        "scale": scale
    })


@app.route('/sensor/<sensor_id>', methods=['POST'])
def create_config(sensor_id):
    config_path = os.path.join(BASE_DIR, f"{sensor_id}_config.json")
    if exists(config_path):
        return jsonify({"error": "Config already exists"}), 409
    config = request.get_json() or {"scale": "Celsius"}
    scale = config.get("scale", "Celsius")
    if scale not in VALID_SCALES:
        return jsonify({"error": f"Invalid scale '{scale}'. Valid options: {VALID_SCALES}"}), 400
    with open(config_path, 'w') as f:
        json.dump({"scale": scale}, f)
    return jsonify({"message": "Config created", "scale": scale}), 201


@app.route('/sensor/<sensor_id>/<config_file>', methods=['PUT'])
def update_config(sensor_id, config_file):
    config_path = os.path.join(BASE_DIR, config_file)
    if not exists(config_path):
        return jsonify({"error": "Config not found"}), 404
    config = request.get_json() or {"scale": "Celsius"}
    scale = config.get("scale", "Celsius")
    if scale not in VALID_SCALES:
        return jsonify({"error": f"Invalid scale '{scale}'. Valid options: {VALID_SCALES}"}), 400
    with open(config_path, 'w') as f:
        json.dump({"scale": scale}, f)
    return jsonify({"message": "Config updated", "scale": scale}), 200


if __name__ == '__main__':
    app.run(debug=True)
