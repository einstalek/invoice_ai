import json
import os
import tempfile
import shutil
from flask import Flask, request, jsonify, render_template_string
from html_template import HTML_TEMPLATE

# from main import pipeline
from utils import pipeline

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        file.save(temp_path)
        
        # Call pipeline
        raw_result = pipeline(temp_path)

        if isinstance(raw_result, str):
            result_dict = json.loads(raw_result)
        else:
            result_dict = raw_result

        final_response = {}
        for k, v in result_dict.items():
            if type(v) is str and not v.strip():
                continue
            if type(v) is list and not v:
                continue
            if isinstance(v, dict) and 'value' in v:
                final_response[k] = v
            else:
                final_response[k] = { "value": v, "bbox": None }

        print(final_response)

        return jsonify(final_response)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    app.run(debug=False, port=5000, host='0.0.0.0')
