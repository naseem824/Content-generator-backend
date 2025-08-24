# Use an official, lightweight Python 3.11.9 image
FROM python:3.11.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of your application code (app.py, prompt.txt, etc.)
COPY . .

# Tell the container to listen on port 10000
EXPOSE 10000

# The command to run your application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
