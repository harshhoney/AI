import os 
from pathlib import Path
from dotenv import load_dotenv
from groq  import Groq

load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("API key kaha hai bhai")

client = Groq(api_key=my_api_key)
model="openai/gpt-oss-120b"
role="user"
prompt="Hey!"

message_systen={
    "role" : "system",
    "content" : "You are office manager"
}

message={
    "role" : role,
    "content" : prompt
}

messages = [message_systen,message]
response = client.chat.completions.create(model= model,messages = messages,temperature = 2)
answer = response.choices[0].message.content
print(answer)