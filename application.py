import tkinter as tk
from tkinter import ttk
import Plot_serial

win = tk.Tk()
win.title("Serial Monitor")

def close_window():
    win.destroy()

def save_data():
    user_data["Name"] = com_port.get()
    user_data["Baud"] = baud_rate.get()
    user_data["Data size"] = data_size.get()
    user_data["Parity"] = parity.get()
    user_data["Handshake"] = handshake.get()
    user_data["Mode"] = mode.get()

screen_x = win.winfo_screenwidth()
screen_y = win.winfo_screenwidth()

center_x = int(screen_x/2 - 400)
center_y = int(screen_y/2 - 650)
win.geometry((f'900x500+{center_x}+{center_y}'))
win.iconbitmap('serial_port.ico')



FONT = ("Helvetica", 10)

user_data = {}



label_serial = tk.Label(win, text="Serial", font=("Helvetica", 14, "bold"))
label_serial.grid(row=0, column=1, pady=10, sticky="w")


label_name = tk.Label(win, text="Name:", font=FONT)
label_name.grid(row=1, column=0, padx=15, pady=5, sticky="w")
com_port = ttk.Combobox(win, values=["COM1", "COM2", "COM3", "COM4", "COM5", "COM6"], font=FONT, width=20)
com_port.set("COM6")
com_port.grid(row=1, column=1, padx=15, pady=10, sticky="e")

label_baud = tk.Label(win, text="Baud:", font=FONT)
label_baud.grid(row=2, column=0, padx=15, pady=10, sticky="w")
baud_rate = ttk.Combobox(win, values=["9600", "115200", "19200", "38400"], font=FONT, width=20)
baud_rate.set("115200")
baud_rate.grid(row=2, column=1, padx=15, pady=10, sticky="e")

label_data = tk.Label(win, text="Data size:", font=FONT)
label_data.grid(row=3, column=0, padx=15, pady=10, sticky="w")
data_size = ttk.Combobox(win, values=["7", "8", "9"], font=FONT, width=20)
data_size.set("8")
data_size.grid(row=3, column=1, padx=15, pady=10, sticky="e")

label_parity = tk.Label(win, text="Parity:", font=FONT)
label_parity.grid(row=4, column=0, padx=15, pady=10, sticky="w")
parity = ttk.Combobox(win, values=["none", "even", "odd"], font=FONT, width=20)
parity.set("none")
parity.grid(row=4, column=1, padx=15, pady=10, sticky="e")

label_handshake = tk.Label(win, text="Handshake:", font=FONT)
label_handshake.grid(row=5, column=0, padx=15, pady=10, sticky="w")
handshake = ttk.Combobox(win, values=["OFF", "RTS/CTS", "XON/XOFF"], font=FONT, width=20)
handshake.set("OFF")
handshake.grid(row=5, column=1, padx=15, pady=10, sticky="e")

label_mode = tk.Label(win, text="Mode:", font=FONT)
label_mode.grid(row=6, column=0, padx=15, pady=10, sticky="w")
mode = ttk.Combobox(win, values=["Setup", "Test"], font=FONT, width=20)
mode.set("Setup")
mode.grid(row=6, column=1, padx=15, pady=10, sticky="e")


btn_close = tk.Button(win, text="Close", command=close_window, font=FONT)
btn_close.grid(row=7, column=1, pady=30)

btn_save = tk.Button(win, text="Open", command=save_data, font=FONT)
btn_save.grid(row=7, column=0, pady=30)



win.mainloop()