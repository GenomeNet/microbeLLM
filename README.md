# MicrobeLLM

MicrobeLLM is a tool for generating LLM predictions for microbial phenotypes.

## Installation

```
git clone https://github.com/yourusername/microbeLLM.git
cd microbeLLM
pip install .
```

### Environment Variables

Ensure the following environment variables are set for API access:

```
export OPENROUTER_API_KEY='your_api_key_here'
```

## Usage

```
microbeLLM by_list \
    --model openai/chatgpt-4o-latest \
    --system_template templates/system/template1.txt \
    --user_template templates/user/template1.txt \
    --input_file data/binomial_names.csv \
    --output example_output/predictions.csv
```
