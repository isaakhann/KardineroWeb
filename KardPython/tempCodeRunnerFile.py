import csv
from io import BytesIO, StringIO
from flask import Flask, jsonify, request, render_template, redirect, send_file, url_for
from ecg_Plotter import EcgPlotter
from scpParser import SCPParser
import numpy as np
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ecg_data_global = None  # Global variable to store ECG data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global ecg_data_global
    parser = SCPParser()

    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Use SCPParser to read the file and extract ECG data
        ecg_data_global = parser.extract_info_from_scp(filepath)

        if ecg_data_global is None:
            return "Error extracting ECG data from the file. Please check the file format."

        return redirect(url_for('select_lead'))
    else:
        return "Invalid file type. Please upload a .scp file."

@app.route('/select-lead', methods=['GET', 'POST'])
def select_lead():
    global ecg_data_global

    if ecg_data_global is None:
        return "No ECG data available. Please upload a file first."

    plotter = EcgPlotter(ecg_data_global)
    lead_names = plotter.lead_names

    if request.method == 'POST':
        selected_lead = request.form.get('lead')
        plot_html = plotter.generate_plot(selected_lead)
        return render_template('show_graph.html', plot_html=plot_html, lead_names=lead_names, selected_lead=selected_lead)

    return render_template('select_lead.html', lead_names=lead_names)
@app.route('/get_patient_info', methods=['GET'])
def get_patient_info():
    parser = SCPParser()
    patient_data = parser.read_scp_file('/Users/isakhan/Documents/KardPython/uploads/rest.scp')  # Replace with the actual file path
    if patient_data:
        return jsonify({'name': patient_data.get('name'), 'id': patient_data.get('id')})
    return jsonify({'error': 'No patient info found'}), 404
@app.route('/download_csv', methods=['GET'])
def download_csv():
    csv_string = parse_scp_file('uploads/rest.scp')  # Replace with actual file path
    
    if csv_string is None:
        return jsonify({'error': 'Failed to generate CSV'}), 500
    
    # Convert the CSV string to bytes and use BytesIO
    csv_bytes = csv_string.encode('utf-8')
    csv_buffer = BytesIO(csv_bytes)

    # Return CSV as a downloadable file
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='ecg_data.csv'
    )

def parse_scp_file(file_path):
    try:
        # Step 1: Initialize the SCPParser and extract patient information
        scp_parser = SCPParser()  # Assuming SCPParser is defined to handle SCP file parsing
        patient_info = scp_parser.extract_info_from_scp(file_path)
        
        # Step 2: Extract the first name from the patient info
        first_name = extract_first_name(patient_info)
        
        # Step 3: Read the file data
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Step 4: Extract ECG data
        ecg_data = scp_parser.extract_ecg_data(file_data)
        
        # Step 5: Calculate derived leads
        full_ecg_data = calculate_derived_leads(ecg_data)
        
        # Step 6: Convert to CSV format
        csv_string = convert_to_csv(patient_info, full_ecg_data)
        
        # Optional: Save CSV to a file (if required)
        csv_filename = f"{first_name}.csv"
        with open(csv_filename, 'w') as f:
            f.write(csv_string)
        
        return csv_string
    
    except Exception as e:
        print(f"Error parsing SCP file or writing CSV: {e}")
        return None

def extract_first_name(patient_info):
    lines = patient_info.split('\n')
    name_line = next((line for line in lines if line.startswith("Name:")), None)
    if name_line:
        name_components = name_line.split()
        if len(name_components) > 1:
            return name_components[1]  # Assuming the first name is the second word
    return "Patient"

def calculate_derived_leads(ecg_data):
    lead_i = ecg_data[0]
    lead_ii = ecg_data[1]

    # Calculate Lead III = Lead II - Lead I
    lead_iii = np.subtract(lead_ii, lead_i)

    # Calculate aVR = -(Lead I + Lead II) / 2
    avr = -np.divide(np.add(lead_i, lead_ii), 2)

    # Calculate aVL = (Lead I - Lead III) / 2
    avl = np.divide(np.subtract(lead_i, lead_iii), 2)

    # Calculate aVF = (Lead II + Lead III) / 2
    avf = np.divide(np.add(lead_ii, lead_iii), 2)

    # Append derived leads to the full ECG data
    full_ecg_data = np.vstack([ecg_data, lead_iii, avr, avl, avf])

    return full_ecg_data

def convert_to_csv(patient_info, ecg_data):
    csv_string = patient_info + "\n"
    csv_string += "CH1,CH2,CH3,CH4,CH5,CH6,CH7,CH8,CH9,CH10,CH11,CH12\n"

    max_length = max(len(lead) for lead in ecg_data)

    for i in range(max_length):
        row = [str(lead[i]) if i < len(lead) else "" for lead in ecg_data]
        csv_string += ",".join(row) + "\n"

    return csv_string
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
