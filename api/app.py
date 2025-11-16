from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route("/_/health", methods=["GET"])
def health():
    # trả 200 để gateway biết app healthy
    return "", 200

OPENWEATHER_KEY = "f213bc4bf06842be76cd76ab053203e3"

def _fetch_weather_from_openweather(params):
    base = "https://api.openweathermap.org/data/2.5/weather"
    params.update({"appid": OPENWEATHER_KEY})
    resp = requests.get(base, params=params, timeout=6)
    resp.raise_for_status()
    return resp.json()

@app.route("/", methods=["GET", "POST"])
def root():
    """
    When invoked via OpenFaaS gateway the function is normally called at the container root.
    If the request contains `city` (or lat&lon) in the query string, do the weather lookup.
    Otherwise return a simple status object (health).
    """
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    units = request.args.get("units", "metric")

    if not (city or (lat and lon)):
        return jsonify({"status": "weather-api alive"})

    if not OPENWEATHER_KEY:
        return jsonify({"error": "Missing OpenWeather API key"}), 500

    try:
        params = {"units": units}
        if city:
            params["q"] = city
        else:
            params["lat"] = lat
            params["lon"] = lon

        data = _fetch_weather_from_openweather(params)
        if "main" not in data:
            return jsonify({"error": "Upstream error", "detail": data}), 502

        result = {
            "name": data.get("name"),
            "description": data.get("weather", [{}])[0].get("description"),
            "temp": data.get("main", {}).get("temp"),
            "humidity": data.get("main", {}).get("humidity"),
            "wind": data.get("wind", {}),
        }
        return jsonify(result)

    except requests.HTTPError as e:
        try:
            body = e.response.json()
        except Exception:
            body = e.response.text
        return jsonify({"error": "upstream_http_error", "detail": body}), getattr(e.response, "status_code", 502)
    except Exception as e:
        return jsonify({"error": "exception", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
