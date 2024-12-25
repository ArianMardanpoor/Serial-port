import tkinter as tk
from tkinter import ttk
import sys, serial
import numpy as np
from time import sleep
from collections import deque
import matplotlib.pyplot as plt 
import matplotlib.animation as animation
import ttkbootstrap as tbs

win = tbs.Window(themename="litera")
win.title("Serial Monitor")

def change_theme():
    theme = win.style.theme.name
    if theme == "litera":
        win.style.theme_use("darkly")
    else:
        win.style.theme_use("litera")

dark_button = tbs.Checkbutton(win, text="Dark Mode", bootstyle="round-toggle", command=change_theme)
dark_button.grid(pady=20, column=20)

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
try:
    win.iconbitmap('serial_port.ico')
except:
    pass


FONT = ("Helvetica", 10)

user_data = {}



label_serial = tk.Label(win, text="Serial", font=("Helvetica", 14, "bold"))
label_serial.grid(row=0, column=1, pady=10, sticky="w")


label_name = tk.Label(win, text="Name:", font=FONT)
label_name.grid(row=1, column=0, padx=15, pady=5, sticky="w")
com_port = ttk.Combobox(win, values=["COM1", "COM2", "COM3", "COM4", "COM5", "COM6"], font=FONT, width=15)
try:
    com_port.set(user_data["Name"])
except:
    com_port.set("COM6")
com_port.grid(row=1, column=1, padx=15, pady=10, sticky="e")

label_baud = tk.Label(win, text="Baud:", font=FONT)
label_baud.grid(row=2, column=0, padx=15, pady=10, sticky="w")
baud_rate = ttk.Combobox(win, values=["9600", "115200", "19200", "38400"], font=FONT, width=15)
try:
    baud_rate.set(user_data["Baud"])
except:
    baud_rate.set("115200")
baud_rate.grid(row=2, column=1, padx=15, pady=10, sticky="e")

label_data = tk.Label(win, text="Data size:", font=FONT)
label_data.grid(row=3, column=0, padx=15, pady=10, sticky="w")
data_size = ttk.Combobox(win, values=["7", "8", "9"], font=FONT, width=15)
try:
    data_size.set(user_data["Data size"])
except:
    data_size.set("8")
data_size.grid(row=3, column=1, padx=15, pady=10, sticky="e")

label_parity = tk.Label(win, text="Parity:", font=FONT)
label_parity.grid(row=4, column=0, padx=15, pady=10, sticky="w")
parity = ttk.Combobox(win, values=["none", "even", "odd"], font=FONT, width=15)
try:
    parity.set(user_data["Parity"])
except:
    parity.set("none")
parity.grid(row=4, column=1, padx=15, pady=10, sticky="e")

label_handshake = tk.Label(win, text="Handshake:", font=FONT)
label_handshake.grid(row=5, column=0, padx=15, pady=10, sticky="w")
handshake = ttk.Combobox(win, values=["OFF", "RTS/CTS", "XON/XOFF"], font=FONT, width=15)
try:
    handshake.set(user_data["Handshake"])
except:
    handshake.set("OFF")
handshake.grid(row=5, column=1, padx=15, pady=10, sticky="e")

label_mode = tk.Label(win, text="Mode:", font=FONT)
label_mode.grid(row=6, column=0, padx=15, pady=10, sticky="w")
mode = ttk.Combobox(win, values=["Setup", "Test"], font=FONT, width=15)
try:
    mode.set(user_data["Mode"])
except:
    mode.set("Setup")
mode.grid(row=6, column=1, padx=15, pady=10, sticky="e")


btn_close = tk.Button(win, text="Close", command=close_window, font=FONT)
btn_close.grid(row=7, column=1, pady=30)

btn_save = tk.Button(win, text="Open", command=save_data, font=FONT)
btn_save.grid(row=7, column=0, pady=30)

# class AnalogPlot:
#   # constr
#     def __init__(self, strPort, maxLen=29):
#       # open serial port
#         self.ser = serial.Serial(strPort, 115200)

#         self.ax = deque([0.0]*maxLen)
#         self.ay = deque([0.0]*maxLen)
#         self.maxLen = maxLen

#   # add to buffer
#     def addToBuf(self, buf, val):
#         if len(buf) < self.maxLen:
#             buf.append(val)
#         else:
#             buf.pop()
#             buf.appendleft(val)

#   # add data
#     def add(self, data):
#         assert(len(data) == 2)
#         self.addToBuf(self.ax, data[0])
#         self.addToBuf(self.ay, data[1])

#   # update plot
#     def update(self, frameNum, a0, a1):
#         try:
#             line = self.ser.readline()
#             data = [float(val) for val in line.split()]
#           # print data
#             if(len(data) == 2):
#                 self.add(data)
#                 a0.set_data(range(self.maxLen), self.ax)
#                 a1.set_data(range(self.maxLen), self.ay)
#         except KeyboardInterrupt:
#             print('exiting')
      
#         return a0, 

#   # clean up
#     def close(self):
#       # close serial
#         self.ser.flush()
#         self.ser.close()    


# # analogPlot = AnalogPlot(user_data['Name'], 100)

# print('plotting data...')

  # set up animation
# fig = plt.figure()
# ax = plt.axes(xlim=(0, 100), ylim=(0, 1023))
# a0, = ax.plot([], [])
# a1, = ax.plot([], [])
# # anim = animation.FuncAnimation(fig, analogPlot.update, 
# #                                  fargs=(a0, a1), 
# #                                  interval=50)
# anim = animation.FuncAnimation(fig, [20, 12, 80, 35], 
#                                   fargs=(a0, a1), 
#                                   interval=50)
# plt.show()

# analogPlot.close()


# t = np.linspace(10,100,1000)
# y = np.sin(t)

# a = plot(t, y)


win.mainloop()
