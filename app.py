import numpy as np
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
import pickle
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from model import process_csv


ALLOWED_EXTENSIONS = set(['csv'])
# Makes sure the file uploaded is a csv file
def allowed_filenames(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/', methods = ['GET'])
def homepage():
    return render_template('upload.html')

@app.route('/upload', methods = ["POST"])
def upload():
    file = request.files['file']
    month = request.form['months']
    month = int(month)
    if file and allowed_filenames(file.filename):
        filename = secure_filename(file.filename)
        #new_filename = f"{filename.split('.')[0]}_{str(datetime.now())}.csv"
        new_filename = "online_retail_input.csv"
        save_location = f"input\{new_filename}"#os.path.join('input', new_filename)
        file.save(save_location)
        
        output_file = process_csv(save_location, month)

        return redirect(url_for('download'))
    else:
        #shows error page when csv file is not uploaded
        return redirect(url_for('error'))

@app.route('/download')
def download():
    return render_template('download.html', files=os.listdir('output'), plt_url = 'static/myplot.png')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('output', filename)

@app.route('/error')
def error():
    return render_template('error.html')

if __name__ == '__main__':
    app.run()