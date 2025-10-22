# chat_loop.py
from openai import OpenAI
import json, os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama")
)
MODEL = os.getenv("OPENAI_MODEL", "llama3.1:8b")

history = []
print("💬 EHD Optimizer Chat - type 'exit' to quit")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    # GPTに送る（履歴も渡す）
    messages = [{"role": "system", "content": "You are an optimization assistant for EHD thrusters."}]
    for h in history:
        messages.append({"role": "user", "content": h["user"]})
        messages.append({"role": "assistant", "content": h["assistant"]})
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=400,
    )
    content = response.choices[0].message.content.strip()
    print("🤖:", content)
    history.append({"user": user_input, "assistant": content})