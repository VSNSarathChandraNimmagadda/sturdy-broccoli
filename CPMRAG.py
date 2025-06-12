import gradio as gr
import requests
from openai import OpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from langchain.utilities import SerpAPIWrapper

# API Keys
SERPER_API_KEY = "21ebf7220b0256281ec6dbb7999426bae6fb8902"
OPENWEATHERMAP_API_KEY = "94e78fe38fd6cb74cdde79334523ad1a"  # 🔁 Replace with your API key
NVIDIA_API_KEY = "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"

# Clients
search = SerpAPIWrapper(params={"engine": "google"}, serpapi_api_key=SERPER_API_KEY)
nvidia_client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)

# Local model setup
LOCAL_MODEL_NAME = "openbmb/MiniCPM4-0.5B"
tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL_NAME, trust_remote_code=True).to("cuda" if torch.cuda.is_available() else "cpu")
model.eval()

# Function: Serper search
def retrieve_context(query):
    try:
        return search.run(query)
    except Exception as e:
        return f"[Error retrieving context: {str(e)}]"

# Function: OpenWeatherMap API
def get_weather(city="Guntur"):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data.get("cod") != 200:
            return f"Weather API Error: {data.get('message', 'Unknown error')}"
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        return f"Weather in {city}: {desc}, Temperature: {temp}°C, Humidity: {humidity}%"
    except Exception as e:
        return f"[Error fetching weather: {str(e)}]"

# Function: Local model Q&A
def local_model_response(message, chat_history):
    context = retrieve_context(f"agriculture or healthcare in Andhra Pradesh: {message}")
    prompt = f"""
You are an AI assistant for agriculture and healthcare in Andhra Pradesh.
Use the following real-time info:
Context: {context}
User Query: {message}
Answer:"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=400, temperature=0.6, top_p=0.9)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    answer = response[len(prompt):].strip()
    return answer

# Function: NVIDIA-based response for general queries
def nvidia_model_response(message, chat_history):
    system_prompt = "You are an AI assistant for agriculture and healthcare in Andhra Pradesh."
    messages = [{"role": "system", "content": system_prompt}]
    for user_msg, bot_msg in chat_history:
        messages.append({"role": "user", "content": user_msg})
        if bot_msg:
            messages.append({"role": "assistant", "content": bot_msg})
    messages.append({"role": "user", "content": message})
    completion = nvidia_client.chat.completions.create(
        model="deepseek-ai/deepseek-r1-distill-qwen-32b",
        messages=messages,
        temperature=0.6,
        top_p=0.7,
        max_tokens=4096,
        stream=False
    )
    return completion.choices[0].message.content
def local_model_response_with_context(domain, message, chat_history):
    context = retrieve_context(f"{domain} in Andhra Pradesh: {message}")
    prompt = f"""
You are an AI assistant specializing in {domain} in Andhra Pradesh.
Use the following real-time information to help answer the user's query:
Context: {context}
User Query: {message}
Answer:"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=400, temperature=0.6, top_p=0.9)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    answer = response[len(prompt):].strip()
    return answer


# Function: Decision-making dashboard (Weather + Soil + Crop)
def irrigation_advice(city, soil_type, crop_type, chat_history=[]):
    weather_data = get_weather(city)
    prompt = f"""
You are an AI expert in agriculture for Andhra Pradesh.

Current weather data:
{weather_data}

Soil type: {soil_type}
Crop type: {crop_type}

Provide proper steps based on the present weather conditions to be taken now so that the crop plants can grow healthy. 
Be precise and concise in your reasoning.
"""
    messages = [{"role": "system", "content": "You are an expert in weather-based irrigation for Andhra Pradesh."},
                {"role": "user", "content": prompt}]
    completion = nvidia_client.chat.completions.create(
        model="deepseek-ai/deepseek-r1-distill-qwen-32b",
        messages=messages,
        temperature=0.6,
        top_p=0.8,
        max_tokens=800
    )
    return f"{weather_data}\n\nAdvice:\n{completion.choices[0].message.content.strip()}"

# Gradio UI
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🌾🩺 Smart AI Assistant for Andhra Pradesh")
    
    with gr.Tab("🌱 Agriculture"):
        gr.Markdown("Get real-time agriculture information using MiniCPM + Serper.")
        agri_chatbot = gr.Chatbot(bubble_full_width=False)
        agri_interface = gr.ChatInterface(fn=local_model_response, chatbot=agri_chatbot)
    
    with gr.Tab("🏥 Healthcare"):
        gr.Markdown("Healthcare help powered by NVIDIA's model.")
        health_chatbot = gr.Chatbot(bubble_full_width=False)
        health_interface = gr.ChatInterface(fn=lambda msg, hist: local_model_response_with_context("healthcare", msg, hist), chatbot=health_chatbot)


    with gr.Tab("☁️ Weather Dashboard"):
        gr.Markdown("Live weather update using OpenWeatherMap.")
        city_input = gr.Textbox(label="City", value="Guntur")
        weather_output = gr.Textbox(label="Weather Info")
        weather_button = gr.Button("Get Weather")
        weather_button.click(fn=get_weather, inputs=[city_input], outputs=[weather_output])

    with gr.Tab("🧠 Decision-Making Dashboard"):
        gr.Markdown("Advisory on irrigation based on weather, soil, and crop data.")
        city = gr.Textbox(label="City", value="Guntur")
        soil_type = gr.Dropdown(["Sandy", "Clay", "Loamy", "Black", "Red"], label="Soil Type")
        crop_type = gr.Textbox(label="Crop Type", placeholder="e.g., Rice, Cotton, etc.")
        decision_output = gr.Textbox(label="Irrigation Advisory", lines=8)
        decision_btn = gr.Button("Generate Advice")
        decision_btn.click(fn=irrigation_advice, inputs=[city, soil_type, crop_type], outputs=[decision_output])

if __name__ == "__main__":
    demo.launch()
