import os
import json
from flask import Request, Response
from hyundai_kia_connect_api import VehicleManager, ClimateRequestOptions
from hyundai_kia_connect_api.exceptions import AuthenticationError

USERNAME = os.environ.get("KIA_USERNAME")
PASSWORD = os.environ.get("KIA_PASSWORD")
PIN = os.environ.get("KIA_PIN")
SECRET_KEY = os.environ.get("SECRET_KEY")
VEHICLE_ID = os.environ.get("VEHICLE_ID")

def handler(request: Request) -> Response:
    path = request.path
    method = request.method
    auth = request.headers.get("Authorization")

    if auth != SECRET_KEY:
        return Response(json.dumps({"error": "Unauthorized"}), status=403, mimetype="application/json")

    try:
        vehicle_manager = VehicleManager(
            region=3,
            brand=1,
            username=USERNAME,
            password=PASSWORD,
            pin=str(PIN)
        )
        vehicle_manager.check_and_refresh_token()

        # /vehicle_status
        if path == "/vehicle_status" and method == "GET":
            vehicle_manager.force_refresh_vehicles_states(VEHICLE_ID)
            vehicle = vehicle_manager.get_vehicle(VEHICLE_ID)

            air_temp = vehicle.air_temperature[0] if vehicle.air_temperature else None
            temp_unit = vehicle.air_temperature[1] if vehicle.air_temperature else None

            status = {
                "locked": vehicle.is_locked,
                "engineOn": vehicle.engine_is_running,
                "fuelLevel": vehicle.fuel_level,
                "interiorTemperature": air_temp,
                "temperatureUnit": temp_unit,
                "rangeMiles": vehicle.fuel_driving_range,
                "odometer": vehicle.odometer_value,
                "acSetTemperature": vehicle.climate_temperature,
                "climateOn": vehicle.is_climate_on
            }

            return Response(json.dumps(status), status=200, mimetype="application/json")

        # /start_climate
        if path == "/start_climate" and method == "POST":
            climate_options = ClimateRequestOptions(set_temp=63, duration=10)
            result = vehicle_manager.start_climate(VEHICLE_ID, climate_options)
            return Response(json.dumps({"status": "Climate started", "result": result}), status=200)

        # /stop_climate
        if path == "/stop_climate" and method == "POST":
            result = vehicle_manager.stop_climate(VEHICLE_ID)
            return Response(json.dumps({"status": "Climate stopped", "result": result}), status=200)

        # /start_heating
        if path == "/start_heating" and method == "POST":
            climate_options = ClimateRequestOptions(set_temp=80, duration=10)
            result = vehicle_manager.start_climate(VEHICLE_ID, climate_options)
            return Response(json.dumps({"status": "Heating started (80°F)", "result": result}), status=200)

        # /lock_car
        if path == "/lock_car" and method == "POST":
            result = vehicle_manager.lock(VEHICLE_ID)
            return Response(json.dumps({"status": "Car locked", "result": result}), status=200)

        # /unlock_car
        if path == "/unlock_car" and method == "POST":
            result = vehicle_manager.unlock(VEHICLE_ID)
            return Response(json.dumps({"status": "Car unlocked", "result": result}), status=200)

        # /find_car
        if path == "/find_car" and method == "POST":
            result = vehicle_manager.find_car(VEHICLE_ID)
            return Response(json.dumps({"status": "Find car signal sent", "result": result}), status=200)

        return Response(json.dumps({"error": f"Endpoint '{path}' not found"}), status=404)

    except AuthenticationError as e:
        return Response(json.dumps({"error": f"Authentication failed: {str(e)}"}), status=401)

    except Exception as e:
        import traceback
        return Response(json.dumps({
            "error": "Internal server error",
            "details": traceback.format_exc()
        }), status=500, mimetype="application/json")