# Use an official Python runtime as a parent image
FROM nvcr.io/nvidia/pytorch:23.07-py3

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
RUN git clone https://github.com/YatoWatch/AnimalGPT.git



# Install any needed packages specified in requirements.txt

RUN cd /app

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Define environment variable
ENV FLASK_RUN_HOST=0.0.0.0


