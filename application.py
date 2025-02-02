import tkinter as tk
from tkinter import ttk
import sys, serial
import numpy as np
from time import sleep
from collections import deque
import matplotlib.pyplot as plt 
import matplotlib.animation as animation
import ttkbootstrap as tbs
import serial
import serial.tools.list_ports



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
def search_for_ports():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    return ports
    

label_serial = tk.Label(win, text="Serial", font=("Helvetica", 14, "bold"))
label_serial.grid(row=0, column=1, pady=10, sticky="w")
label_serial.place(x=125, y=10)

label_name = tk.Label(win, text="Name:", font=FONT)
label_name.grid(row=1, column=0, padx=15, pady=5, sticky="w")
def load_port():
    if search_for_ports() != " not found!":
        com_port = ttk.Combobox(win, values=search_for_ports(), font=FONT, width=15)
    else:
        com_port = ttk.Combobox(win, values=["COM not found!"], font=FONT, width=15)
    try:
        com_port.set(search_for_ports()[0])
    except:
        com_port.set("COM not found!")

    com_port.grid(row=1, column=1, padx=15, pady=10, sticky="e")
    return com_port

load_port()
def save_data():
    com_port = load_port()
    user_data["Name"] = com_port.get()

btn_close = tk.Button(win, text="Close", command=close_window, font=FONT)
btn_close.grid(pady=30)
btn_close.place(x=50, y= 350)

btn_save = tk.Button(win, text="Open", command=save_data, font=FONT)
btn_save.grid(pady=30)
btn_save.place(x=200, y= 350)

btn_scan = tk.Button(win, text="Scan", command=load_port, font=FONT)
btn_scan.grid(pady=30)
btn_scan.place(x=280, y= 70)


class AnalogPlot:
  # constr
    def __init__(self, strPort, maxLen=29):
      # open serial port
        self.ser = serial.Serial(strPort, 115200)

        self.ax = deque([0.0]*maxLen)
        self.ay = deque([0.0]*maxLen)
        self.maxLen = maxLen

  # add to buffer
    def addToBuf(self, buf, val):
        if len(buf) < self.maxLen:
            buf.append(val)
        else:
            buf.pop()
            buf.appendleft(val)

  # add data
    def add(self, data):
        assert(len(data) == 2)
        self.addToBuf(self.ax, data[0])
        self.addToBuf(self.ay, data[1])

  # update plot
    def update(self, frameNum, a0, a1):
        try:
            line = self.ser.readline()
            data = [float(val) for val in line.split()]
          # print data
            if(len(data) == 2):
                self.add(data)
                a0.set_data(range(self.maxLen), self.ax)
                a1.set_data(range(self.maxLen), self.ay)
        except KeyboardInterrupt:
            print('exiting')
      
        return a0, 

  # clean up
    def close(self):
      # close serial
        self.ser.flush()
        self.ser.close()    


# analogPlot = AnalogPlot(user_data['Name'], 100)

# print('plotting data...')


# fig = win.figure()
# ax = win.axes(xlim=(0, 100), ylim=(0, 1023))
# a0, = ax.plot([], [])
# a1, = ax.plot([], [])
# # anim = animation.FuncAnimation(fig, analogPlot.update, 
# #                                  fargs=(a0, a1), 
# #                                  interval=50)
# anim = animation.FuncAnimation(fig, [20, 12, 80, 35], 
#                                   fargs=(a0, a1), 
#                                   interval=50)
#win.show()

#analogPlot.close()





win.mainloop()
