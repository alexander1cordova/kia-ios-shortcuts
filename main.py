import os
import logging
from flask import Flask, request, jsonify
# Importación corregida para evitar el error de Migue
import hyundai_kia_connect_api as kia

# Configuración de logs para ver todo en Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Tus variables de entorno
USERNAME = os.environ.get('KIA_USERNAME')
PASSWORD = os.environ.get('KIA_PASSWORD')
PIN = os.environ.get('KIA_PIN')
SECRET_KEY = os.environ.get('SECRET_KEY')
VEHICLE_ID = os.environ.get('VEHICLE_ID')

# Definición de región directa para evitar el ImportError
REGION_USA = 3 

def get_vehicle():
    # Usamos la marca Kia (brand=1) y la región USA
    vm = kia.VehicleManager(region=REGION_USA, brand=1, username=USERNAME, password=PASSWORD, pin=PIN)
    
    vm.check_and_refresh_token()
    vm.update_all_vehicles_with_cached_state()
    
    if VEHICLE_ID:
        return vm.get_vehicle(VEHICLE_ID)
    
    return next(iter(vm.vehicles.values()))

def check_auth():
    auth_header = request.headers.get('Authorization')
    return auth_header == SECRET_KEY

@app.route('/')
def health_check():
    return "Servidor de Migue operando correctamente, amor.", 200

@app.route('/lock_car', methods=['POST', 'GET'])
def lock_car():
    if not check_auth():
        return jsonify({"error": "No autorizado"}), 401
    try:
        vehicle = get_vehicle()
        vehicle.lock()
        return jsonify({"status": "Success", "message": "Cerrado correctamente"}), 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/unlock_car', methods=['POST', 'GET'])
def unlock_car():
    if not check_auth():
        return jsonify({"error": "No autorizado"}), 401
    try:
        vehicle = get_vehicle()
        vehicle.unlock()
        return jsonify({"status": "Success", "message": "Abierto correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/start_climate', methods=['POST', 'GET'])
def start_climate():
    if not check_auth():
        return jsonify({"error": "No autorizado"}), 401
    try:
        vehicle = get_vehicle()
        vehicle.start_climate(set_temp=72, duration=10)
        return jsonify({"status": "Success", "message": "Clima encendido"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
