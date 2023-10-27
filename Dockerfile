# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install flask werkzeug pillow timm torch flask-cors

# Make port 80 available to the world outside this container
EXPOSE 3001

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.py"]
