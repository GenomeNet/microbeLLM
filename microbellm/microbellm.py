#!/usr/bin/env python

# Import necessary libraries
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import pandas as pd
from tqdm import tqdm
from microbellm.utils import read_template_from_file, write_batch_jsonl
from microbellm.predict import predict_binomial_name

def read_genes_from_file(file_path):
    """
    Reads gene names from a file and returns them as a list.
    
    Args:
        file_path (str): Path to the file containing gene names.
    
    Returns:
        list: List of gene names.
    """
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def check_environment_variables(model_host):
    required_vars = ['OPENROUTER_API_KEY'] if model_host == 'openrouter' else ['OPENAI_API_KEY', 'OPENAI_ORG_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("Error: The following required environment variables are not set:")
        for var in missing_vars:
            print(f"- {var}")
        print("Please set these variables before running the script.")
        return False
    return True

def main():
    """
    Main function to parse arguments and execute the prediction command.
    """
    
    parser = argparse.ArgumentParser(description="microbeLLM - Applying LLMs on microbe data")
    subparsers = parser.add_subparsers(dest="command")

    # Subparser for the predict command
    predict_parser = subparsers.add_parser("by_list", help="Performs prediction based on a input list containing binomial names (such as 'Escherichia coli')")
    predict_parser.add_argument("--model", type=str, nargs='+', default=["openai/chatgpt-4o-latest"], help="List of models to use for prediction")
    predict_parser.add_argument("--model_host", type=str, choices=['openrouter', 'openai'], default='openrouter', help="Select the model host (default: openrouter)")
    predict_parser.add_argument("--system_template", type=str, nargs='+', required=True, help='Text files for system message templates')
    predict_parser.add_argument("--user_template", type=str, nargs='+', required=True, help='Text files for user message templates')
    predict_parser.add_argument("--input_file", type=str, required=True, help="Path to the input CSV file. Each row represents an instance for prediction, containing the binomial name and other relevant information.")
    predict_parser.add_argument("--output", type=str, required=True, help="Output file path to save predictions")
    predict_parser.add_argument("--column_name", type=str, default='Binomial.name', help="Name of the column in the input file containing binomial names")
    predict_parser.add_argument("--threads", type=int, default=1, help='Number of parallel threads to use')
    predict_parser.add_argument("--temperature", type=float, default=0, help='Temperature for the prediction model')
    predict_parser.add_argument("--use_genes", action='store_true', default=False, help='Specify if gene names should be considered')
    predict_parser.add_argument("--gene_column", type=str, default='Gene_file', help='Column name for gene file paths')
    predict_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    predict_parser.add_argument("--batchoutput", action="store_true", help="Generate batch output file for OpenAI processing")


    # Subparser for the by_name command
    by_name_parser = subparsers.add_parser("by_name", help="Performs prediction based on a single binomial name")
    by_name_parser.add_argument("--model", type=str, nargs='+', default=["openai/chatgpt-4o-latest"], help="List of models to use for prediction")
    by_name_parser.add_argument("--model_host", type=str, choices=['openrouter', 'openai'], default='openrouter', help="Select the model host (default: openrouter)")
    by_name_parser.add_argument("--system_template", type=str, required=True, help='Text file for system message template')
    by_name_parser.add_argument("--user_template", type=str, required=True, help='Text file for user message template')
    by_name_parser.add_argument("--output", type=str, required=True, help="Output file path to save predictions")
    by_name_parser.add_argument("--binomial_name", type=str, required=True, help="Binomial name for prediction (e.g., 'Escherichia coli')")
    by_name_parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    # Subparser for the web interface command
    web_parser = subparsers.add_parser("web", help="Starts the web interface for MicrobeLLM")
    web_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to run the web interface on")
    web_parser.add_argument("--port", type=int, default=5000, help="Port to run the web interface on")

    args = parser.parse_args()

    #if not check_environment_variables(args.model_host):
    #    return

    if args.command == "by_list":
        # Validate template files
        template_files = args.system_template + args.user_template
        missing_files = [file for file in template_files if not os.path.exists(file)]
        if missing_files:
            print("Error: The following template files are missing:")
            for file in missing_files:
                print(f"- {file}")
            print("Please ensure all specified template files exist before running the script.")
            return

        # Check if the output file already exists
        if os.path.exists(args.output):
            print(f"Warning: The output file '{args.output}' already exists.")
            print("New predictions will be added to this file without overwriting existing content.")
            input("Press Enter to continue or Ctrl+C to abort...")

        # Read binomial names from the provided input file
        data = pd.read_csv(args.input_file, delimiter=';')
        binomial_names = data[args.column_name].dropna().unique()

        # Calculate total number of tasks
        total_tasks = len(binomial_names) * len(args.model) * len(args.system_template)

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = []
            
            # Create progress bar
            with tqdm(total=total_tasks, desc="Processing ") as pbar:
                for name in binomial_names:
                    gene_list = []
                    if args.use_genes and args.gene_column in data.columns:
                        gene_file_path = data.loc[data[args.column_name] == name, args.gene_column].values[0]
                        gene_list = read_genes_from_file(gene_file_path)

                    for model in args.model:
                        for system_template, user_template in zip(args.system_template, args.user_template):
                            if args.use_genes:
                                # Modify template names to include genes
                                system_template = system_template.replace('.txt', '_with_genes.txt')
                                user_template = user_template.replace('.txt', '_with_genes.txt')

                            system_message = read_template_from_file(system_template)
                            user_message = read_template_from_file(user_template)
                            
                            # Submit prediction task to the executor
                            future = executor.submit(predict_binomial_name, name, model, system_message, user_message, args.output, system_template, args.temperature, gene_list if args.use_genes else None, args.model_host, pbar, verbose=args.verbose, batch_output=args.batchoutput)
                            futures.append(future)
                
                # Wait for all futures to complete
                for future in as_completed(futures):
                    future.result()  # This will raise any exceptions that occurred during execution

        if args.batchoutput:
            print(f"Batch output file '{args.output}' has been generated for OpenAI processing.")

    elif args.command == "by_name":
        # Validate template files
        template_files = [args.system_template, args.user_template]
        missing_files = [file for file in template_files if not os.path.exists(file)]
        if missing_files:
            print("Error: The following template files are missing:")
            for file in missing_files:
                print(f"- {file}")
            print("Please ensure all specified template files exist before running the script.")
            return

        # Check if the output file already exists
        if os.path.exists(args.output):
            print(f"Warning: The output file '{args.output}' already exists.")
            print("New predictions will be added to this file without overwriting existing content.")
            input("Press Enter to continue or Ctrl+C to abort...")

        system_message = read_template_from_file(args.system_template)
        user_message = read_template_from_file(args.user_template)

        for model in args.model:
            predict_binomial_name(args.binomial_name, model, system_message, user_message, args.output, args.system_template, 0, None, args.model_host, by_name_mode=True, verbose=args.verbose)

    elif args.command == "web":
        from microbellm.app import app
        app.run(host=args.host, port=args.port)

if __name__ == "__main__":
    print("Welcome to microbeLLM!")
    main()