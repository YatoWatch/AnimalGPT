# Use an official PyTorch runtime with Python 3 as a base image
FROM nvcr.io/nvidia/pytorch:23.07-py3

# Set the working directory to /app in the container
WORKDIR /app

# Clone the AnimalGPT repository from GitHub into /app in the container
RUN git clone https://github.com/YatoWatch/AnimalGPT.git

RUN apt-get install -y zip

# Change the working directory to /app/AnimalGPT in the container
WORKDIR /app/AnimalGPT/

# Install the required packages using pip
RUN pip install flask werkzeug pillow timm torch flask-cors
# Install dependencies listed in the requirements.txt file
RUN pip install -r requirements.txt
# Install the llama-cpp-python package using pip, force reinstall if needed, and do not use cache
RUN pip install llama-cpp-python==0.1.65 --force-reinstall --upgrade --no-cache-dir
# Install the git-lfs package for handling large files in Git repositories
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash

# Create the directories for storing animal pictures and models in the container
RUN mkdir ./static/animal 
RUN mkdir ./models

# Download the pre-trained Llama model binary file and move it to the models directory
RUN wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/resolve/main/llama-2-7b-chat.ggmlv3.q4_0.bin
RUN mv llama-2-7b-chat.ggmlv3.q4_0.bin ./models

# Change the working directory to /app/AnimalGPT in the container
RUN cd /app/AnimalGPT

# Expose port 5000 to the host machine
EXPOSE 5000

# Set the FLASK_APP environment variable to app.py
ENV FLASK_APP=app.py

# Set the FLASK_RUN_HOST environment variable to 0.0.0.0 to allow connections from any host
ENV FLASK_RUN_HOST=0.0.0.0


