import os
import json
from hyundai_kia_connect_api import VehicleManager, ClimateRequestOptions
from hyundai_kia_connect_api.exceptions import AuthenticationError

USERNAME = os.environ.get("KIA_USERNAME")
PASSWORD = os.environ.get("KIA_PASSWORD")
PIN = os.environ.get("KIA_PIN")
SECRET_KEY = os.environ.get("SECRET_KEY")
VEHICLE_ID = os.environ.get("VEHICLE_ID")

def handler(request):
    path = request.path
    method = request.method
    auth = request.headers.get("authorization")

    if auth != SECRET_KEY:
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Unauthorized"})
        }

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

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(status)
            }

        # /start_climate
        if path == "/start_climate" and method == "POST":
            climate_options = ClimateRequestOptions(set_temp=63, duration=10)
            result = vehicle_manager.start_climate(VEHICLE_ID, climate_options)
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "Climate started", "result": result})
            }

        # /stop_climate
        if path == "/stop_climate" and method == "POST":
            result = vehicle_manager.stop_climate(VEHICLE_ID)
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "Climate stopped", "result": result})
            }

        # /start_heating
        if path == "/start_heating" and method == "POST":
            climate_options = ClimateRequestOptions(set_temp=80, duration=10)
            result = vehicle_manager.start_climate(VEHICLE_ID, climate_options)
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "Heating started (80°F)", "result": result})
            }

        # /lock_car
        if path == "/lock_car" and method == "POST":
            result = vehicle_manager.lock(VEHICLE_ID)
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "Car locked", "result": result})
            }

        # /unlock_car
        if path == "/unlock_car" and method == "POST":
            result = vehicle_manager.unlock(VEHICLE_ID)
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "Car unlocked", "result": result})
            }

        # /find_car
        if path == "/find_car" and method == "POST":
            result = vehicle_manager.find_car(VEHICLE_ID)
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "Find car signal sent", "result": result})
            }

        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Endpoint not found"})
        }

    except AuthenticationError as e:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": f"Authentication failed: {str(e)}"})
        }

    except Exception as e:
        import traceback
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "details": traceback.format_exc()
            })
        }