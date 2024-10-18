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
humedad_terra_topic = os.getenv("HUME_TERRA_TOPIC")

# Configuración de MongoDB
mongo_client = MongoClient('mongodb://127.0.0.1:27017/')
db = mongo_client['sensor_database']  # Nombre de la base de datos
temperature_collection = db['temperatura']  # Colección para la temperatura
humidity_collection = db['humedad']  # Colección para la humedad
soil_moisture_collection = db['humedad_tierra']  # Colección para la humedad de la tierra

# Callback para cuando el cliente recibe una CONNACK del servidor
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(temperatura_topic)
    client.subscribe(humedad_topic)
    client.subscribe(humedad_terra_topic)

# Callback que se llama cuando se recibe un mensaje del servidor.
def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    if msg.topic == temperatura_topic:
        print(msg.topic + " " + payload)
        temperatura = float(payload) - 5

        # Verificar si la temperatura es menor o igual a cero
        if temperatura <= 0:
            temperatura_mediana = calcular_mediana_temperatura()
            if temperatura_mediana is not None:
                temperatura = temperatura_mediana
            else:
                print("Mediana no disponible, usando valor por defecto")
                temperatura = 18  # Valor por defecto si la mediana no está disponible

        temperature_collection.insert({"temperatura": temperatura})

    elif msg.topic == humedad_topic:
        print(msg.topic + " " + payload)
        #Ajuste de humedad
        humedad_ajustada = float(payload) + 20
        # Asegurarse de que la humedad ajustada no exceda el 100%
        if humedad_ajustada > 90:
            humedad_ajustada = 70
        humidity_collection.insert({"humedad": humedad_ajustada})
    
    elif msg.topic == humedad_terra_topic:
        print(msg.topic + " " + payload)
        # Procesar la humedad del suelo directamente
        humedad_tierra = float(payload)
        soil_moisture_collection.insert({"humedad_tierra": humedad_tierra})


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

def calcular_mediana_temperatura():
    # Obtener los últimos 6 registros de temperatura
    temperaturas = temperature_collection.find().sort("_id", -1).limit(7)

    # Extraer los valores de temperatura
    valores = [temp["temperatura"] for temp in temperaturas]

    # Verificar si hay suficientes valores para calcular la mediana
    n = len(valores)
    if n == 0:
        raise ValueError("No hay suficientes datos para calcular la mediana")

    # Ordenar los valores y calcular la mediana
    valores.sort()
    mediana = valores[n // 2] if n % 2 != 0 else (valores[n // 2 - 1] + valores[n // 2]) / 2

    return mediana

def get_last_humedad():
    # Obtener el último registro de temperatura
    ultimo_registro = humidity_collection.find().sort("_id", -1).limit(1)
    
    # Verificar si se encontró algún registro
    if ultimo_registro.count() == 0:
        return jsonify({"error": "No se encontraron datos de humedad"})

    # Acceder al primer (y único) elemento del cursor
    ultimo_registro = list(ultimo_registro)[0]
    return ultimo_registro["humedad"]

def get_last_7_registros(collection):
    # Obtener los últimos 7 registros de una colección
    ultimos_7_registros = collection.find().sort("_id", -1).limit(7)
    
    # Verificar si se encontraron registros
    if ultimos_7_registros.count() == 0:
        return None

    # Convertir a lista y devolver
    return list(ultimos_7_registros)


@app.route('/temperatura')
def get_temperature():
    local_tz = pytz.timezone("Europe/Madrid")
    mediana_temp = calcular_mediana_temperatura()

    # Obtener los últimos 7 registros de temperatura y humedad
    ultimos_7_temperaturas = get_last_7_registros(temperature_collection)
    ultima_humedad = get_last_humedad()

    # Verificar si se encontraron registros
    if not ultimos_7_temperaturas or not ultima_humedad:
        return jsonify({"error": "No se encontraron datos suficientes"})
        # Extraer y convertir las marcas de tiempo de cada registro
    
    fechas = [
        convert_utc_to_local(ObjectId(registro["_id"]).generation_time, local_tz) 
        for registro in ultimos_7_temperaturas
    ]


    result = {
        "ultimas_temperaturas": [registro["temperatura"] for registro in ultimos_7_temperaturas],
        "timestamp": fechas,
        "mediana": mediana_temp,
        "humedad": ultima_humedad,
    }
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

@app.route('/humedad_tierra')
def get_soil_moisture():
    local_tz = pytz.timezone("Europe/Madrid")
    soil_moistures = soil_moisture_collection.find().sort("_id", -1).limit(10)
    result = [{
        "humedad_tierra": temp["humedad_tierra"],
        "timestamp": convert_utc_to_local(ObjectId(temp["_id"]).generation_time, local_tz)
    } for temp in soil_moistures]
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)