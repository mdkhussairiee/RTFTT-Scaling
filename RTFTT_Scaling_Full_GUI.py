import MetaTrader5 as mt5
import time
import json
import os
import math
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# ---------------- Configuration ----------------
CONFIG_FILE = "RTFTT_accounts.json"
DAILY_DRAWDOWN = 0.03  # 3%
MIN_LOT = 0.01
RETRY_DELAY = 5
MAX_RETRIES = 3

# ---------------- Load accounts ----------------
if not os.path.exists(CONFIG_FILE):
    default_data = {"master": {"login": 0, "password": "password", "server": "server"}, "slaves": []}
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_data, f, indent=4)
    print(f"{CONFIG_FILE} created, please fill your accounts.")
    exit()

with open(CONFIG_FILE, "r") as f:
    data = json.load(f)

master = data["master"]
slaves = data["slaves"]

# ---------------- Global state ----------------
copier_paused = False
tracked_tickets = set()
slave_trade_map = {s["login"]: {} for s in slaves}
master_start_equity = 0
start_day = datetime.now().date()
master_trades_status = {}  # ticket -> status: "new", "copied", "closed"

# ---------------- MT5 Helper Functions ----------------
def login(account):
    for attempt in range(1, MAX_RETRIES+1):
        mt5.shutdown()
        if not mt5.initialize():
            time.sleep(RETRY_DELAY)
            continue
        if not mt5.login(account["login"], account["password"], account["server"]):
            time.sleep(RETRY_DELAY)
            continue
        return True
    return False

def round_lot(symbol, lot):
    info = mt5.symbol_info(symbol)
    if not info:
        return 0
    step = info.volume_step
    min_lot = info.volume_min
    lot_rounded = max(min_lot, math.floor(lot / step) * step)
    return round(lot_rounded, 2)

