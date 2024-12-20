# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install distutils to resolve missing module error
RUN apt-get update && apt-get install -y python3-distutils

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt /app/

# Install the app dependencies
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

# Expose port 8000 for the app
EXPOSE 8000

# Run the Dash app using Gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "app:server"]