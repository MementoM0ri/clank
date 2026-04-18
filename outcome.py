import pdf2image
import tempfile
import base64

import json
import os
from ollama import chat
from pydantic import BaseModel, Field
from difflib import get_close_matches

from pydantic.json_schema import model_json_schema


class Medform(BaseModel):
    name: str
    answered: bool = Field(description = "The questions in the form were answered")
#    base64_image : str = Field(description="Encoded base64 image string")

class MedformList(BaseModel):
    medforms: list[Medform]

class FormAnswers(BaseModel):
    answers: dict[str, str] = Field(description="Dictionary mapping questions to their answers")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def match_form_name(extracted_name, forms_dir="forms"):
    """
    Match the extracted form name to an actual form file in the forms directory.

    Args:
        extracted_name: The form name extracted by Ollama
        forms_dir: Directory containing form JSON files

    Returns:
        Path to matched form JSON file or None if no match found
    """
    if not os.path.exists(forms_dir):
        print(f"Forms directory '{forms_dir}' not found")
        return None

    # Get all JSON files in forms directory
    form_files = [f for f in os.listdir(forms_dir) if f.endswith('.json')]

    if not form_files:
        print(f"No JSON files found in '{forms_dir}'")
        return None

    # Extract form names from filenames (remove .json and replace _ with space)
    form_names = [os.path.splitext(f)[0].replace('_', ' ') for f in form_files]

    # Try to find close matches (case-insensitive)
    extracted_name_lower = extracted_name.lower()
    form_names_lower = [name.lower() for name in form_names]
    matches = get_close_matches(extracted_name_lower, form_names_lower, n=1, cutoff=0.6)

    if matches:
        matched_name_lower = matches[0]
        # Find the original form name (with proper case)
        matched_index = form_names_lower.index(matched_name_lower)
        matched_name = form_names[matched_index]
        # Convert back to filename
        matched_file = matched_name.replace(' ', '_') + '.json'
        matched_path = os.path.join(forms_dir, matched_file)
        print(f"Matched '{extracted_name}' to '{matched_name}' ({matched_file})")
        return matched_path

    print(f"No match found for '{extracted_name}'")
    return None


def extract_form_answers(base64_image, form_json_path):
    """
    Extract raw answers (letters or numbers) from a form image one question at a time using Ollama.

    Args:
        base64_image: Base64 encoded image of the form
        form_json_path: Path to the form JSON template

    Returns:
        Dictionary containing questions and their raw answers (letters for multiple choice, numbers for scales)
    """
    # Load form template
    with open(form_json_path, 'r', encoding='utf-8') as f:
        form_data = json.load(f)

    form_name = form_data.get("form", "Unknown Form")
    questions = form_data.get("questions", [])
    answer_format = form_data.get("answer_format", "unknown")

    if not questions:
        print(f"No questions found in {form_json_path}")
        return None

    print(f"\nExtracting answers for {form_name} ({len(questions)} questions, format: {answer_format})...")
    print("Processing one question at a time...")

    # Build instructions based on answer format
    if answer_format == "numeric_scale":
        scale_info = form_data.get("scale", {})
        min_val = scale_info.get("min", 0)
        max_val = scale_info.get("max", 10)
        base_instruction = f"Look at the form image and find the number ({min_val}-{max_val}) that was circled or marked. Return ONLY the number as an integer, or null if no answer is marked."

    elif answer_format == "multiple_choice":
        base_instruction = "Look at the form image and find which option letter (A, B, C, D, E, or F) was circled or selected. Return ONLY the letter as a string (e.g., 'A'), or null if no answer is marked."

    elif answer_format == "yes_sometimes_no":
        base_instruction = "Look at the form image and find which option was selected (YES, SOMETIMES, or NO). Return ONLY the text as a string (e.g., 'YES'), or null if no answer is marked."

    elif answer_format == "checkbox_multiple":
        base_instruction = "Look at the form image and find which checkbox number was selected. Return ONLY the number as an integer, or null if no answer is marked."

    elif answer_format == "mixed":
        base_instruction = "Look at the form image and find what was marked (letter, number, or Yes/No). Return the value in the appropriate format (letter as string, number as integer), or null if no answer is marked."

    else:
        base_instruction = "Look at the form image and find what was circled or marked. Return the value exactly as it appears, or null if no answer is marked."

    answers = {}

    # Process each question one at a time
    for i, question in enumerate(questions, start=1):
        if isinstance(question, dict):
            section = question.get("section", "")
            text = question.get("text", "")
            question_text = text
            question_display = f"{section}: {text}" if section else text
        else:
            question_text = question
            question_display = question

        print(f"  Processing Q{i}/{len(questions)}: {question_display[:60]}...")

        # Create prompt for this specific question
        prompt = f"""Form: {form_name}

Question {i}: {question_display}

{base_instruction}

Return a JSON object with a single key "answer" containing the value.

Example: {{"answer": 5}} or {{"answer": "A"}} or {{"answer": null}}

Return ONLY the JSON object, nothing else."""

        try:
            response = chat(
                model='minicpm-v',
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [base64_image],
                }],
                format='json'
            )

            # Parse the response
            response_text = response["message"]["content"]
            result = json.loads(response_text)
            answer_value = result.get("answer", None)

            answers[question_text] = answer_value
            print(f"    → Answer: {answer_value}")

        except json.JSONDecodeError as e:
            print(f"    → Warning: Could not parse response for Q{i}: {e}")
            answers[question_text] = None
        except Exception as e:
            print(f"    → Error processing Q{i}: {e}")
            answers[question_text] = None

    return {
        "form_name": form_name,
        "form_template": form_json_path,
        "answer_format": answer_format,
        "answers": answers,
        "questions": questions
    }


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

    pages = pdf2image.convert_from_path(pdf_path, dpi=300)
    results = []

    for i, page in enumerate(pages, start = 1):

        with tempfile.NamedTemporaryFile(suffix= ".png", delete= False) as tmpfile:
            image_path= tmpfile.name
        print(f"Processing page {i}: {image_path}")
        page.save(image_path, "png")
        base64_image = encode_image(image_path)
        os.remove(tmpfile.name)
        response = chat(
            model = 'minicpm-v',
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

        # Create result entry for this page
        page_result = {
            "page": i,
            "name": form_description.name,
            "answered": form_description.answered,
            "base64_image": base64_image
        }

        # If form is answered, try to match it and extract answers
        if form_description.answered:
            matched_form = match_form_name(form_description.name)
            if matched_form:
                answers_data = extract_form_answers(base64_image, matched_form)
                if answers_data:
                    page_result["extracted_answers"] = answers_data
                    print(f"Successfully extracted answers for page {i}")
            else:
                print(f"Could not match form '{form_description.name}' to any template")

        results.append(page_result)

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
    pdf_path = "o_test.pdf"
    # Uses default output file (o_test_output.json)
    process_pdf(pdf_path)

    # Or specify custom output file
    # process_pdf(pdf_path, "custom_output.json")
