import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ttkbootstrap as tbs
from functools import partial
import time

class SerialMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Monitor")
        self.root.geometry("1000x600")
        self.FONT = ("Comic Sans MS", 11, "bold")
        self.serial_connection = None
        self.animations = {}
        self.plots = {}
        self.plot_data = {f'CH{i}': {} for i in range(1, 4)}
        self.MAX_POINTS = 100
        self.plot_start_time = None

        try:
            self.root.iconbitmap('serial_port.ico')
        except:
            pass

        self.setup_ui()

    def setup_ui(self):
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        
        self.port_frame = ttk.LabelFrame(self.top_frame, text=" 🚀 Serial Port ", padding=(10, 5))
        self.port_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        tk.Label(self.port_frame, text="Port:", font=self.FONT, fg="#ff4500").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ports = self.search_for_ports()
        self.com_port = ttk.Combobox(self.port_frame, values=self.ports, font=self.FONT, width=20, state="readonly")
        self.com_port.grid(row=0, column=1, padx=5, pady=5)
        self.com_port.set(self.ports[0] if self.ports else "No Port Found!")
        btn_scan = ttk.Button(self.port_frame, text="🔍 Scan", command=self.refresh_ports, bootstyle="info-outline")
        btn_scan.grid(row=0, column=2, padx=5, pady=5)
        
        self.channel_select_frame = ttk.LabelFrame(self.top_frame, text=" 🖥️ Channels ", padding=(10, 5))
        self.channel_select_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.channel_vars = {
            "CH1": tk.BooleanVar(value=False),
            "CH2": tk.BooleanVar(value=False),
            "CH3": tk.BooleanVar(value=False)
        }
        col = 0
        for ch_name, var in self.channel_vars.items():
            ttk.Checkbutton(self.channel_select_frame, text=ch_name, variable=var,
                            command=lambda name=ch_name: self.toggle_channel(name)
                           ).grid(row=0, column=col, padx=10, pady=5, sticky="w")
            col += 1

        dark_button = tbs.Checkbutton(self.top_frame, text="🌙 Dark Mode", bootstyle="success-round-toggle", 
                                      command=self.change_theme)
        dark_button.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        
        self.channel_frames = {}   
        self.plot_frames = {}     
        
        self.control_frame = ttk.LabelFrame(self.root, text=" 🎛️ Controls ", padding=(10, 5))
        self.control_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        btn_open = ttk.Button(self.control_frame, text="🚀 Open", command=self.open_serial, bootstyle="success-outline")
        btn_open.grid(row=0, column=0, padx=10, pady=5)
        btn_close = ttk.Button(self.control_frame, text="❌ Close", command=self.close_application, bootstyle="danger-outline")
        btn_close.grid(row=0, column=1, padx=10, pady=5)

    def toggle_channel(self, channel_name):
        is_visible = self.channel_vars[channel_name].get()
        row_position = {"CH1": 1, "CH2": 2, "CH3": 3}[channel_name]

        if is_visible:
            if channel_name not in self.channel_frames or not self.channel_frames[channel_name]:
                settings_frame = ttk.LabelFrame(self.root, text=f"⚙️ {channel_name} Setting", padding=(10, 5))
                settings_frame.grid(row=row_position, column=0, padx=10, pady=5, sticky="ew")
                self.channel_frames[channel_name] = settings_frame
                self.setup_channel_settings(channel_name, settings_frame)
            else:
                self.channel_frames[channel_name].grid()
 
            if channel_name not in self.plot_frames or not self.plot_frames[channel_name]:
                plot_frame = ttk.LabelFrame(self.root, text=f"📊 {channel_name} Plot Options", padding=(10, 5))
                plot_frame.grid(row=row_position, column=1, padx=10, pady=5, sticky="ew")
                self.plot_frames[channel_name] = plot_frame
                self.setup_plot_options(channel_name, plot_frame)
            else:
                self.plot_frames[channel_name].grid()
        else:
            if channel_name in self.channel_frames and self.channel_frames[channel_name]:
                self.channel_frames[channel_name].grid_remove()
            if channel_name in self.plot_frames and self.plot_frames[channel_name]:
                self.plot_frames[channel_name].grid_remove()

    def setup_channel_settings(self, channel_name, frame):
        tk.Label(frame, text="Working method:", font=self.FONT, fg="#ff4500").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        method_var = tk.StringVar(value="")
        setattr(self, f"{channel_name}_method", method_var)
        methods = [("R", "R"), ("I", "I"), ("P", "P")]
        for i, (text, value) in enumerate(methods):
            ttk.Radiobutton(frame, text=text, variable=method_var, value=value).grid(
                row=0, column=i+1, padx=5, pady=2, sticky="w")
        value_entry = ttk.Entry(frame, width=10)
        value_entry.grid(row=0, column=4, padx=2, pady=2, sticky="w")
        setattr(self, f"{channel_name}_value", value_entry)
        unit_label = tk.Label(frame, text="", font=self.FONT, fg="#ff4500")
        unit_label.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        setattr(self, f"{channel_name}_unit", unit_label)
        method_var.trace_add("write", lambda *args, ch=channel_name: self.update_unit_label(ch))

    def setup_plot_options(self, channel_name, frame):
        plot_vars = {
            "I": tk.BooleanVar(value=False),
            "V": tk.BooleanVar(value=False),
            "R": tk.BooleanVar(value=False),
            "P": tk.BooleanVar(value=False)
        }
        setattr(self, f"{channel_name}_plot_vars", plot_vars)
        tk.Label(frame, text="Plot:", font=self.FONT, fg="#ff4500").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        for i, (text, var) in enumerate(plot_vars.items()):
            ttk.Checkbutton(frame, text=text, variable=var).grid(
                row=0, column=i+1, padx=10, pady=2, sticky="w")

    def update_unit_label(self, channel_name):
        method_var = getattr(self, f"{channel_name}_method")
        unit_label = getattr(self, f"{channel_name}_unit")
        method = method_var.get()
        units = {"R": "Ω", "I": "A", "P": "W"}
        if method in units:
            unit_label.config(text=units[method])
        else:
            unit_label.config(text="")

    def change_theme(self):
        theme = self.root.style.theme.name if hasattr(self.root, "style") else "litera"
        self.root.style.theme_use("litera" if theme == "darkly" else "darkly")
        
    def search_for_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def refresh_ports(self):
        self.ports = self.search_for_ports()
        self.com_port["values"] = self.ports
        self.com_port.set(self.ports[0] if self.ports else "No Port Found!")

    def open_serial(self):
        self.plot_start_time = time.time()
        port_name = self.com_port.get()
        if not port_name or port_name == "No Port Found!":
            return
        try:
            if self.serial_connection:
                self.close_serial()
            self.serial_connection = SerialDataHandler(port_name)
            active_channels = [ch for ch, var in self.channel_vars.items() if var.get()]
            if not active_channels:
                print("No channels selected")
                return
            for channel in active_channels:
                plot_vars = getattr(self, f"{channel}_plot_vars")
                for measure, var in plot_vars.items():
                    if var.get():
                        self.create_plot_for_measure(channel, measure)
        except Exception as e:
            print(f"Error opening serial port: {e}")
        
    def create_plot_for_measure(self, channel, measure):
        fig = plt.figure(figsize=(6, 3))
        fig.canvas.manager.set_window_title(f"{channel} {measure} Plot")
        ax = fig.add_subplot(1, 1, 1)
        key = f"{channel}_{measure}"
        self.plots[key] = {'fig': fig, 'ax': ax}
        anim = animation.FuncAnimation(
            fig,
            lambda i: self.animate_measure(channel, measure, i),
            interval=50
        )
        self.animations[key] = anim
        plt.grid()
        plt.tight_layout()
        plt.show(block=False)

    def animate_measure(self, channel, measure, i):
        if not self.serial_connection:
            return
        data = self.serial_connection.get_data()
        if not data or "time" not in data:
            return

        time_val = data["time"]
        
        if measure not in self.plot_data[channel]:
            self.plot_data[channel][measure] = {'x': [], 'y': []}
        self.plot_data[channel][measure]['x'].append(time_val)
        self.plot_data[channel][measure]['y'].append(data.get(measure, 0))
        if len(self.plot_data[channel][measure]['x']) > self.MAX_POINTS:
            self.plot_data[channel][measure]['x'].pop(0)
            self.plot_data[channel][measure]['y'].pop(0)

        key = f"{channel}_{measure}"
        ax = self.plots[key]['ax']
        ax.clear()
        ax.plot(self.plot_data[channel][measure]['x'],
                self.plot_data[channel][measure]['y'],
                label=measure)
        ax.set_title(f"{channel} {measure} Data")
        ax.grid(True)
        ax.legend()

    def close_serial(self):
        for key, anim in self.animations.items():
            if anim and hasattr(anim, "event_source") and anim.event_source:
                anim.event_source.stop()  
        for key, plot_info in self.plots.items():
            plt.close(plot_info['fig'])
        self.animations = {}
        self.plots = {}
        for channel in self.plot_data:
            self.plot_data[channel] = {}
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None

    def close_application(self):
        self.close_serial()
        self.root.destroy()

