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
            fuel = vs.get('fuelLevel', None)
            engine = vs.get('engine', None)
            locked = vs.get('doorLock', None)
            odometer = vs.get('odometer', {}).get('value', None)
            range_miles = vs.get('distanceToEmpty', {}).get('value', None)
            air_temp = climate.get('airTemp', {})
            climate_set = air_temp.get('hvacTempType', None)
            interior_temp = air_temp.get('value', None)

            status = {
                "locked": locked,
                "engineOn": engine,
                "fuelLevel": fuel,
                "interiorTemperature": interior_temp,
                "rangeMiles": range_miles,
                "odometer": odometer,
                "acSetTemperature": climate_set,
                "climateOn": vs.get('airCtrl', None)
            }
        else:
            status = {
                "locked": getattr(vehicle, "is_locked", None),
                "engineOn": getattr(vehicle, "engine_is_running", None),
                "fuelLevel": getattr(vehicle, "fuel_level", None),
                "interiorTemperature": getattr(vehicle, "interior_temperature", None),
                "rangeMiles": getattr(vehicle, "fuel_driving_range", None),
                "odometer": getattr(vehicle, "odometer_value", None),
                "acSetTemperature": getattr(vehicle, "climate_temperature", None),
                "climateOn": getattr(vehicle, "is_climate_on", None)
            }

        print(status)
        return jsonify(status), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /vehicle_status:\n{error_trace}")
        return jsonify({"error": error_trace}), 500

# Los demás endpoints se mantienen tal como ya están definidos...
# start_climate, stop_climate, lock_car, unlock_car, aftermarket_trunk, start_heating
# No se repiten aquí porque no fueron modificados y ya funcionan en tu versión actual.

if __name__ == "__main__":
    print("Starting Kia Vehicle Control API...")
    app.run(host="0.0.0.0", port=8080)