
# RTFTT‑Scaling

## Summary Project  
The **RTFTT‑Scaling** project is a Python‑based utility designed to provide scaling operations on top of the core RTFTT (Risk‑Trade‑Flow‑Time‑Trade) system. It allows you to manage multiple trading accounts, monitor trade logs and error logs, and scale execution via a GUI interface and Docker deployment. The repository includes a full GUI script (`RTFTT_Scaling_Full_GUI.py`), account configuration (`RTFTT_accounts.json`), logging mechanisms, and containerised deployment files (`Dockerfile`, `docker‑compose.yml`) for easy setup in production or test environments.

## Features  
- Full‑featured GUI interface for managing trades and scaling operations.  
- Support for multiple trading accounts – configured in `RTFTT_accounts.json`.  
- Automated logging of trades (`RTFTT_trade_log.csv`) and errors (`RTFTT_error_log.csv`).  
- Docker and docker‑compose ready for containerised deployment.  
- Python dependencies listed in `requirements.txt` for reproducible environments.  
- Modular setup with clean separation of GUI logic, configuration, logging and deployment.

## Installation Step  
1. **Clone the repository**  
   ```bash
   git clone https://github.com/mdkhussairiee/RTFTT-Scaling.git
   cd RTFTT-Scaling
   ```  
2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```  
3. **Configure accounts**  
   Edit `RTFTT_accounts.json` with your trading account details, credentials, API keys, or other parameters as required.  
4. **Run locally (without Docker)**  
   ```bash
   python RTFTT_Scaling_Full_GUI.py
   ```  
   This will launch the GUI interface and begin monitoring/logging trades as configured.  
5. **Run with Docker**  
   ```bash
   docker-compose up --build
   ```  
   This will build and run the containerised application. You can adjust settings in `docker-compose.yml`.  
6. **Check logs**  
   - `RTFTT_trade_log.csv` — stores trade execution records  
   - `RTFTT_error_log.csv` — captures error events for debugging  
7. **Shutdown / tear down**  
   If using Docker:  
   ```bash
   docker-compose down
   ```  
   Ensure any active processes or containers are stopped before making major config changes.

## Author  
**Name:** Debra (Representative, Grab Holdings)  
**Project Contact:** [Your email or GitHub handle]  
**Repository:** https://github.com/mdkhussairiee/RTFTT‑Scaling  
