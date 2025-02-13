import requests
import tkinter as tk
from tkinter import messagebox

API_KEY = "1548b730d7a84a989e18d6ece4334e5b"  # Replace with your API Key
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def fetch_weather_data(city):
    params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        weather_data = {
            'temperature': f"{data['main']['temp']} °C",
            'humidity': f"{data['main']['humidity']}%",
            'pressure': f"{data['main']['pressure']} hPa",
            'wind_speed': f"{data['wind']['speed']} m/s",
        }
        return weather_data
    else:
        return {'error': data.get('message', 'Unable to fetch data')}


def get_weather():
    city = city_entry.get().strip()
    if city:
        weather_data = fetch_weather_data(city)
        if 'error' in weather_data:
            messagebox.showerror("Error", f"Error: {weather_data['error']}")
        else:
            result_label.config(
                text=(
                    f"Temperature: {weather_data['temperature']}\n"
                    f"Humidity: {weather_data['humidity']}\n"
                    f"Pressure: {weather_data['pressure']}\n"
                    f"Wind Speed: {weather_data['wind_speed']}"
                )
            )
    else:
        messagebox.showwarning("Warning", "Please enter a city name!")


# Create main application window
app = tk.Tk()
app.title("Weather App")
app.geometry("400x300")

# City input
city_label = tk.Label(app, text="Enter City Name:", font=("Arial", 12))
city_label.pack(pady=10)
city_entry = tk.Entry(app, font=("Arial", 12))
city_entry.pack(pady=10)

# Get Weather Button
fetch_button = tk.Button(app, text="Get Weather", font=("Arial", 12), command=get_weather)
fetch_button.pack(pady=10)

# Result Display
result_label = tk.Label(app, text="Weather details will be displayed here", font=("Arial", 12), justify="left")
result_label.pack(pady=20)

# Run the Tkinter event loop
app.mainloop()
