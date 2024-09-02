# utils.py

import csv
import json
import re
import os
import time
from openai import OpenAI
from datetime import datetime
from string import Template


def query_openai_api(messages, model, temperature):
    """
    Queries the OpenAI API with the given messages and model.
    
    Args:
        messages (list): List of messages to send to the API.
        model (str): Model to use for the API call.
        temperature (float): Temperature to use for the API call.
    
    Returns:
        str: The content of the API response.
    """
    #print("Using OpenAI API")
    client = OpenAI(
        organization=os.getenv("OPENAI_ORG_ID"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Remove the "openai/" prefix from the model name
    model_name = model.replace("openai/", "")

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": message["role"],
                "content": [
                    {
                        "type": "text",
                        "text": message["content"]
                    }
                ]
            }
            for message in messages
        ],
        temperature=temperature,
        max_tokens=1024,
        top_p=0,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    return completion.choices[0].message.content

def read_template_from_file(file_path, substitutions={}):
    """
    Reads a template from a file and substitutes any placeholders.
    
    Args:
        file_path (str): Path to the template file.
        substitutions (dict): Dictionary of substitutions to make in the template.
    
    Returns:
        str: The template with substitutions made.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        template_string = file.read()
        template = Template(template_string)
        return template.substitute(substitutions)

def read_csv(file_path, delimiter=';'):
    """
    Reads a CSV file and returns the headers and rows.
    
    Args:
        file_path (str): Path to the CSV file.
        delimiter (str): Delimiter used in the CSV file.
    
    Returns:
        tuple: Headers and rows of the CSV file.
    """
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=delimiter)
        headers = next(reader)  # Skip the header row
        return headers, list(reader)

def extract_and_validate_json(data):
    """
    Extracts and validates JSON data from a string.
    
    Args:
        data (str): String containing JSON data.
    
    Returns:
        dict: Parsed JSON data.
    """
    if isinstance(data, dict):
        return data  # Already a dictionary, return as is.
    try:
        # Assuming data is a string that needs to be parsed
        json_str = re.search(r'\{.*\}', data, re.DOTALL).group()
        return json.loads(json_str)
    except (re.error, AttributeError, json.JSONDecodeError) as e:
        #print(f"Error extracting or decoding JSON: {e}")
        return None

def load_query_template(template_path, binomial_name):
    """
    Loads a query template and substitutes the binomial name.
    
    Args:
        template_path (str): Path to the template file.
        binomial_name (str): Binomial name to substitute in the template.
    
    Returns:
        str: The query message with the binomial name substituted.
    """
    with open(template_path, 'r') as file:
        template = file.read()
    # Replace the placeholder with the actual binomial name
    query_message = template.format(binomial_name=binomial_name)
    return query_message

def write_prediction(output_file, prediction, model_used, template_path):
    """
    Writes a prediction to a CSV file.
    
    Args:
        output_file (str): Path to the output CSV file.
        prediction (dict): Prediction data to write.
        model_used (str): Model used for the prediction.
        template_path (str): Path to the query template used.
    """
    write_header = False
    if not os.path.exists(output_file):
        write_header = True

    with open(output_file, mode='a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        
        # Define headers for the CSV file
        headers = list(prediction.keys()) + ['Model Used', 'Query Template', 'Date']
        
        # Check if the file is empty and write headers if it is
        if write_header:
            writer.writerow(headers)
        
        # Prepare data for writing
        raw_json = json.dumps(prediction, ensure_ascii=False).replace('"', "'")
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [prediction.get(header, 'N/A') for header in headers[:-3]] + [model_used, template_path, current_date]
        
        # Write the prediction row to the CSV file
        writer.writerow(row)

def query_openrouter_api(messages, model, temperature):
    """
    Queries the OpenRouter API with the given messages and model.
    
    Args:
        messages (list): List of messages to send to the API.
        model (str): Model to use for the API call.
        temperature (float): Temperature to use for the API call.
    
    Returns:
        str: The content of the API response.
    """
    #print("Using OpenRouter API")
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "microbe.cards", 
                "X-Title": "microbe.cards",
            },
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=2048,
            top_p=0
        )
        result = completion.choices[0].message.content
        #print("API call successful, result obtained.")
        #print(result)
        return result
    except Exception as e:
        #print(f"Error during API call: {e}")
        return None

def summarize_predictions(predictions):
    """
    Summarizes predictions by calculating the majority vote and identifying disagreements.
    
    Args:
        predictions (list): List of prediction dictionaries.
    
    Returns:
        tuple: Summary of predictions and disagreements.
    """
    from collections import Counter
    summary = {}
    disagreements = {}

    # Initialize dictionaries to store counts of each category
    for key in predictions[0].keys():
        if key not in ['Model Used', 'Query Template', 'Date', 'Type']:
            summary[key] = []
            disagreements[key] = Counter()

    # Collect all predictions for each category
    for prediction in predictions:
        for key, value in prediction.items():
            if key in summary:
                # Convert lists to tuples for hashability
                if isinstance(value, list):
                    value = tuple(value)
                summary[key].append(value)

    # Calculate majority vote and identify disagreements
    results = {}
    for key, values in summary.items():
        count = Counter(values)
        most_common, num_most_common = count.most_common(1)[0]
        results[key] = most_common
        # Check if there's a disagreement
        if num_most_common < len(values):
            disagreements[key] = count

    # Ensure 'Binomial name' is included in results if it's a key in the predictions
    if 'Binomial name' in predictions[0]:
        results['Binomial name'] = predictions[0]['Binomial name']

    return results, disagreements


def pretty_print_prediction(prediction):
    """
    Pretty prints a prediction dictionary to the console.
    
    Args:
        prediction (dict): The prediction dictionary to print.
    """
    print("\nPrediction Results:")
    print("=" * 40)
    for key, value in prediction.items():
        if key not in ['Model Used', 'Query Template', 'Date']:
            if isinstance(value, (list, dict)):
                print(f"{key}:")
                print(json.dumps(value, indent=2))
            else:
                print(f"{key}: {value}")
    print("=" * 40)