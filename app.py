from flask import Flask
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

# Carga las variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configura los detalles del broker MQTT
mqtt_broker = os.getenv("MQTT_BROKER")
mqtt_port = 1883
mqtt_topic = os.getenv("TEMP_TOPIC")

# El callback para cuando el cliente recibe una CONNACK del servidor
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(mqtt_topic)

# El callback que se llama cuando se recibe un mensaje del servidor.
def on_message(client, userdata, msg):
    print(msg.topic + " " + msg.payload.decode('utf-8'))
    # Aquí puedes procesar los datos recibidos

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_broker, mqtt_port, 60)

# Inicia un bucle en segundo plano para escuchar los mensajes
client.loop_start()

@app.route('/')
def index():
    return "MQTT to Flask Bridge"

if __name__ == '__main__':
    app.run( host='0.0.0.0')
