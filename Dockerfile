# Use an official Python image as the base image
FROM python:3.11.1

# Set the working directory in the container to /app
WORKDIR /

# Copy the requirements.txt file to the container
COPY requirements.txt /requirements.txt

# Install the required packages in the container
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files to the container
COPY . /

# Specify the command to run when the container starts
CMD [ "python", "main.py"]
