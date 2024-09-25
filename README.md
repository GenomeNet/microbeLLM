# MicrobeLLM

[![DOI](https://zenodo.org/badge/851077612.svg)](https://zenodo.org/doi/10.5281/zenodo.13839818)

MicrobeLLM is a versatile Python tool designed to leverage publicly available, general-purpose Large Language Models (LLMs) for predicting microbial phenotypes. This tool allows researchers to query diverse LLM providers, including OpenAI and those accessible through OpenRouter, without requiring any specific training on microbiological data.

MicrobeLLM queries publicly available, general-purpose LLMs that have not been specifically trained on microbiological datasets. The tool's effectiveness stems from these models' broad knowledge base acquired through training on diverse text corpora. Users should be aware of potential limitations and validate results against experimental data when necessary.
This tool is designed for research purposes and to explore the capabilities of LLMs in microbiology. It does not replace traditional experimental methods or specialized bioinformatics tools but offers a complementary approach to microbial phenotype prediction.

## Key Features

- *Flexible Query System*: Utilizes customizable templates for system and user messages, enabling adaptable query formulation across multiple LLM platforms.
- *Gene List Integration*: Capable of incorporating gene lists into queries, allowing for predictions based on both taxonomic and genomic information.
- *Multi-threading Support*: Implements parallel processing to optimize performance when dealing with extensive datasets.
- *Robust Error Handling*: Includes automatic retry mechanisms (up to 4 attempts) to manage API failures or malformed responses, ensuring reliable operation.
- *Standardized Output*: Processes and validates LLM responses, extracting predictions in a structured JSON format and saving results in CSV format with relevant metadata.
- *Support for Multiple LLM Providers*: Compatible with OpenAI's API and OpenRouter, providing access to a wide range of state-of-the-art language models.
- *Support for OpenAI Batch output format*: Can generate JSONL files that can be uploaded to OpenAI for batch processing to save 50% API costs.

## Installation

To install MicrobeLLM, follow these steps:

```
git clone https://github.com/yourusername/microbeLLM.git
cd microbeLLM
pip install -e .
```

This will clone the repository and install MicrobeLLM in editable mode, allowing you to easily update the code as needed.

### Environment Variables

MicrobeLLM requires API keys to access various LLM providers. Set up the following environment variables for API access. You can add these to your `~/.bashrc` or `~/.zshrc` file for permanent configuration:

```
export OPENROUTER_API_KEY='your_api_key_here' # If using OpenRouter
export OPENAI_API_KEY='your_openai_api_key_here'  # If using only OpenAI models through OpenAI API
```

Make sure to replace 'your_api_key_here' with your actual API keys.


## MicrobeLLM Web Interface

### Getting Started

MicrobeLLM now includes a web interface for single-species predictions. 

To start the development server, run:

```
microbellm web  
```

This will typically start a server running at `http://127.0.0.1:5000/`.


### API Endpoints 

#### POST Request
Once the server is running you can run predictions using the web interface or via curl

```
curl -X POST -H "Content-Type: application/json" -d '{"binomial_name":"Escherichia coli"}' http://127.0.0.1:5000/
```

#### GET Request

For easier testing in a browser:

```
curl "http://127.0.0.1:5000/predict?binomial_name=Escherichia%20coli"
```

And the corresponding URL for the browser would be:

http://127.0.0.1:5000/predict?binomial_name=Escherichia%20coli

#### Response Format

The API returns a JSON object with predictions for various bacterial properties. For example:

```
{
"Binomial name": "Escherichia coli",
"aerophilicity": "['facultatively anaerobic']",
"animal_pathogenicity": "TRUE",
"biofilm_formation": "TRUE",
"biosafety_level": "biosafety level 2",
"cell_shape": "bacillus",
"extreme_environment_tolerance": "FALSE",
"gram_staining": "gram stain negative",
"health_association": "TRUE",
"hemolysis": "non-hemolytic",
"host_association": "TRUE",
"motility": "TRUE",
"plant_pathogenicity": "FALSE",
"spore_formation": "FALSE"
}
```

## Usage of the command line tool

MicrobeLLM offers two main modes of operation: *predicting phenotypes* and assessing *knowledge groups* for species.

### Prediction of phenotypes

MicrobeLLM can predict various microbial phenotypes based on species names or gene content. Here are some example usage scenarios:


To predict phenotypes for multiple species at once:

#### 'Batch' Prediction from a List

```
microbeLLM by_list \
    --model meta-llama/llama-3-8b-instruct \
    --system_template templates/system/template1.txt \
    --user_template templates/user/template1.txt \
    --input_file data/binomial_names.csv \
    --output example_output/predictions.csv
```

This command processes a list of binomial names from data/binomial_names.csv and saves the predictions to example_output/predictions.csv.

#### Using Multiple Models and Templates

MicrobeLLM supports using multiple models and templates in a single run:

```
microbeLLM by_list \
    --model meta-llama/llama-3-8b-instruct openai/chatgpt-4o-latest \
    --system_template templates/system/template1.txt templates/system/template2.txt \
    --user_template templates/user/template1.txt templates/user/template2.txt \
    --input_file data/binomial_names.csv \
    --output example_output/predictions_mult_templates.csv
```

This approach allows for comparing predictions across different models and query formulations.

#### OpenAI-Batch output

OpenAI limits that batches are only contain one model per JSONL file, so please not use more than one model. Also the `--model` paramter shpould be a model from OpenAI, see https://platform.openai.com/docs/models/gpt-4-turbo-and-gpt-4

```
microbeLLM by_list \
    --model gpt-4o-mini \
    --system_template templates/system/template1.txt \
    --user_template templates/user/template1.txt \
    --input_file data/binomial_names.csv \
    --output example_output/example_batches.jsonl  \
    --batchoutput
```

This batch can be uploaded via https://platform.openai.com/batches/ 

#### Single Species Prediction

For predicting phenotypes of a single species:

```
microbeLLM by_name \
    --binomial_name "Escherichia coli" \
    --model "openai/chatgpt-4o-latest" \
    --system_template templates/system/template1.txt \
    --user_template templates/user/template1.txt \
    --output example_output/single_predictions.csv
```

This command will output predictions for Escherichia coli using two different models. The output will look similar to:

```
Prediction Results:
========================================
Binomial name: Escherichia coli
num_genes: 0
gram_staining: gram stain negative
motility: TRUE
aerophilicity:
[
  "facultatively anaerobic"
]
extreme_environment_tolerance: FALSE
biofilm_formation: TRUE
animal_pathogenicity: TRUE
biosafety_level: biosafety level 2
health_association: TRUE
host_association: TRUE
plant_pathogenicity: FALSE
spore_formation: FALSE
hemolysis: non-hemolytic
cell_shape: bacillus
========================================
```

### Prediction of Knowledge Groups

MicrobeLLM can also assess the LLM's self-rated knowledge level about specific bacterial species. This feature helps in understanding the confidence level of the predictions. The usage is similar to phenotype prediction, but you'll need to use specific templates designed for knowledge group assessment.

### Additional Notes

- Ensure that your input files are properly formatted with one binomial name per line. And the column containing the binomial name is names "Binomial.name" or specified using `--column_name column_header`
- System and user templates in the templates/ directory can be customized to refine the queries sent to the LLMs.
