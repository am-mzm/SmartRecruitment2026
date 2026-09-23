# Use an official Python image as the base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /pybackend_revised

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Copy the requirements file into the container
COPY requirements_revised.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements_revised.txt

RUN pip install huggingface_hub[hf_xet]

# Install NLTK resources
RUN python -m nltk.downloader stopwords punkt punkt_tab

# Copy the application code and the chroma folder into the container
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8002

# Set the command to run the `run.py` script
CMD ["python", "-m", "uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8002"]