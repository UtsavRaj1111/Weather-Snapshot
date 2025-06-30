from flask import Flask, render_template, request
import requests  # call the api 
import os
from dotenv import load_dotenv # read aur secret api
import time
from datetime import datetime, timedelta #handle past weather

load_dotenv()

app = Flask(__name__)
API_KEY = os.getenv("OPENWEATHER_API_KEY")  #load the api key

@app.route("/", methods=["GET", "POST"])  #main route
def index():
    weather = {}
    forecast_data = []
    history_data = []

    if request.method == "POST":
        city = request.form.get("city")
        mode = request.form.get("mode") or "current"

        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(weather_url)  

        if response.status_code == 200:
            data = response.json()
            lat = data["coord"]["lat"]
            lon = data["coord"]["lon"]

            # Get AQI data
            aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
            aqi_response = requests.get(aqi_url)
            aqi = None
            if aqi_response.status_code == 200:
                aqi_data = aqi_response.json()
                aqi = aqi_data["list"][0]["main"]["aqi"]

            weather = {
                "city": city,
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "humidity": data["main"]["humidity"],
                "feels_like": data["main"]["feels_like"],
                "wind_speed": data["wind"]["speed"],
                "country": data["sys"]["country"],
                "time": time.strftime("%I:%M %p"),
                "aqi": aqi
            }

            if mode == "forecast":
                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
                forecast_response = requests.get(forecast_url)
                if forecast_response.status_code == 200:
                    forecast_json = forecast_response.json()
                    for item in forecast_json["list"][:8]:
                        forecast_data.append({
                            "time": item["dt_txt"],
                            "temp": item["main"]["temp"],
                            "desc": item["weather"][0]["description"],
                            "icon": item["weather"][0]["icon"]
                        })

            elif mode == "past":
                for days_ago in range(1, 4):  # Last 3 days
                    dt = int((datetime.utcnow() - timedelta(days=days_ago)).timestamp())
                    hist_url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={lon}&dt={dt}&appid={API_KEY}&units=metric"
                    hist_response = requests.get(hist_url)
                    if hist_response.status_code == 200:
                        hist_json = hist_response.json()
                        day_data = hist_json.get("data", hist_json.get("hourly", []))
                        if day_data:
                            avg_temp = sum(h["temp"] for h in day_data) / len(day_data)
                            history_data.append({
                                "date": datetime.utcfromtimestamp(dt).strftime("%Y-%m-%d"),
                                "avg_temp": round(avg_temp, 1),
                                "desc": day_data[0]["weather"][0]["description"],
                                "icon": day_data[0]["weather"][0]["icon"]
                            })
        else:
            weather["error"] = "City not found!"  #error handling

    return render_template("index.html", weather=weather, forecast=forecast_data, history=history_data)  #return data to website

if __name__ == "__main__":
    app.run(debug=True)  #start the app
