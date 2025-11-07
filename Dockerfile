# Use official Python image
FROM python:3.12-slim

# Install Tkinter dependencies for GUI
RUN apt-get update && apt-get install -y \
    python3-tk \
    tcl8.6-dev tk8.6-dev \
    libffi-dev \
    libssl-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    xvfb \
 && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set display for Tkinter (headless option)
ENV DISPLAY=:99

# Run the copier script
CMD ["python", "RTFTT_Scaling_Full_GUI.py"]
