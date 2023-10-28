from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import zipfile
import os
import shutil
from flask_cors import CORS
from urllib.request import urlopen
from PIL import Image
import timm
import torch
import subprocess

import json
import privateGPT

# Initialize variables
folder_animal="static/animal/"
zip_name=""

# pre-trained model
model = timm.create_model('mobilenetv3_large_100.ra_in1k', pretrained=True)
model = model.eval()
data_config = timm.data.resolve_model_data_config(model)
transforms = timm.data.create_transform(**data_config, is_training=False)

# Function to check if a file is a picture (PNG, JPG, or JPEG)
def is_picture(filename):
    # Open the file in binary read mode
    with open(filename, 'rb') as f:
        header = f.read(10)
        
        # Check if it's a PNG, JPG or JPEG by comparing file headers
        if header[:8] == b'\x89PNG\r\n\x1a\n'or header[:2] == b'\xff\xd8' or header[6:10] in (b'JFIF', b'Exif'):
            return True
        else:
            return False

# Function to unzip a file and extract its contents
def unzip(filename, destination_directory):
    global folder_animal
    zip_file = destination_directory + filename
    # Check if the file is a zip file
    is_zip = zipfile.is_zipfile(zip_file)
    if is_zip:
        # If it is, set the extraction folder and extract the contents
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
            
            # If the file is a picture, add it to the list
            if(is_picture(full_path)):
                tab.append(full_path)

    return(tab)

# Function to add path to dictionary for a given ID
def add_to_dictionnary(path, id, dictionnary):
  if not id in dictionnary:
    dictionnary[id] = []
  dictionnary[id].append(path)

# Function to identify animal using the pre-trained model
def identifyAnimal(path, percentage):
  # Load image and apply the model
  img = Image.open(path)
  output = model(transforms(img).unsqueeze(0))  # unsqueeze single image into batch of 1
  # Get top 5 probabilities and class indices
  top5_probabilities, top5_class_indices = torch.topk(output.softmax(dim=1) * 100, k=5)
  # Check if the highest probability is greater than the percentage
  if(top5_probabilities[0][0].item() < percentage):
    return -1
  else:
    return top5_class_indices[0][0].item()

# Function to find IDs for an animal name in the dictionary
def find_id_animal(name, dictionnary):
  animalTab = []
  # Iterate over dictionary keys and values
  for key, value in dictionnary.items():
      if isinstance(value, list):
          # Check if name exists in values
          if any(name in v for v in value):
              animalTab.append(key)
      else:
          if name in value:
              animalTab.append(key)
  return animalTab

# Function to find animals with a given ID in the list of links
def find_animal(animalId,tab_link):
    dictionnary = {}
    perc = 30
    # Iterate through the list of animal IDs and links
    for j in range(len(animalId)):
        for i in tab_link:
            # Identify the animal in the image
            result = identifyAnimal(i, perc)
            if(result == -1):
                pass
            else:
                # If it matches the ID, add to the dictionary
                if(result == int(animalId[j])):
                    add_to_dictionnary(i, result, dictionnary)
    return dictionnary

# Function to copy images to a specified folder
def copy_images_to_folder(image_paths, folder_name):
    # Create folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Copy each image into the folder
    for image_path in image_paths:
        shutil.copy(image_path, os.path.join(folder_name, os.path.basename(image_path)))

# Function to zip a folder
def zip_folder(folder_name, zip_name):
    shutil.make_archive(zip_name, 'zip', folder_name)

def zip_animals_all():
    src_dir = "static/animal/"
    zip_path = "static/animals.zip"

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for foldername, subfolders, filenames in os.walk(src_dir):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                if not filename.endswith('.zip'):
                    zipf.write(file_path, arcname=os.path.relpath(file_path, src_dir))


###########################################################################
# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/newchat', methods=['GET'])
def newchat():
    if os.path.exists(folder_animal):
        shutil.rmtree(folder_animal)
    os.mkdir(folder_animal)
    return render_template('index.html')

# Route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    # Get the uploaded file
    file = request.files['file']

    # Secure the filename
    filename = secure_filename(file.filename)

    # Save the file and unzip it
    file.save(folder_animal + filename)
    directory_zip = folder_animal
    unzip(filename, directory_zip)

    return redirect(url_for('index'))

# Route to handle animal data prediction
@app.route('/predict', methods=['POST'])
def get_animal_data():
    global zip_name
    # Get the data from the request
    data = request.get_json()
    # Get the list of pictures in the folder
    tab=tab_picture(folder_animal)

    # Specify the path to the JSON file
    database = 'database.json'

    # Open the JSON file and load the contents into a dictionary
    with open(database, 'r') as fichier:
        database_dic = json.load(fichier)

    # Find the animal IDs in the dictionary
    animal_id = find_id_animal(data['animal'], database_dic)
    # Find the animals with the given ID in the list of links
    find_animal_res = find_animal(animal_id,tab)

    res=[]
    # Add the image paths to the result list
    for i in find_animal_res:
        for j in find_animal_res[i]:
            res.append(str(j))

    # Set the result folder path and copy images to it
    res_folder = "static/animal/" + data['animal']
    copy_images_to_folder(res,res_folder)
    zip_name= res_folder

    # Call the private GPT model and write the answer to a file
    answer, sources = privateGPT.call_model(data['animal'], hide_source=False)
    print(answer)

    # Open the file in write mode and write the text to the file
    fichier_txt = data['animal'] +'.txt'
    with open(fichier_txt, 'w') as fichier:
        fichier.write(answer)
    
    # Move the file to the result folder
    shutil.move(fichier_txt,res_folder)
    
    # Zip all animals
    zip_animals_all()
    # Zip the result folder
    zip_folder(res_folder,zip_name)
    zip_name+=".zip"
    return res

@app.route('/download', methods=['POST'])
def download_file():
    if zip_name != "":
        return send_file(zip_name, as_attachment=True)
    else:
        return None
    
@app.route('/downloadall', methods=['POST'])
def downloadall_file():
    if os.path.exists("static/animals.zip"):
        return send_file("static/animals.zip", as_attachment=True)
    else:
        return None

if __name__ == '__main__':
    # Ingest data into the private GPT model
    privateGPT.ingest()

    # If the folder for animal pictures exists, remove it and create a new one
    if os.path.exists(folder_animal):
        shutil.rmtree(folder_animal)
    os.mkdir(folder_animal)

    # Set the upload folder for source documents
    app.config['UPLOAD_FOLDER'] = 'source_documents'
    # Run the app on port 5000 and allow connections from any host
    app.run(port=5000, host='0.0.0.0', debug=True)

