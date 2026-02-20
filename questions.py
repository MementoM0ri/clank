import json
import os
from ollama import chat
import base64

form_path = "forms/test.json" 



def load_questions(path):
    with open(path, 'r') as file:
        data = json.load(file)
    return data

#    return data['questions']

def get_answers(base64_image, form_path):
    form_json = load_questions(form_path)
    for item in form_json['questions']:

        response = chat(
            model = 'llama3.2-vision',
            messages = [{
                'role' : ' user',
                'content' : 'Get the answer to the question ' [item],
                'images' : [base64_image],
                }
            ]
        )
        print(f"{response}")

if __name__ == '__main__':
    load_questions(form_path)

