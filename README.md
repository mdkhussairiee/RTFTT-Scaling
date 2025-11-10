# MT4/MT5 Copy Trading System

## Overview

This system is a **full-featured MT4/MT5 copy trading platform** with:

- Multiple **Master accounts** (MT4/MT5)  
- Multiple **Slave accounts** (MT4/MT5)  
- **Live trade replication** from master to slaves  
- **Admin dashboard** to monitor trades in real-time  
- **Cross-platform architecture** using Windows for MTApi and Docker for dashboard  

The system is designed to run **real MT terminals** using the MTApi plugin and communicates trades via **RabbitMQ**.  

---

## Architecture

```
[MT4/MT5 Master] ---> [Backend Windows App] ---> RabbitMQ ---> [SlaveBridge Windows App] ---> [MT4/MT5 Slaves]
                                                                             --> [Admin UI Docker] (React Dashboard)
```

### Components

| Component | Platform | Description |
|-----------|---------|-------------|
| Backend | Windows | Reads trades from Master MT terminals using MTApi and publishes to RabbitMQ |
| Slave Bridge | Windows | Subscribes to RabbitMQ and executes trades on Slave MT terminals |
| RabbitMQ | Docker/Linux | Message broker for trade events |
| Admin UI | Docker/Linux | React dashboard for monitoring Masters, Slaves, and live trades |

---

## Features

- Multiple Master & Slave account support  
- Adjustable lot sizes and risk settings  
- Live trade monitoring on Admin Dashboard  
- Cross-platform deployment (Windows + Linux/Docker)  
- Fully automated setup scripts  

---

## Installation

### 1️⃣ Linux / Docker Setup (RabbitMQ + Admin UI)

1. Make the setup script executable:

```bash
chmod +x setup_copytrade_system.sh
```

2. Run the setup script:

```bash
./setup_copytrade_system.sh
```

3. Navigate to the generated folder and start Docker services:

```bash
cd copytrade-mt-live-system
docker compose up --build
```

- RabbitMQ will run on **ports 5672 (AMQP) and 15672 (management UI)**  
- Admin Dashboard will be accessible at **http://localhost:3000**  

---

### 2️⃣ Windows Setup (Backend + Slave Bridge)

1. Copy `setup_copytrade_system.ps1` from the Linux folder to your Windows host.  
2. Open **PowerShell as Administrator** and allow script execution:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. Run the setup script:

```powershell
.\setup_copytrade_system.ps1
```

4. This will create:

```
C:\CopyTradeSystem
├── Backend        # Master backend application
├── SlaveBridge    # Slave trade replication application
└── lib            # MTApi.dll
```

5. Ensure **MT4/MT5 terminals** are running on Windows with **MTApi plugin installed**.  
6. Run the applications:

```powershell
cd C:\CopyTradeSystem\Backend
dotnet run

cd C:\CopyTradeSystem\SlaveBridge
dotnet run
```

---

### 3️⃣ Admin Dashboard

- Once Docker services are running, open **http://localhost:3000** in your browser  
- Monitor:

  - Master accounts  
  - Slave accounts  
  - Live trades  

---

## Configuration & Risk Management

### Adding Master Accounts

1. Launch MT4/MT5 terminal and connect as a **Master account**.  
2. Configure **MTApi plugin** with correct port (default 8222).  
3. In Admin Dashboard, click **Add Master** to register the account.  

### Adding Slave Accounts

1. Launch separate MT4/MT5 terminals as **Slave accounts**.  
2. Configure MTApi plugin with different port (default 8223).  
3. Register Slave accounts in Admin Dashboard or directly in `SlaveBridge` environment variables:

```
MT_SERVER=<slave_terminal_host>
MT_LOGIN=<login_number>
MT_PASSWORD=<password>
MT_TYPE=MT5
```

### Lot Size & Risk Management

- Default **1x lot multiplier**.  
- You can adjust risk per Slave by modifying `riskMultiplier` in `SlaveBridge`:

```csharp
double riskMultiplier = 1.0; // Increase or decrease per strategy
lot *= riskMultiplier;
```

- For multiple Slaves with tiered lots, apply multipliers like:

| Slave Account | Lot Multiplier |
|---------------|----------------|
| Slave 1       | 1.0            |
| Slave 2       | 1.2            |
| Slave 3       | 1.5            |

- Ensure total exposure does not exceed your risk limits.  

### Trade Execution Settings

- Stop loss / take profit can be configured in MT4/MT5 EA or via MTApi commands if needed.  
- Trades are executed **asynchronously**, so monitoring via dashboard is recommended.  

---

## Folder Structure

```
copytrade-system/
├── setup_copytrade_system.sh          # Linux setup script
├── setup_copytrade_system.ps1         # Windows setup script
├── docker-compose.yml                 # Docker services
├── admin-ui/                          # React Admin Dashboard
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── services/api.js
│       └── components/
│           ├── MasterList.jsx
│           ├── SlaveList.jsx
│           └── TradeMonitor.jsx
```

---

## Quick Start Summary

1. **Linux**: 

```bash
./setup_copytrade_system.sh
cd copytrade-system
docker compose up --build
```

2. **Windows**:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_copytrade_system.ps1
cd C:\CopyTradeSystem\Backend
dotnet run
cd C:\CopyTradeSystem\SlaveBridge
dotnet run
```

3. **Browser**: Open Admin Dashboard at `http://localhost:3000`  

---

## Notes

- The system **requires MT4/MT5 terminals on Windows** for real trading.  
- MTApi.dll is Windows-only, so the Backend and Slave Bridge **cannot run in Linux containers**.  
- Docker is used only for **RabbitMQ and Admin UI**, which can run cross-platform.  

---

## License

This project is **free to use and modify**.

---

## ⚡⚡⚡ Author  
**Name:** King (Representative, RTFTT)  
**Project Contact:** [aslan.the.king.1981@gmail.com]  
**Repository:** https://github.com/mdkhussairiee/RTFTT‑Scaling  