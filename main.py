import os
from flask import Flask, request, jsonify
from hyundai_kia_connect_api import VehicleManager, Region

app = Flask(__name__)

# Configuración desde variables de entorno
USERNAME = os.environ.get('KIA_USERNAME')
PASSWORD = os.environ.get('KIA_PASSWORD')
PIN = os.environ.get('KIA_PIN')
SECRET_KEY = os.environ.get('SECRET_KEY')
VEHICLE_ID = os.environ.get('VEHICLE_ID')
REGION = Region.USA # Cambiar si es necesario

def get_vehicle():
    vm = VehicleManager(region=REGION, brand=1, username=USERNAME, password=PASSWORD, pin=PIN)
    vm.check_and_refresh_token()
    # Si tienes el VEHICLE_ID configurado, lo buscamos específicamente
    if VEHICLE_ID:
        return vm.get_vehicle(VEHICLE_ID)
    # Si no, tomamos el primero disponible
    return list(vm.vehicles.values())[0]

def check_auth():
    auth_header = request.headers.get('Authorization')
    return auth_header == SECRET_KEY

@app.route('/lock_car', methods=['POST'])
def lock_car():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        vehicle = get_vehicle()
        vehicle.lock()
        return jsonify({"status": "Success", "message": "Vehicle locked"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/unlock_car', methods=['POST'])
def unlock_car():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        vehicle = get_vehicle()
        vehicle.unlock()
        return jsonify({"status": "Success", "message": "Vehicle unlocked"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/start_climate', methods=['POST'])
def start_climate():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        vehicle = get_vehicle()
        # Configuración por defecto: 72 grados por 10 min
        vehicle.start_climate(set_temp=72, duration=10)
        return jsonify({"status": "Success", "message": "Climate started"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/stop_climate', methods=['POST'])
def stop_climate():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        vehicle = get_vehicle()
        vehicle.stop_climate()
        return jsonify({"status": "Success", "message": "Climate stopped"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