class SerialDataHandler:
    def __init__(self, port):
        self.ser = serial.Serial(port, 115200, timeout=1)
    def get_data(self):
        try:
            if self.ser.in_waiting > 0:
                str_line = self.ser.readline().decode('utf-8', errors="ignore").strip()
                if not str_line:
                    return {}
            else:
                return {}

            values = []
            elapsed_time = time.time()
            values.append(elapsed_time)

            if len(str_line) >= 11:
                if str_line[1] == ':' and len(str_line) > 3:
                    V = ord(str_line[2]) * 256 + ord(str_line[3])
                    values.append(V)
                else:
                    values.append(0)
                
                if len(str_line) > 6 and str_line[4] == ':':
                    I = ord(str_line[5]) * 256 + ord(str_line[6])
                    values.append(I)
                else:
                    values.append(0)
                
                if len(str_line) > 10 and str_line[8] == ':':
                    G = ord(str_line[9]) * 256 + ord(str_line[10])
                    R = 1 / G if G != 0 else 0
                    values.append(R)
                else:
                    values.append(0)
                
                try:
                    P = values[1] * values[2]
                except Exception:
                    P = 0
                values.append(P)
            else:
                values.extend([0, 0, 0, 0])

            keys = ["time", "V", "I", "R", "P"]
            return dict(zip(keys, values))
        except Exception as e:
            print(f"Error receiving data: {e}")
            return {}

    def close(self):
        self.ser.close()

if __name__ == "__main__":
    win = tbs.Window(themename="litera")
    app = SerialMonitor(win)
    win.mainloop()

