import tkinter as tk
import requests
API_KEY = '94e78fe38fd6cb74cdde79334523ad1a'
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
def get_weather():
    city_name = entry.get() 
    url = f"{BASE_URL}?q={city_name}&appid={API_KEY}&units=metric"  
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()  
        main = data['main']
        weather = data['weather'][0]
        wind = data['wind']
        temperature = main['temp']
        humidity = main['humidity']
        description = weather['description']
        wind_speed = wind['speed'] 
        label_temp.config(text=f"Temperature: {temperature}°C")
        label_humidity.config(text=f"Humidity: {humidity}%")
        label_description.config(text=f"Description: {description.capitalize()}")
        label_wind_speed.config(text=f"Wind Speed: {wind_speed} m/s")
    else:
        label_temp.config(text="Error: City not found.")
        label_humidity.config(text="")
        label_description.config(text="")
        label_wind_speed.config(text="")
root = tk.Tk()
root.title("Weather App")
entry = tk.Entry(root, width=20)
entry.pack(pady=10)
button = tk.Button(root, text="Get Weather", command=get_weather)
button.pack(pady=10)
label = tk.Label(root, text="Weather details are:", font=("Helvetica", 14))
label.pack()
label_temp = tk.Label(root, text="Temperature: ", font=("Helvetica", 12))
label_temp.pack()
label_humidity = tk.Label(root, text="Humidity: ", font=("Helvetica", 12))
label_humidity.pack()
label_description = tk.Label(root, text="Description: ", font=("Helvetica", 12))
label_description.pack()
label_wind_speed = tk.Label(root, text="Wind Speed: ", font=("Helvetica", 12))
label_wind_speed.pack()
root.mainloop()
