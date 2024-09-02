# MicrobeLLM

MicrobeLLM is a tool for generating LLM predictions for microbial phenotypes.

## Installation

```
git clone https://github.com/yourusername/microbeLLM.git
cd microbeLLM
pip install -e .
```

### Environment Variables

Ensure the following environment variables are set for API access:

```
export OPENROUTER_API_KEY='your_api_key_here'
```

## Usage

using a list with one binomial name per line as input file

```
microbeLLM by_list \
    --model openai/chatgpt-4o-latest \
    --system_template templates/system/template1.txt \
    --user_template templates/user/template1.txt \
    --input_file data/binomial_names.csv \
    --output example_output/predictions.csv
```

using a single binomial name directly

```
microbeLLM by_name \
    --binomial_name "Escherichia coli" \
    --model "openai/chatgpt-4o-latest" \
    --system_template templates/system/template1.txt \
    --user_template templates/user/template1.txt \
    --output example_output/single_predictions.csv
```

Which produces

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