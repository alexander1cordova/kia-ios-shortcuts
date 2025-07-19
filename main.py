import os
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

@app.route('/list_vehicles', methods=['GET'])
def list_vehicles():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        vehicles = vehicle_manager.vehicles
        vehicle_list = [
            {
                "name": v.name,
                "id": v.id,
                "model": v.model,
                "year": v.year
            }
            for v in vehicles.values()
        ]
        return jsonify({"status": "Success", "vehicles": vehicle_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/vehicle_status', methods=['GET'])
def vehicle_status():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        vehicle = vehicle_manager.vehicles[VEHICLE_ID]

        # Compatibilidad máxima de nombres de atributos
        engine_on = getattr(vehicle, "engine_is_running", None) or getattr(vehicle, "engine", None)
        locked = getattr(vehicle, "is_locked", None) or getattr(vehicle, "doorLock", None)
        climate_on = getattr(vehicle, "is_climate_on", None) or getattr(vehicle, "airCtrlOn", None)
        ac_set_temp = getattr(vehicle, "climate_temperature", None) or getattr(vehicle, "airTemp", None)
        interior_temp = getattr(vehicle, "cabin_temperature", None) or getattr(vehicle, "insideTemp", None)
        fuel_level = getattr(vehicle, "fuel_level", None)
        if not fuel_level and hasattr(vehicle, "fuelStatus"):
            fuel_status = getattr(vehicle, "fuelStatus", None)
            if fuel_status and isinstance(fuel_status, dict):
                fuel_level = fuel_status.get("fuelLevel", None)
        range_miles = getattr(vehicle, "range_miles", None)
        if not range_miles and hasattr(vehicle, "fuelStatus"):
            fuel_status = getattr(vehicle, "fuelStatus", None)
            if fuel_status and isinstance(fuel_status, dict):
                range_miles = fuel_status.get("distance", None)
        last_updated = getattr(vehicle, "last_updated_at", None) or getattr(vehicle, "lastStatusDate", None)
        if last_updated:
            last_updated = str(last_updated)

        status = {
            "engineOn": engine_on,
            "locked": locked,
            "climateOn": climate_on,
            "acSetTemperature": ac_set_temp,
            "interiorTemperature": interior_temp,
            "fuelLevel": fuel_level,
            "rangeMiles": range_miles,
            "lastUpdated": last_updated
        }
        return jsonify(status), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/start_climate', methods=['POST'])
def start_climate():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        temp = request.json.get("set_temp", 63)
        duration = request.json.get("duration", 10)
        climate_options = ClimateRequestOptions(set_temp=temp, duration=duration)
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

@app.route('/start_heating', methods=['POST'])
def start_heating():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        heating_options = ClimateRequestOptions(set_temp=80, duration=10)
        result = vehicle_manager.start_climate(VEHICLE_ID, heating_options)
        return jsonify({"status": "Heating started (80°F)", "result": result}), 200
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

@app.route('/start_engine', methods=['POST'])
def start_engine():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.start_engine(VEHICLE_ID)
        return jsonify({"status": "Engine started", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stop_engine', methods=['POST'])
def stop_engine():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.stop_engine(VEHICLE_ID)
        return jsonify({"status": "Engine stopped", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/open_trunk', methods=['POST'])
def open_trunk():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.open_trunk(VEHICLE_ID)
        return jsonify({"status": "Trunk opened", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/close_trunk', methods=['POST'])
def close_trunk():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.close_trunk(VEHICLE_ID)
        return jsonify({"status": "Trunk closed", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/honk_horn', methods=['POST'])
def honk_horn():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.honk(VEHICLE_ID)
        return jsonify({"status": "Horn honked", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/flash_lights', methods=['POST'])
def flash_lights():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.flash_lights(VEHICLE_ID)
        return jsonify({"status": "Lights flashed", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/find_vehicle', methods=['GET'])
def find_vehicle():
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        vehicle = vehicle_manager.vehicles[VEHICLE_ID]
        if hasattr(vehicle, "location") and vehicle.location:
            location = vehicle.location
            return jsonify({"status": "Success", "location": location}), 200
        elif hasattr(vehicle, "get_location"):
            location = vehicle.get_location()
            return jsonify({"status": "Success", "location": location}), 200
        else:
            return jsonify({"error": "Location not available"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Kia Vehicle Control API...")
    app.run(host="0.0.0.0", port=8080)