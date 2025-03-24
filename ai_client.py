from openai import OpenAI
import os

# Class to run chat completion calls using openai

class ChatCompletion:
    def __init__(self, api_key=None):
        
        self.api_key = api_key or os.getenv('DS_API_KEY')
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

    def chat(self, prompt):
        response = self.client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {"role": "system", "content": "You are an experienced financial report analyst"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        stream=False
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content