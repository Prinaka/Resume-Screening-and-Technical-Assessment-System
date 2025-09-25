from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()   


def call_kimi(prompt):
    client = Groq(api_key=os.environ["GROQ_API"])
    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",
        messages=[{"role": "user","content": prompt}],
        temperature=0.4,
        )
    return response.choices[0].message.content


def call_llama(prompt):
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API"],
        )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user","content": prompt}],
        max_tokens=512,
        )
    return response.choices[0].message.content