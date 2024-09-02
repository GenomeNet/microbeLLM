# predict.py

# Import necessary libraries
import argparse
import json
import pandas as pd
from colorama import Fore, Style
from microbellm.utils import query_openrouter_api, extract_and_validate_json, write_prediction, query_openai_api
import sys
from tqdm import tqdm

def predict_binomial_name(binomial_name, model, system_message_template, user_message_template, output_file, system_template_path, temperature, gene_list=None, pbar=None, max_retries=4):
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
        pbar (tqdm, optional): Progress bar object for updating progress.

    Returns:
        list: The prediction result.
    """
    name_parts = binomial_name.split()
    if len(name_parts) != 2:
        # Ensure the binomial name consists of exactly two words (genus and species)
        return None

    original_gene_list = gene_list  # Save the original gene list

    # Update the progress bar with the current binomial name on the right
    if pbar:
        pbar.set_postfix_str(f"Processing: {binomial_name}")

    system_message = system_message_template
    user_message = user_message_template.replace('{binomial_name}', binomial_name)

    if original_gene_list:
        gene_list_str = ', '.join(gene_list)
        user_message = user_message.replace('{gene_list}', gene_list_str)

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

    retry_count = 0
    while retry_count < max_retries:
        # Query the appropriate API based on the model
        response_json = query_openrouter_api(messages, model)

        valid_json = extract_and_validate_json(response_json)

        if valid_json is not None:
            # Calculate the number of genes
            num_genes = len(gene_list) if gene_list else 0
    
            prediction = {'Binomial name': binomial_name, 'num_genes': num_genes, **valid_json}
            write_prediction(output_file, prediction, model, system_template_path)
            
            # Update the progress bar
            if pbar:
                pbar.update(1)
            
            return [prediction]
        else:
            print(Fore.YELLOW + f"\nFailed to extract valid JSON for {binomial_name}. Retrying... (Attempt {retry_count + 1}/{max_retries})" + Style.RESET_ALL)
            retry_count += 1

    print(Fore.RED + f"\nFailed to extract valid JSON for {binomial_name} after {max_retries} attempts." + Style.RESET_ALL)
    
    # Update the progress bar even if we failed
    if pbar:
        pbar.update(1)
    
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
            predict_binomial_name(name, None, None, None, args.output, None, None, gene_list)

if __name__ == "__main__":
    main()