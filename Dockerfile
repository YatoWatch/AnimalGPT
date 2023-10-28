# Use an official Python runtime as a parent image
FROM nvcr.io/nvidia/pytorch:23.07-py3

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN pip install flask werkzeug pillow timm torch flask-cors
RUN pip install -r requirements.txt
RUN pip install llama-cpp-python==0.1.65 --force-reinstall --upgrade --no-cache-dir
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash


RUN mkdir ./static/animal 
RUN mkdir ./models && cd models/
RUN wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/resolve/main/llama-2-7b-chat.ggmlv3.q4_0.bin

# Install any needed packages specified in requirements.txt

RUN cd /app

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Define environment variable
ENV FLASK_RUN_HOST=0.0.0.0


