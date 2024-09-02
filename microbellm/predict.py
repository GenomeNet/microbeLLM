# predict.py

# Import necessary libraries
import argparse
import json
import pandas as pd
from colorama import Fore, Style
from microbellm.utils import query_openrouter_api, query_openai_api, extract_and_validate_json, write_prediction, pretty_print_prediction
import sys
from tqdm import tqdm

def predict_binomial_name(binomial_name, model, system_message_template, user_message_template, output_file, system_template_path, temperature, gene_list=None, model_host='openrouter', pbar=None, max_retries=4, by_name_mode=False):
    """
    Predicts the phenotype of a microbe given its binomial name using a specified model.

    Args:
        binomial_name (str): The binomial name of the microbe.
        model (str): The model to use for prediction.
        system_message_template (str): The system message template.
        user_message_template (str): The user message template.
        output_file (str): The file to write the prediction to.
        system_template_path (str): The path to the system template.
        temperature (float): The temperature for the prediction model.
        gene_list (list, optional): List of genes to include in the query. Defaults to None.
        model_host (str, optional): The model host to use for the query. Defaults to 'openrouter'.
        pbar (tqdm, optional): Progress bar object for updating progress.
        max_retries (int): Maximum number of retries for API calls.
        by_name_mode (bool): Whether the function is being called in by_name mode.

    Returns:
        list: The prediction result.
    """
    name_parts = binomial_name.split()
    if len(name_parts) != 2:
        print(Fore.RED + "Error: The binomial name must consist of exactly two words (genus and species)." + Style.RESET_ALL)
        return None

    system_message = system_message_template
    user_message = user_message_template.replace('{binomial_name}', binomial_name)

    if gene_list:
        gene_list_str = ', '.join(gene_list)
        user_message = user_message.replace('{gene_list}', gene_list_str)

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    retry_count = 0
    while retry_count < max_retries:
        if model_host == 'openrouter':
            response_json = query_openrouter_api(messages, model, temperature)
        elif model_host == 'openai':
            response_json = query_openai_api(messages, model, temperature)
        else:
            raise ValueError(f"Invalid model_host: {model_host}")

        valid_json = extract_and_validate_json(response_json)

        if valid_json is not None:
            num_genes = len(gene_list) if gene_list else 0
            prediction = {'Binomial name': binomial_name, 'num_genes': num_genes, **valid_json}
            write_prediction(output_file, prediction, model, system_template_path)
            
            if by_name_mode:
                pretty_print_prediction(prediction, model)
            
            return [prediction]
        else:
            print(Fore.YELLOW + f"\nFailed to extract valid JSON for {binomial_name}. Retrying... (Attempt {retry_count + 1}/{max_retries})" + Style.RESET_ALL)
            retry_count += 1

    print(Fore.RED + f"\nFailed to extract valid JSON for {binomial_name} after {max_retries} attempts." + Style.RESET_ALL)
    return None

def main():
    """
    Main function to parse arguments and execute the prediction command.
    """
    parser = argparse.ArgumentParser(description="Microbe LLM Prediction Tool")
    parser.add_argument('--binomial_name', type=str, help='Binomial name or path to file containing binomial names')
    parser.add_argument('--column_name', type=str, default='Taxon_name', help='Column name in the file for binomial names')
    parser.add_argument('--output', type=str, help='Output file path to save the predictions as CSV')
    parser.add_argument('--is_file', action='store_true', help='Indicate if the binomial_name argument points to a file')
    parser.add_argument('--use_genes', action='store_true', help='Indicate if gene list should be included in the query')
    parser.add_argument('--gene_list', type=str, nargs='+', help='List of genes to include in the query')
    parser.add_argument('--model_host', type=str, choices=['openrouter', 'openai'], default='openrouter', help="Select the model host (default: openrouter)")
    args = parser.parse_args()

    if args.is_file:
        # Read binomial names from the provided file
        data = pd.read_csv(args.binomial_name, delimiter=';')
        binomial_names = data[args.column_name].dropna().unique()
        for name in binomial_names:
            if args.use_genes:
                gene_list = args.gene_list
            else:
                gene_list = None
            predict_binomial_name(name, None, None, None, args.output, None, None, gene_list, args.model_host)

if __name__ == "__main__":
    main()