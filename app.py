import os
import pandas as pd
import numpy as np
from flask import Flask, request, render_template, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup as bs
import requests
import zipfile

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define the route for the main page
@app.route('/')
def upload_file():
    return render_template('index.html')

# Define the route to handle file uploads
@app.route('/uploader', methods=['POST'])
def uploader_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Run your taxonomy scraping function
        tax_result_file, retry_file = process_file(filepath)
        
        # Create a ZIP file containing both the result CSV and the retry text file
        zip_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'taxonomy_results.zip')
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            zipf.write(tax_result_file, os.path.basename(tax_result_file))
            zipf.write(retry_file, os.path.basename(retry_file))
        
        # Send the ZIP file to the user
        return send_file(zip_filename, as_attachment=True, download_name='taxonomy_results.zip')

    return 'Invalid file format. Please upload a .txt or .csv file.'

# Function to process the uploaded file and scrape taxonomy information
def process_file(filepath):
    # Read the uploaded file as species list
    missingTaxFile = pd.read_csv(filepath, header=None)
    speciesNames = missingTaxFile.iloc[:, [0]].values.tolist()
    speciesNames = np.array(speciesNames).ravel()

    specieslist = []
    filesToRetry = []
    taxidlist = []

    missingTaxDb_cols = ['superkingdom', 'kingdom', 'subkingdom', 'superphylum', 'phylum', 'subphylum',
                         'superclass', 'class', 'subclass', 'superorder', 'order', 'suborder', 'superfamily',
                         'family', 'subfamily', 'tribe', 'subtribe', 'genus', 'subgenus', 'species', 'subspecies', 'taxid']

    missingTaxDb = pd.DataFrame(columns=missingTaxDb_cols)

    for i in speciesNames:
        i = " ".join(i.strip().split(' '))
        specieslist.append(i)
        URL = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=taxonomy&term={i}[SCIN]"
        response = requests.get(URL)
        soup = bs(response.content, 'xml')
        taxId = soup.find_all('Id')
        if taxId:
            for tax in taxId:
                taxidlist.append(tax.get_text())
        else:
            filesToRetry.append(i)

    for i in taxidlist:
        URL = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&id={i}&mode=text&report=xml"
        response = requests.get(URL)
        soup = bs(response.content, 'xml')
        sci_names = soup.find_all('ScientificName')
        ranks = soup.find_all('Rank')

        tempList22 = {col: 'n' for col in missingTaxDb_cols}
        for rank, name in zip(ranks, sci_names):
            if rank.get_text() != "no rank":
                tempList22[rank.get_text()] = name.get_text()

        tempList22['taxid'] = i
        
        # Convert tempList22 (which is a dict) to a DataFrame with one row
        tempList22_df = pd.DataFrame([tempList22])
        
        missingTaxDb = pd.concat([missingTaxDb, tempList22_df], ignore_index=True)

    # Save the result as a CSV file
    result_file = os.path.join(app.config['UPLOAD_FOLDER'], 'missingTaxonomyInfo.csv')
    missingTaxDb.to_csv(result_file, index=False)
    
    # Save the filesToRetry as a text file
    retry_file = os.path.join(app.config['UPLOAD_FOLDER'], 'speciesToRetry.txt')
    with open(retry_file, 'w') as f:
        for species in filesToRetry:
            f.write(species + '\n')

    return result_file, retry_file

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
