# Use the official Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

## Copy the requirements file into the container
#COPY requirements.txt .
#
## Install dependencies
#RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application code into the container
COPY . .

# Expose port 5000
EXPOSE 5000

# Command to run the Flask application
CMD ["python", "app.py"]
