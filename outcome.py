import pdf2image
import tempfile
import base64

import json
import os
from ollama import chat
from pydantic import BaseModel, Field

from pydantic.json_schema import model_json_schema


class Medform(BaseModel):
    name: str
    answered: bool = Field(description = "The questions in the form were answered")
#    base64_image : str = Field(description="Encoded base64 image string")

class MedformList(BaseModel):
    medforms: list[Medform]

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def process_pdf(pdf_path, output_file=None):
    """
    Process a PDF file by converting it to images and extracting form data.

    Args:
        pdf_path: Path to the PDF file to process
        output_file: Path to the output JSON file (default: pdf_path with .json extension)

    Returns:
        tuple: (output_file_path, results_dict)
    """
    if output_file is None:
        output_file = os.path.splitext(pdf_path)[0] + "_output.json"

    pages = pdf2image.convert_from_path(pdf_path, dpi=600)
    results = []

    for i, page in enumerate(pages, start = 1):

        with tempfile.NamedTemporaryFile(suffix= ".png", delete= False) as tmpfile:
            image_path= tmpfile.name
        print(f"Processing page {i}: {image_path}")
        page.save(image_path, "png")
        base64_image = encode_image(image_path)
        os.remove(tmpfile.name)
        response = chat(
            model = 'llama3.2-vision',
            messages = [{
                    'role': 'user',
                    'content': 'I have this imaege of form and I need to know its name and if it was filled out',
                    'images': [base64_image],
                }
            ],

            format = Medform.model_json_schema()
        )
        form_description = Medform.model_validate_json(response["message"]["content"])
        print(f"Page {i}: {form_description}")

        results.append({
            "page": i,
            "name": form_description.name,
            "answered": form_description.answered,
            "base64_image": base64_image
        })

    # Write results to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {output_file}")
    return output_file, results
       # with open(form_json, 'r') as file:
       #     data = json.load(file)
       # if response["message"]["content"]["name"].contains(data["form"]):
       #     for question in data["questions"]:
       #         response = chat(
       #             model = 'deepseek-ocr:latest',
       #             messages = [{
       #                     'role': 'user',
       #                     'content': 'Get answer to ' [question],
       #                     'images': [base64_image],
       #                 }
       #             ],
       #         )
       #         print(response)


          #  page.save(image_path, "png")

          #  prompt = f"\"Extract answers to multiple choice quetions from this image " + "\""
          #

          #  result = subprocess.run(["ollama", "run", "llama3.2-vision", " ", prompt, image_path ], capture_output=True,)
          #  output_text = result.stdout.decode("utf-8").strip()
          #  if not output_text:
          #      output_text = "[No output received from Ollama]"


          #  with open(f"page_{i}_output.txt", "w", encoding = "utf-8") as f:
          #      f.write(output_text)

          #  print(f"Page processed. Result saved to page_{i}_output.txt")

            #os.remove(image_path)


if __name__ == "__main__":
    # Example usage
    pdf_path = "1.pdf"
    # Uses default output file (1_output.json)
    process_pdf(pdf_path)

    # Or specify custom output file
    # process_pdf(pdf_path, "custom_output.json")
