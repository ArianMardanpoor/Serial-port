import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ttkbootstrap as tbs

win = tbs.Window(themename="litera")
win.title("Serial Monitor")
win.geometry("700x500")

FONT = ("Comic Sans MS", 11, "bold")

try:
    win.iconbitmap('serial_port.ico')
except:
    pass

def change_theme():
    theme = win.style.theme.name
    win.style.theme_use("litera" if theme == "darkly" else "darkly")

dark_button = tbs.Checkbutton(win, text="Dark Mode", bootstyle="success-round-toggle", command=change_theme)
dark_button.grid(row=0, column=1, pady=10, padx=10, sticky="e")

def search_for_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

frame_serial = ttk.LabelFrame(win, text=" 🚀 Serial Port ", padding=(10, 5))
frame_serial.grid(row=1, column=0, padx=20, pady=10, sticky="ew", columnspan=2)

tk.Label(frame_serial, text="Port:", font=FONT, fg="#ff4500").grid(row=0, column=0, padx=5, pady=5, sticky="w")

com_port = ttk.Combobox(frame_serial, values=search_for_ports(), font=FONT, width=20, state="readonly")
com_port.grid(row=0, column=1, padx=5, pady=5)
ports = search_for_ports()
com_port.set(ports[0] if ports else "No Port Found!")

def refresh_ports():
    ports = search_for_ports()
    com_port["values"] = ports
    com_port.set(ports[0] if ports else "No Port Found!")

btn_scan = ttk.Button(frame_serial, text="🔍 Scan", command=refresh_ports, bootstyle="info-outline")
btn_scan.grid(row=0, column=2, padx=5, pady=5)

class CreateData:
    def __init__(self, port):
        self.ser = serial.Serial(port, 115200, timeout=1)

    def get_data(self):
        try:
            if self.ser.in_waiting > 0:
                str_line = self.ser.readline().decode('utf-8').strip()
                if not str_line:
                    return {}
                values = str_line.split(',')
                data = []
                for x in values:
                    try:
                        data.append(float(x.strip()))
                    except ValueError:
                        continue
                p_dic = {}
                for i in range(0, min(len(data), 6), 2):
                    p_dic[f'plot{(i//2)+1}'] = data[i:i+2]
                return p_dic
        except Exception as e:
            print(f"Error receiving data: {e}")
            return {}
        return {}
    
    def close(self):
        self.ser.close()

def save_data():
    if com_port != "No Port Found!":
        port_name = com_port.get()
        if not port_name or port_name == "No Port Found":
            return
        
        try:
            analogPlot = CreateData(port_name)
            x_list, y_list = [], []
            MAX_POINTS = 100

            
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)
            
            def animate(i,xs,xy):
                dic_port = analogPlot.get_data()
                if dic_port and 'plot1' in dic_port:
                    first_plot_list = dic_port['plot1']
                    if len(first_plot_list) == 2:
                        x_list.append(first_plot_list[0])
                        y_list.append(first_plot_list[1])
                        if len(x_list) > MAX_POINTS:
                            x_list.pop(0)
                            y_list.pop(0)
                ax.clear()
                ax.plot(x_list, y_list)
                plt.grid()
                plt.hot()
                # plt.xticks(rotation=45, ha='right')
                # plt.subplots_adjust(bottom=0.30)


            
            global anim
            anim = animation.FuncAnimation(fig, animate, fargs=(x_list,y_list), interval=50)
            plt.show()

            def on_close():
                anim.event_source.stop()
                analogPlot.close()

            

        except Exception as e:
            print(f"Error opening serial port: {e}")
    else:
        ttk.Label(text="No Port Found!")
frame_buttons = ttk.LabelFrame(win, text=" 🎛️ Controls ", padding=(10, 5))
frame_buttons.grid(row=3, column=0, padx=20, pady=10, sticky="ew", columnspan=2)

btn_save = ttk.Button(frame_buttons, text="🚀 Open", command=save_data, bootstyle="success-outline")
btn_save.grid(row=1, column=0, padx=10, pady=10)

btn_close = ttk.Button(frame_buttons, text="❌ Close", command=win.destroy, bootstyle="danger-outline")
btn_close.grid(row=1, column=1, padx=10, pady=10)

win.mainloop()

