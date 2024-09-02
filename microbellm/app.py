from flask import Flask, render_template, request, jsonify, Response
from microbellm.predict import predict_binomial_name
from microbellm.utils import read_template_from_file
import os
import logging
import tempfile
import time

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        app.logger.info("Received POST request")
        try:
            data = request.get_json() if request.is_json else request.form
            binomial_name = data.get('binomial_name')
            prediction = process_prediction(binomial_name)
            if isinstance(prediction, Response):
                return prediction
            return jsonify(prediction)
        except Exception as e:
            app.logger.error(f"An error occurred: {str(e)}", exc_info=True)
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
    return render_template('index.html')

@app.route('/predict', methods=['GET'])
def predict():
    binomial_name = request.args.get('binomial_name')
    if not binomial_name:
        return jsonify({"error": "Missing 'binomial_name' parameter"}), 400
    return process_prediction(binomial_name)

def process_prediction(binomial_name):
    app.logger.info(f"Processing prediction for: {binomial_name}")
    try:
        model = "openai/chatgpt-4o-latest"
        model_host = 'openrouter'
        system_template_path = 'templates/system/template1.txt'
        user_template_path = 'templates/user/template1.txt'
        
        app.logger.info(f"Model: {model}, Host: {model_host}")
        app.logger.info(f"System template: {system_template_path}")
        app.logger.info(f"User template: {user_template_path}")

        system_template = read_template_from_file(system_template_path)
        user_template = read_template_from_file(user_template_path)
        
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as temp_file:
            temp_output_path = temp_file.name
        
        app.logger.info(f"Temporary file created: {temp_output_path}")
        
        predict_binomial_name(
            binomial_name, 
            model, 
            system_template, 
            user_template, 
            temp_output_path,
            system_template_path,
            0,  # temperature
            None,  # gene_list
            model_host,
            None,  # pbar
            4,  # max_retries
            False  # by_name_mode (set to False to write to file)
        )
        
        # Wait for a short time to ensure the file is fully written
        time.sleep(2)
        
        # Check if the file exists and is not empty
        if os.path.exists(temp_output_path) and os.path.getsize(temp_output_path) > 0:
            app.logger.info(f"Temporary file exists and is not empty")
            # Read the prediction from the temporary file
            with open(temp_output_path, 'r') as file:
                content = file.read().strip()
                app.logger.info(f"File content: {content}")
                
            # Parse the content
            parts = content.split(';')
            if len(parts) >= 15:
                prediction = {
                    "Binomial name": parts[0],
                    "gram_staining": parts[2],
                    "motility": parts[3],
                    "aerophilicity": parts[4],
                    "extreme_environment_tolerance": parts[5],
                    "biofilm_formation": parts[6],
                    "animal_pathogenicity": parts[7],
                    "biosafety_level": parts[8],
                    "health_association": parts[9],
                    "host_association": parts[10],
                    "plant_pathogenicity": parts[11],
                    "spore_formation": parts[12],
                    "hemolysis": parts[13],
                    "cell_shape": parts[14]
                }
                app.logger.info(f"Parsed prediction: {prediction}")
            else:
                app.logger.error("File content is not in the expected format")
                return jsonify({"error": "Prediction file is not in the expected format"}), 400
        else:
            app.logger.error(f"Temporary file is empty or does not exist: {temp_output_path}")
            return jsonify({"error": "Failed to generate prediction"}), 400
        
        # Clean up the temporary file
        os.unlink(temp_output_path)
        app.logger.info("Temporary file deleted")
        
        if prediction:
            app.logger.info("Prediction successful")
            return prediction  # Return the prediction dictionary directly
        else:
            app.logger.error("Prediction failed")
            return {"error": "Failed to generate prediction"}, 400
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return {"error": f"An error occurred: {str(e)}"}, 500

if __name__ == '__main__':
    app.run(debug=True)