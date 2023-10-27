from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import zipfile
import os
import shutil

from urllib.request import urlopen
from PIL import Image
import timm
import torch


import json

app = Flask(__name__)
folder_animal="static/animal/"
zip_name=""
model = timm.create_model('mobilenetv3_large_100.ra_in1k', pretrained=True)
model = model.eval()
data_config = timm.data.resolve_model_data_config(model)
transforms = timm.data.create_transform(**data_config, is_training=False)

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


def add_to_dictionnary(path, id, dictionnary):
  if not id in dictionnary:
    dictionnary[id] = []
  dictionnary[id].append(path)

def identifyAnimal(path, percentage):
  img = Image.open(path)
  output = model(transforms(img).unsqueeze(0))  # unsqueeze single image into batch of 1
  top5_probabilities, top5_class_indices = torch.topk(output.softmax(dim=1) * 100, k=5)
  if(top5_probabilities[0][0].item() < percentage):
    # print("Error : percentage")
    return -1
  else:
    return top5_class_indices[0][0].item()
  


def find_id_animal(name, dictionnary):
  # Iterate over dictionary keys and values
  animalTab = []
  for key, value in dictionnary.items():
      if isinstance(value, list):
          if any(name in v for v in value):
              animalTab.append(key)
      else:
          if name in value:
              animalTab.append(key)
  return animalTab

def find_animal(animalId,tab_link):
    dictionnary = {}
    perc = 30
    for j in range(len(animalId)):
        for i in tab_link:
            result = identifyAnimal(i, perc)
            if(result == -1):
                pass
            else:
                if(result == int(animalId[j])):
                    add_to_dictionnary(i, result, dictionnary)
    return dictionnary


def copy_images_to_folder(image_paths, folder_name):
    # Créer un dossier s'il n'existe pas
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Copier chaque image dans le dossier
    for image_path in image_paths:
        shutil.copy(image_path, os.path.join(folder_name, os.path.basename(image_path)))

def zip_folder(folder_name, zip_name):
    shutil.make_archive(zip_name, 'zip', folder_name)


###########################################################################""

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
    global zip_name
    data = request.get_json()
    tab=tab_picture(folder_animal)

    # Spécifiez le chemin vers votre fichier JSON
    database = 'data.json'

    # Ouvrez le fichier JSON en mode lecture
    with open(database, 'r') as fichier:
        # Chargez le contenu du fichier JSON dans un dictionnaire
        database_dic = json.load(fichier)

    animal_id = find_id_animal(data['animal'], database_dic)
    find_animal_res = find_animal(animal_id,tab)

    res=[]
    for i in find_animal_res:
        for j in find_animal_res[i]:
            res.append(str(j))

    res_folder = "static/animal/" + data['animal']
    copy_images_to_folder(res,res_folder)
    zip_name= res_folder

    zip_folder(res_folder,zip_name)
    zip_name+=".zip"
    return res

@app.route('/download', methods=['POST'])
def download_file():
    if zip_name != "":
        return send_file(zip_name, as_attachment=True)
    else:
        return None

if __name__ == '__main__':
    shutil.rmtree(folder_animal)
    os.mkdir(folder_animal)
    app.run(port=3000, debug=True)
