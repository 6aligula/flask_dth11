from flask import Flask, jsonify
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from bson.objectid import ObjectId
import pytz
from dotenv import load_dotenv
import os

# Carga las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configura los detalles del broker MQTT
mqtt_broker = os.getenv("MQTT_BROKER")
mqtt_port = 1883
temperatura_topic = os.getenv("TEMP_TOPIC")
humedad_topic = os.getenv("HUME_TOPIC")

# Configuración de MongoDB
mongo_client = MongoClient('mongodb://127.0.0.1:27017/')
db = mongo_client['sensor_database']  # Nombre de la base de datos
temperature_collection = db['temperatura']  # Colección para la temperatura
humidity_collection = db['humedad']  # Colección para la humedad

# Callback para cuando el cliente recibe una CONNACK del servidor
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(temperatura_topic)
    client.subscribe(humedad_topic)

# Callback que se llama cuando se recibe un mensaje del servidor.
def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    if msg.topic == temperatura_topic:
        print(msg.topic + " " + payload)
        temperature_collection.insert({"temperatura": float(payload)})

    elif msg.topic == humedad_topic:
        print(msg.topic + " " + payload)
        humidity_collection.insert({"humedad": float(payload)})

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_broker, mqtt_port, 60)
client.loop_start()

@app.route('/')
def index():
    return "MQTT to Flask Bridge"

def convert_utc_to_local(utc_dt, local_tz):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_dt.strftime('%Y-%m-%d %H:%M:%S')

@app.route('/temperatura')
def get_temperature():
    local_tz = pytz.timezone("Europe/Madrid")  # Reemplaza con tu zona horaria
    temperatures = temperature_collection.find().sort("_id", -1).limit(10)
    result = [{
        "temperatura": temp["temperatura"],
        "timestamp": convert_utc_to_local(ObjectId(temp["_id"]).generation_time, local_tz)
    } for temp in temperatures]
    return jsonify(result)

@app.route('/humedad')
def get_humidity():
    local_tz = pytz.timezone("Europe/Madrid")  # Reemplaza con tu zona horaria
    humidities = humidity_collection.find().sort("_id", -1).limit(10)
    result = [{
        "humedad": temp["humedad"],
        "timestamp": convert_utc_to_local(ObjectId(temp["_id"]).generation_time, local_tz)
    } for temp in humidities]
    return jsonify(result)
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
