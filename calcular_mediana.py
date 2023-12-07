# calcular_mediana.py
from pymongo import MongoClient
from datetime import datetime

# Configuración de MongoDB (ajustar según sea necesario)
mongo_client = MongoClient('mongodb://127.0.0.1:27017/')
db = mongo_client['sensor_database']
temperature_collection = db['temperatura']
mediana_collection = db['mediana_temperatura']

def calcular_y_guardar_mediana_temperatura():
    # Obtener los últimos 7 registros de temperatura
    temperaturas = temperature_collection.find().sort("_id", -1).limit(7)

    # Extraer los valores de temperatura
    valores = [temp["temperatura"] for temp in temperaturas]

    # Verificar si hay suficientes valores para calcular la mediana
    n = len(valores)
    if n == 0:
        print("No hay suficientes datos para calcular la mediana")
        return  # Salir de la función si no hay suficientes datos

    # Ordenar los valores y calcular la mediana
    valores.sort()
    mediana = valores[n // 2] if n % 2 != 0 else (valores[n // 2 - 1] + valores[n // 2]) / 2
    
    time =  datetime.utcnow()

    # Guardar la mediana en la base de datos con timestamp
    mediana_collection.insert({"mediana": mediana})

    print(f"Mediana de temperatura {mediana} guardada en la base de datos. a  fecha {time}")
    return mediana

if __name__ == "__main__":
    calcular_y_guardar_mediana_temperatura()
