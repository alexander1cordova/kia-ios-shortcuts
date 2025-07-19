import os
import time
from flask import Flask, request, jsonify
from hyundai_kia_connect_api import VehicleManager, ClimateRequestOptions
from hyundai_kia_connect_api.exceptions import AuthenticationError

app = Flask(__name__)

USERNAME = os.environ.get('KIA_USERNAME')
PASSWORD = os.environ.get('KIA_PASSWORD')
PIN = os.environ.get('KIA_PIN')
SECRET_KEY = os.environ.get("SECRET_KEY")
VEHICLE_ID = os.environ.get("VEHICLE_ID")

if not USERNAME or not PASSWORD or not PIN or not SECRET_KEY:
    raise ValueError("Missing one or more required environment variables.")

vehicle_manager = VehicleManager(
    region=3,  # North America
    brand=1,   # KIA
    username=USERNAME,
    password=PASSWORD,
    pin=str(PIN)
)

try:
    print("Attempting to authenticate and refresh token...")
    vehicle_manager.check_and_refresh_token()
    print("Token refreshed successfully.")
    print("Updating vehicle states...")
    vehicle_manager.update_all_vehicles_with_cached_state()
    print(f"Connected! Found {len(vehicle_manager.vehicles)} vehicle(s).")
except AuthenticationError as e:
    print(f"Failed to authenticate: {e}")
    exit(1)
except Exception as e:
    print(f"Unexpected error during initialization: {e}")
    exit(1)

if not VEHICLE_ID:
    if not vehicle_manager.vehicles:
        raise ValueError("No vehicles found in the account. Please ensure your Kia account has at least one vehicle.")
    VEHICLE_ID = next(iter(vehicle_manager.vehicles.keys()))
    print(f"No VEHICLE_ID provided. Using the first vehicle found: {VEHICLE_ID}")

@app.before_request
def log_request_info():
    print(f"Incoming request: {request.method} {request.url}")

@app.route('/', methods=['GET'])
def root():
    return jsonify({"status": "Welcome to the Kia Vehicle Control API"}), 200

@app.route('/vehicle_status', methods=['GET'])
def vehicle_status():
    print("Received request to /vehicle_status")

    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        vehicle = vehicle_manager.vehicles[VEHICLE_ID]
        rpt = getattr(vehicle, 'vehicleStatusRpt', None)
        status = {}

        if rpt:
            vs = rpt.get('vehicleStatus', {})
            climate = vs.get('climate', {})
            distance = vs.get('distanceToEmpty', {})
            fuel = vs.get('fuelLevel', None)
            engine = vs.get('engine', None)
            locked = vs.get('doorLock', None)
            date = rpt.get('reportDate', {}).get('utc', None)

            status = {
                "locked": locked,
                "lastUpdated": date,
                "engineOn": engine,
                "fuelLevel": fuel,
                "interiorTemperature": climate.get('airTemp', {}).get('value', None),
                "rangeMiles": distance.get('value', None),
                "acSetTemperature": None,
                "climateOn": vs.get('airCtrl', None)
            }
        else:
            # Fallback: atributos directos del objeto
            status = {
                "locked": getattr(vehicle, "is_locked", None),
                "lastUpdated": str(getattr(vehicle, "last_updated_at", None)),
                "engineOn": getattr(vehicle, "engine_is_running", None),
                "fuelLevel": getattr(vehicle, "fuel_level", None),
                "interiorTemperature": getattr(vehicle, "interior_temperature", None),
                "rangeMiles": getattr(vehicle, "range_miles", None),
                "acSetTemperature": getattr(vehicle, "climate_temperature", None),
                "climateOn": getattr(vehicle, "is_climate_on", None)
            }

        print(status)
        return jsonify(status), 200
    except Exception as e:
        print(f"Error in /vehicle_status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/start_climate', methods=['POST'])
def start_climate():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        climate_options = ClimateRequestOptions(
            set_temp=63,
            duration=10
        )
        result = vehicle_manager.start_climate(VEHICLE_ID, climate_options)
        return jsonify({"status": "Climate started", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stop_climate', methods=['POST'])
def stop_climate():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.stop_climate(VEHICLE_ID)
        return jsonify({"status": "Climate stopped", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/unlock_car', methods=['POST'])
def unlock_car():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.unlock(VEHICLE_ID)
        return jsonify({"status": "Car unlocked", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/lock_car', methods=['POST'])
def lock_car():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.lock(VEHICLE_ID)
        return jsonify({"status": "Car locked", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ENDPOINT PARA ABRIR PUERTA TRASERA CON DESBLOQUEO TRIPLE ---
@app.route('/open_trunk', methods=['POST'])
def open_trunk():
    print("Received request to /open_trunk")
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        # Enviar señal de desbloqueo tres veces con un pequeño delay
        results = []
        for i in range(3):
            result = vehicle_manager.unlock(VEHICLE_ID)
            results.append(result)
            print(f"Unlock command {i+1} sent.")
            time.sleep(1)  # 1 segundo entre comandos (ajusta si necesitas más/menos delay)
        return jsonify({"status": "Trunk opening command sent (triple unlock)", "results": results}), 200
    except Exception as e:
        print(f"Error in /open_trunk: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Kia Vehicle Control API...")
    app.run(host="0.0.0.0", port=8080)