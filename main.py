import os
from flask import Flask, request, jsonify
from hyundai_kia_connect_api import VehicleManager, ClimateRequestOptions
from hyundai_kia_connect_api.exceptions import AuthenticationError

app = Flask(__name__)

# Credenciales desde variables de entorno
USERNAME = os.environ.get('KIA_USERNAME')
PASSWORD = os.environ.get('KIA_PASSWORD')
PIN = os.environ.get('KIA_PIN')
SECRET_KEY = os.environ.get('SECRET_KEY')
VEHICLE_ID = os.environ.get("VEHICLE_ID")

if not USERNAME or not PASSWORD or not PIN or not SECRET_KEY:
    raise ValueError("Missing one or more required environment variables.")

# Inicializa el VehicleManager
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
        data = {
            "name": vehicle.name,
            "model": vehicle.model,
            "odometer_miles": getattr(vehicle, "_odometer_value", None),
            "car_battery_percentage": getattr(vehicle, "car_battery_percentage", None),
            "engine_is_running": getattr(vehicle, "engine_is_running", None),
            "is_locked": getattr(vehicle, "is_locked", None),
            "air_temperature_f": getattr(vehicle, "_air_temperature_value", None),
            "air_control_is_on": getattr(vehicle, "air_control_is_on", None),
            "fuel_level_percent": getattr(vehicle, "fuel_level", None),
            "fuel_driving_range_miles": getattr(vehicle, "_fuel_driving_range_value", None),
            "tire_pressure_warning": getattr(vehicle, "tire_pressure_all_warning_is_on", None),
            "washer_fluid_warning": getattr(vehicle, "washer_fluid_warning_is_on", None),
            "brake_fluid_warning": getattr(vehicle, "brake_fluid_warning_is_on", None),
            "doors": {
                "front_left_locked": getattr(vehicle, "front_left_door_is_locked", None),
                "front_right_locked": getattr(vehicle, "front_right_door_is_locked", None),
                "back_left_locked": getattr(vehicle, "back_left_door_is_locked", None),
                "back_right_locked": getattr(vehicle, "back_right_door_is_locked", None),
                "front_left_open": getattr(vehicle, "front_left_door_is_open", None),
                "front_right_open": getattr(vehicle, "front_right_door_is_open", None),
                "back_left_open": getattr(vehicle, "back_left_door_is_open", None),
                "back_right_open": getattr(vehicle, "back_right_door_is_open", None),
                "trunk_open": getattr(vehicle, "trunk_is_open", None),
                "hood_open": getattr(vehicle, "hood_is_open", None)
            },
            "location": {
                "lat": getattr(vehicle, "_location_latitude", None),
                "lon": getattr(vehicle, "_location_longitude", None),
                "last_set_time": str(getattr(vehicle, "_last_set_time", None)),
            },
            "dtc_codes": getattr(vehicle, "dtc_descriptions", None),
            "last_updated": str(getattr(vehicle, "last_updated_at", None))
        }
        print("==== VEHICLE STATUS CLEAN ====")
        print(data)
        print("==============================")
        return jsonify(data), 200
    except Exception as e:
        print(f"Error in /vehicle_status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/start_climate', methods=['POST'])
def start_climate():
    print("Received request to /start_climate")
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        climate_options = ClimateRequestOptions(
            set_temp=72,  # puedes cambiar la temperatura aquí
            duration=10
        )
        result = vehicle_manager.start_climate(VEHICLE_ID, climate_options)
        return jsonify({"status": "Climate started", "result": result}), 200
    except Exception as e:
        print(f"Error in /start_climate: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stop_climate', methods=['POST'])
def stop_climate():
    print("Received request to /stop_climate")
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.stop_climate(VEHICLE_ID)
        return jsonify({"status": "Climate stopped", "result": result}), 200
    except Exception as e:
        print(f"Error in /stop_climate: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/unlock_car', methods=['POST'])
def unlock_car():
    print("Received request to /unlock_car")
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.unlock(VEHICLE_ID)
        return jsonify({"status": "Car unlocked", "result": result}), 200
    except Exception as e:
        print(f"Error in /unlock_car: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/lock_car', methods=['POST'])
def lock_car():
    print("Received request to /lock_car")
    if request.headers.get("Authorization") != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403
    try:
        vehicle_manager.update_all_vehicles_with_cached_state()
        result = vehicle_manager.lock(VEHICLE_ID)
        return jsonify({"status": "Car locked", "result": result}), 200
    except Exception as e:
        print(f"Error in /lock_car: {e}")
        return jsonify({"error": str(e)}), 500

# Puedes agregar más endpoints según tus necesidades

if __name__ == "__main__":
    print("Starting Kia Vehicle Control API...")
    app.run(host="0.0.0.0", port=8080)