def copy_trade_to_slave(trade, slave, lot_multiplier):
    if not login(slave):
        return None
    volume = round_lot(trade.symbol, trade.volume * lot_multiplier)
    if volume < MIN_LOT:
        return None
    order_type = mt5.ORDER_TYPE_BUY if trade.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(trade.symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(trade.symbol).bid

    for attempt in range(1, MAX_RETRIES+1):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": trade.symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": trade.sl,
            "tp": trade.tp,
            "deviation": 20,
            "magic": 12345,
            "comment": f"Copied from {master['login']}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            slave_trade_map[slave["login"]][trade.ticket] = result.order
            master_trades_status[trade.ticket] = "copied"
            return result.order
        else:
            time.sleep(RETRY_DELAY)
    return None

def close_all_positions(account):
    if not login(account):
        return
    positions = mt5.positions_get() or []
    for p in positions:
        opposite = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(p.symbol).bid if opposite == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(p.symbol).ask
        mt5.order_send({
            "action": mt5.TRADE_ACTION_DEAL,
            "position": p.ticket,
            "symbol": p.symbol,
            "volume": p.volume,
            "type": opposite,
            "price": price,
            "deviation": 20,
            "magic": 12345,
            "comment": "Manual/Auto Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        })
    for s in slaves:
        slave_trade_map[s["login"]] = {}

# ---------------- Tooltip ----------------
class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.text = ""
    def showtip(self, text):
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack(ipadx=1)
    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# ---------------- Copier Thread ----------------
def trade_copier_loop():
    global tracked_tickets, master_start_equity, start_day
    if not login(master):
        messagebox.showerror("Error", "Cannot login master account!")
        return

    info = mt5.account_info()
    master_start_equity = info.equity if info else 0
    start_day = datetime.now().date()

    while True:
        if copier_paused:
            time.sleep(1)
            continue

        if datetime.now().date() != start_day:
            info = mt5.account_info()
            master_start_equity = info.equity if info else master_start_equity
            start_day = datetime.now().date()

        info = mt5.account_info()
        eq = info.equity if info else 0
        drawdown = ((1 - eq / master_start_equity) * 100) if master_start_equity else 0
        positions = mt5.positions_get() or []
        current_ids = {p.ticket for p in positions}

        if drawdown >= DAILY_DRAWDOWN*100:
            close_all_positions(master)
            for s in slaves:
                close_all_positions(s)
            time.sleep(5)
            continue

        new_ids = current_ids - tracked_tickets
        for tid in new_ids:
            trade = next((t for t in positions if t.ticket == tid), None)
            if trade:
                master_trades_status[tid] = "new"
                master_balance = info.balance if info else 0
                for s in slaves:
                    s_info = mt5.account_info() if login(s) else None
                    if not s_info or s_info.balance < master_balance:
                        continue
                    lot_mult = s_info.balance / master_balance
                    copy_trade_to_slave(trade, s, lot_mult)

        closed_ids = tracked_tickets - current_ids
        for tid in closed_ids:
            master_trades_status[tid] = "closed"
            for s in slaves:
                login(s)
                mapped = slave_trade_map[s["login"]].get(tid)
                if mapped:
                    close_all_positions(s)

        tracked_tickets = current_ids
        time.sleep(1)

# ---------------- GUI ----------------
class CopierGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RTFTT MT5 Copier Dashboard with Master & Slave P/L")
        self.geometry("1150x700")
        self.create_widgets()
        self.update_gui_loop()
        threading.Thread(target=trade_copier_loop, daemon=True).start()

    def create_widgets(self):
        global copier_paused
        # Master Info Frame
        self.master_frame = ttk.LabelFrame(self, text="Master Account")
        self.master_frame.pack(fill="x", padx=10, pady=5)
        self.master_equity_var = tk.StringVar()
        self.master_drawdown_var = tk.StringVar()
        self.master_trades_var = tk.StringVar()
        ttk.Label(self.master_frame, text="Equity:").grid(row=0, column=0, sticky="w")
        ttk.Label(self.master_frame, textvariable=self.master_equity_var).grid(row=0, column=1, sticky="w")
        ttk.Label(self.master_frame, text="Drawdown:").grid(row=1, column=0, sticky="w")
        ttk.Label(self.master_frame, textvariable=self.master_drawdown_var).grid(row=1, column=1, sticky="w")
        ttk.Label(self.master_frame, text="Open Trades:").grid(row=2, column=0, sticky="w")
        ttk.Label(self.master_frame, textvariable=self.master_trades_var).grid(row=2, column=1, sticky="w")
        ttk.Button(self.master_frame, text="Pause Copier", command=self.pause_copier).grid(row=0, column=2, padx=10)
        ttk.Button(self.master_frame, text="Resume Copier", command=self.resume_copier).grid(row=1, column=2, padx=10)
        ttk.Button(self.master_frame, text="Close All Trades", command=self.close_all_trades).grid(row=2, column=2, padx=10)

        # Master Trades Tree
        self.master_trades_frame = ttk.LabelFrame(self, text="Master Trades (P/L & Tooltip)")
        self.master_trades_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.master_tree = ttk.Treeview(self.master_trades_frame, columns=("Symbol","Volume","Type","Status","Entry","SL","TP","PL"), show="headings")
        for col in self.master_tree["columns"]:
            self.master_tree.heading(col, text=col)
        self.master_tree.pack(fill="both", expand=True)
        self.tooltip = ToolTip(self.master_tree)
        self.master_tree.bind("<Motion>", self.show_tooltip)

        # Slave Accounts Tree
        self.slave_frame = ttk.LabelFrame(self, text="Slave Accounts (Balance & P/L)")
        self.slave_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.slave_tree = ttk.Treeview(self.slave_frame, columns=("Balance", "Trades", "Total P/L", "Status"), show="headings")
        for col in self.slave_tree["columns"]:
            self.slave_tree.heading(col, text=col)
        self.slave_tree.pack(fill="both", expand=True)
        for s in slaves:
            self.slave_tree.insert("", "end", iid=s["login"], values=(0,0,0,"Unknown"))
        self.slave_tree.bind("<<TreeviewSelect>>", lambda e: self.update_slave_trades())

        # Slave Trades Tree
        self.slave_trades_frame = ttk.LabelFrame(self, text="Slave Trades (Select Account)")
        self.slave_trades_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.slave_trades_tree = ttk.Treeview(self.slave_trades_frame, columns=("Symbol","Volume","Type","Status","Entry","SL","TP","PL"), show="headings")
        for col in self.slave_trades_tree["columns"]:
            self.slave_trades_tree.heading(col, text=col)
        self.slave_trades_tree.pack(fill="both", expand=True)
        self.slave_trades_tooltip = ToolTip(self.slave_trades_tree)
        self.slave_trades_tree.bind("<Motion>", self.show_slave_trade_tooltip)

    # ---------------- GUI Updates ----------------
    def show_tooltip(self, event):
        iid = self.master_tree.identify_row(event.y)
        if iid:
            values = self.master_tree.item(iid, "values")
            text = f"Symbol: {values[0]}\nVolume: {values[1]}\nType: {values[2]}\nStatus: {values[3]}\nEntry: {values[4]}\nSL: {values[5]}\nTP: {values[6]}\nPL: {values[7]}"
            self.tooltip.showtip(text)
        else:
            self.tooltip.hidetip()

    def show_slave_trade_tooltip(self, event):
        iid = self.slave_trades_tree.identify_row(event.y)
        if iid:
            values = self.slave_trades_tree.item(iid, "values")
            text = f"Symbol: {values[0]}\nVolume: {values[1]}\nType: {values[2]}\nStatus: {values[3]}\nEntry: {values[4]}\nSL: {values[5]}\nTP: {values[6]}\nPL: {values[7]}"
            self.slave_trades_tooltip.showtip(text)
        else:
            self.slave_trades_tooltip.hidetip()

    def update_slave_trades(self):
        selected_slave = self.slave_tree.selection()
        if not selected_slave:
            return
        s_login = selected_slave[0]
        s_account = next(s for s in slaves if s["login"]==s_login)
        if login(s_account):
            positions = mt5.positions_get() or []
            for item in self.slave_trades_tree.get_children():
                self.slave_trades_tree.delete(item)
            for p in positions:
                mapped_master = next((m_tid for m_tid, s_tid in slave_trade_map[s_login].items() if s_tid == p.ticket), None)
                status = master_trades_status.get(mapped_master, "copied") if mapped_master else "manual"
                pl = p.profit if hasattr(p,"profit") else 0
                values = (p.symbol, p.volume, "BUY" if p.type==mt5.ORDER_TYPE_BUY else "SELL",
                          status, p.price_open, p.sl, p.tp, round(pl,2))
                tag = f"{'profit' if pl>0 else 'loss' if pl<0 else 'neutral'}_{p.ticket}"
                self.slave_trades_tree.insert("", "end", iid=p.ticket, values=values, tags=(tag,))
                if pl > 0:
                    self.slave_trades_tree.tag_configure(tag, background="lightgreen")
                elif pl < 0:
                    self.slave_trades_tree.tag_configure(tag, background="lightcoral")
                else:
                    self.slave_trades_tree.tag_configure(tag, background="lightyellow")

    def update_gui_loop(self):
        # Master update
        if login(master):
            info = mt5.account_info()
            positions = mt5.positions_get() or []
            eq = info.equity if info else 0
            balance = info.balance if info else 0
            drawdown = ((1 - eq / balance) * 100) if balance else 0
            self.master_equity_var.set(f"{eq:.2f}")
            self.master_drawdown_var.set(f"{drawdown:.2f}%")
            self.master_trades_var.set(f"{len(positions)}")
            for p in positions:
                status = master_trades_status.get(p.ticket, "new")
                pl = p.profit if hasattr(p,"profit") else 0
                values = (p.symbol, p.volume, "BUY" if p.type==mt5.ORDER_TYPE_BUY else "SELL",
                          status, p.price_open, p.sl, p.tp, round(pl,2))
                if not self.master_tree.exists(p.ticket):
                    self.master_tree.insert("", "end", iid=p.ticket, values=values)
                else:
                    self.master_tree.item(p.ticket, values=values)

        # Slave update
        for s in slaves:
            if login(s):
                info = mt5.account_info()
                positions = mt5.positions_get() or []
                balance = info.balance if info else 0
                trades = len(positions)
                total_pl = sum([p.profit for p in positions]) if positions else 0
                status = "OK" if balance >= 0 else "Error"
                self.slave_tree.item(s["login"], values=(f"{balance:.2f}", trades, f"{total_pl:.2f}", status))
                if total_pl > 0:
                    self.slave_tree.tag_configure(f"profit_{s['login']}", background="lightgreen")
                    self.slave_tree.item(s["login"], tags=(f"profit_{s['login']}",))
                elif total_pl < 0:
                    self.slave_tree.tag_configure(f"loss_{s['login']}", background="lightcoral")
                    self.slave_tree.item(s["login"], tags=(f"loss_{s['login']}",))
                else:
                    self.slave_tree.tag_configure(f"neutral_{s['login']}", background="lightyellow")
                    self.slave_tree.item(s["login"], tags=(f"neutral_{s['login']}",))

        self.after(1000, self.update_gui_loop)

    def pause_copier(self):
        global copier_paused
        copier_paused = True

    def resume_copier(self):
        global copier_paused
        copier_paused = False

    def close_all_trades(self):
        if messagebox.askyesno("Confirm","Close all trades for master and slaves?"):
            close_all_positions(master)
            for s in slaves:
                close_all_positions(s)

# ---------------- Main ----------------
if __name__ == "__main__":
    app = CopierGUI()
    app.mainloop()
