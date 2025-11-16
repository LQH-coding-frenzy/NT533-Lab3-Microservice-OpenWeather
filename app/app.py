from flask import Flask, render_template, request, redirect, url_for
import os
import requests

app = Flask(__name__, template_folder="templates")

@app.route("/_/health", methods=["GET"])
def health():
    return "", 200

OPENFAAS_GATEWAY = os.getenv("OPENFAAS_GATEWAY", "http://127.0.0.1:8080")
API_FUNCTION_NAME = os.getenv("API_FUNCTION_NAME", "weather-api")

@app.route("/", methods=["GET"]) 
def index():
    return render_template("index.html")

@app.route("/result", methods=["POST"])
def result():
    city = request.form.get("city", "").strip()
    lat = request.form.get("lat", "").strip()
    lon = request.form.get("lon", "").strip()
    units = request.form.get("units", "metric")

    base = OPENFAAS_GATEWAY.rstrip('/')
    target = f"{base}/function/{API_FUNCTION_NAME}"

    params = {"units": units}
    if city:
        params["city"] = city
    elif lat and lon:
        params["lat"] = lat
        params["lon"] = lon
    else:
        return render_template("result.html", error="Vui lòng nhập city hoặc lat & lon.")

    try:
        resp = requests.get(target, params=params, timeout=6)
        try:
            data = resp.json()
        except Exception:
            data = {"error": "Không thể parse JSON từ weather-api", "raw": resp.text}

        if resp.status_code != 200:
            return render_template("result.html", error=data)

        return render_template("result.html", data=data)

    except requests.exceptions.RequestException as e:
        return render_template("result.html", error=str(e))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)