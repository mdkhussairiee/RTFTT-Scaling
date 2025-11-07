
# RTFTT MT5 Trade Scaling

## Description
**RTFTT MT5 Trade Scaling** is a Python-based MetaTrader 5 (MT5) automation tool that allows users to copy trades from a master account to multiple slave accounts in real-time. It provides a GUI to monitor master and slave accounts, trade status, and profit/loss.

## Summary Project
This project supports multiple slave accounts, automatically scales lot sizes, tracks open and closed trades, and handles daily drawdown limits. The GUI dashboard allows users to pause, resume, or close trades with a single click.

## Features
- Real-time trade copying from master to slave accounts.
- Automatic lot size scaling based on balance.
- Master and slave monitoring with P/L display.
- GUI dashboard with pause/resume and close-all trades.
- Threaded architecture for smooth real-time updates.
- Risk Management:
  - Daily drawdown limit (3% by default).
  - Minimum lot enforcement.
  - Retry mechanism for login/order failures.

## Installation with Docker on Windows
1. **Clone the repository**
   ```bash
   git clone https://github.com/mdkhussairiee/RTFTT-Scaling.git
   cd RTFTT-Scaling
   ```  
2. **Configure Accounts**  
   Edit `RTFTT_accounts.json` with your trading account details, credentials, API keys, or other parameters as required.  
3. **Run the application**  
   ```bash
   docker compose up --build
   ```  
   This will launch the GUI interface and begin monitoring/logging trades as configured.   
4. **Shutdown / tear down**  
   If using Docker:  
   ```bash
   docker-compose down
   ```  
   Make sure Docker Desktop is set to Windows containers mode.

## Author  
**Name:** King (Representative, RTFTT)  
**Project Contact:** [aslan.the.king.1981@gmail.com]  
**Repository:** https://github.com/mdkhussairiee/RTFTT‑Scaling  
