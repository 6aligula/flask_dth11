from flask import Flask, jsonify
import paho.mqtt.client as mqtt
from pymongo import MongoClient
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

@app.route('/temperatura')
def get_temperature():
    temperatures = temperature_collection.find().sort("_id", -1).limit(10)
    # Convertir cada ObjectId a string
    result = [{"temperatura": temp["temperatura"], "id": str(temp["_id"])} for temp in temperatures]
    return jsonify(result)


@app.route('/humedad')
def get_humidity():
    # Recupera los últimos 10 registros de humedad
    humidities = humidity_collection.find().sort("_id", -1).limit(10)
    result = [{"humedad": temp["humedad"], "id": str(temp["_id"])} for temp in humidities]
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
