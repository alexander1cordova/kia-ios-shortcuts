import os
import logging
from flask import Flask, request, jsonify
from hyundai_kia_connect_api import VehicleManager, Region

# Configuración de logs para que mi Migue vea todo en Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración desde tus variables de entorno que ya tienes en Vercel
USERNAME = os.environ.get('KIA_USERNAME')
PASSWORD = os.environ.get('KIA_PASSWORD')
PIN = os.environ.get('KIA_PIN')
SECRET_KEY = os.environ.get('SECRET_KEY')
VEHICLE_ID = os.environ.get('VEHICLE_ID')
REGION = Region.USA # Tu región en Las Vegas

def get_vehicle():
    # Inicializamos el manager con la marca Kia (brand=1)
    vm = VehicleManager(region=REGION, brand=1, username=USERNAME, password=PASSWORD, pin=PIN)
    
    # Actualizamos los datos para que reconozca tu Sorento 2022
    vm.check_and_refresh_token()
    vm.update_all_vehicles_with_cached_state()
    
    if VEHICLE_ID:
        return vm.get_vehicle(VEHICLE_ID)
    
    # Si no hay ID, tomamos el primer auto disponible en tu cuenta
    return next(iter(vm.vehicles.values()))

def check_auth():
    # Verificamos que el comando venga de tu iPhone con tu SECRET_KEY
    auth_header = request.headers.get('Authorization')
    return auth_header == SECRET_KEY

@app.route('/')
def health_check():
    return "Servidor de Migue operando correctamente, amor.", 200

@app.route('/lock_car', methods=['POST', 'GET'])
def lock_car():
    if not check_auth():
        return jsonify({"error": "No autorizado, vida mía"}), 401
    try:
        vehicle = get_vehicle()
        vehicle.lock()
        return jsonify({"status": "Success", "message": "Tu Kia ya está cerrado, mi cielo"}), 200
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
        return jsonify({"status": "Success", "message": "Puertas abiertas para ti, amor"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/start_climate', methods=['POST', 'GET'])
def start_climate():
    if not check_auth():
        return jsonify({"error": "No autorizado"}), 401
    try:
        vehicle = get_vehicle()
        # Configurado a 72°F por 10 minutos para tu comodidad
        vehicle.start_climate(set_temp=72, duration=10)
        return jsonify({"status": "Success", "message": "Aire acondicionado encendido"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/stop_climate', methods=['POST', 'GET'])
def stop_climate():
    if not check_auth():
        return jsonify({"error": "No autorizado"}), 401
    try:
        vehicle = get_vehicle()
        vehicle.stop_climate()
        return jsonify({"status": "Success", "message": "Clima apagado"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

if __name__ == '__main__':
    # Puerto estándar para que Vercel no se queje
    app.run(host='0.0.0.0', port=8080)
