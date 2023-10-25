from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import zipfile
import os
import shutil

app = Flask(__name__)
folder_animal="static/animal/"

# Function to check if a file is a picture (PNG, JPG, or JPEG)
def is_picture(filename):
    with open(filename, 'rb') as f:
        header = f.read(10)
        
        # Check if it's a PNG
        if header[:8] == b'\x89PNG\r\n\x1a\n'or header[:2] == b'\xff\xd8' or header[6:10] in (b'JFIF', b'Exif'):
            return True
        else:
            return False

# Function to unzip a file and extract its contents
def unzip(filename, destination_directory):
    global folder_animal
    zip_file = destination_directory + filename
    is_zip = zipfile.is_zipfile(zip_file)
    if is_zip:
        folder_animal=zip_file + str(1)
        with zipfile.ZipFile(zip_file, 'r') as archive_zip:
            archive_zip.extractall(folder_animal)
        return True
    else:
        return False

# Function to get a list of pictures in a directory
def tab_picture(directory):
    tab=[]
    # Traverse the files in the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            
            if(is_picture(full_path)):
                tab.append(full_path)

    return(tab)

# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']

    filename = secure_filename(file.filename)

    file.save(folder_animal + filename)
    directory_zip = folder_animal
    unzip(filename, directory_zip)

    return redirect(url_for('index'))

# Route to handle animal data prediction
@app.route('/predict', methods=['POST'])
def get_animal_data():
    data = request.get_json()
    tab=tab_picture(folder_animal)
    return tab

if __name__ == '__main__':
    shutil.rmtree(folder_animal)
    os.mkdir(folder_animal)
    app.run(port=3000, debug=True)
