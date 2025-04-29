import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import gradio as gr

# Load tokenizer and model
model_name = "microsoft/phi-2"
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading model on {device.upper()}...")

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
model.eval()

# Inference function
def generate_response(prompt):
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=500,
                do_sample=True,
                top_p=0.9,
                temperature=0.7
            )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# GUI with dynamic port fallback
def start_gui():
    try:
        gr.Interface(
            fn=generate_response,
            inputs=gr.Textbox(label="Enter your prompt"),
            outputs=gr.Textbox(label="Model response"),
            title="Local Chatbot - Phi-2 (GPU)"
        ).launch(server_port=7860)
    except OSError:
        print("Port 7860 is in use. Trying 7861...")
        gr.Interface(
            fn=generate_response,
            inputs=gr.Textbox(label="Enter your prompt"),
            outputs=gr.Textbox(label="Model response"),
            title="Local Chatbot - Phi-2 (GPU)"
        ).launch(server_port=7861)

if __name__ == "__main__":
    start_gui()
