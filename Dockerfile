# Use Windows Python image
FROM mcr.microsoft.com/windows/python:3.11

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

# Default command
CMD ["python", "RTFTT_Scaling_Full_GUI.py"]
