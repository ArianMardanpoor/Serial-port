<<<<<<< HEAD
import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ttkbootstrap as tbs
from functools import partial

class SerialMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Monitor")
        self.root.geometry("1000x600")
        self.FONT = ("Comic Sans MS", 11, "bold")
        self.serial_connection = None
        self.animations = {}
        self.plots = {}
        self.plot_data = {f'CH{i}': {'x': [], 'y': []} for i in range(1, 4)}
        self.MAX_POINTS = 100

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
        
        # فریم انتخاب کانال (سمت راست)
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
                plot_frame = ttk.LabelFrame(self.root, text=f"📊 {channel_name} Plot", padding=(10, 5))
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
                self.create_plot_for_channel(channel)
        except Exception as e:
            print(f"Error opening serial port: {e}")

    def create_plot_for_channel(self, channel):

        fig = plt.figure(figsize=(6, 3))
        fig.canvas.manager.set_window_title(f"{channel} Plot")
        ax = fig.add_subplot(1, 1, 1)
        self.plots[channel] = {'fig': fig, 'ax': ax}
        anim = animation.FuncAnimation(
            fig,
            lambda i: self.animate_channel(channel, i),
            interval=50
        )
        self.animations[channel] = anim
        plt.grid()
        plt.tight_layout()
        plt.show(block=False)

    def animate_channel(self, channel, i):
        if not self.serial_connection:
            return
        data = self.serial_connection.get_data()
        ch_index = int(channel[-1])
        plot_key = f'plot{ch_index}'
        if data and plot_key in data:
            plot_data = data[plot_key]
            if len(plot_data) == 2:
                self.plot_data[channel]['x'].append(plot_data[0])
                self.plot_data[channel]['y'].append(plot_data[1])
                if len(self.plot_data[channel]['x']) > self.MAX_POINTS:
                    self.plot_data[channel]['x'].pop(0)
                    self.plot_data[channel]['y'].pop(0)
        ax = self.plots[channel]['ax']
        ax.clear()
        ax.plot(self.plot_data[channel]['x'], self.plot_data[channel]['y'], 'b-')
        ax.set_title(f"{channel} Data")
        ax.grid(True)

    def close_serial(self):
        for channel, anim in self.animations.items():
            anim.event_source.stop()
        for channel, plot_info in self.plots.items():
            plt.close(plot_info['fig'])
        self.animations = {}
        self.plots = {}
        for channel in self.plot_data:
            self.plot_data[channel] = {'x': [], 'y': []}
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
    def close(self):
        self.ser.close()

if __name__ == "__main__":
    win = tbs.Window(themename="litera")
    app = SerialMonitor(win)
    win.mainloop()

=======
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.animation as animation
import numpy as np  
import time
import ttkbootstrap as tbs

class SerialCommunicationHandler:
    def __init__(self, port):
        self.ser = serial.Serial(port, 115200, timeout=1)
        self.last_read_time = time.time()
        self.read_interval = 0.05  # 50ms minimum interval between reads
    
    def send_channel_config(self, channel, method, value):
        try:
            channel_map = {'CH1': 1, 'CH2': 2, 'CH3': 3}
            method_map = {'R': 1, 'I': 2, 'P': 3}
            
            value = max(0, min(int(value), 65535))
            high_byte = (value >> 8) & 0xFF
            low_byte = value & 0xFF
            
            packet = bytearray([
                channel_map.get(channel, 0),
                method_map.get(method, 0),
                high_byte,
                low_byte
            ])
            
            self.ser.write(packet)
            response = self.ser.readline().decode('utf-8').strip()
            return response == "OK"
        
        except Exception as e:
            print(f"Error sending channel config: {e}")
            return False
    
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
        if self.ser.is_open:
            self.ser.close()

class AdvancedSerialMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Advanced Serial Monitor Pro")
        self.root.geometry("1000x600")
        
        self.FONT = ("Segoe UI", 11, "bold")
        self.serial_connection = None
        self.connection_status = False
        
        # Plot settings
        self.plot_settings = {
            'auto_scale': tk.BooleanVar(value=True),
            'grid_enabled': tk.BooleanVar(value=True),
            'legend_enabled': tk.BooleanVar(value=True),
            'update_interval': tk.IntVar(value=100)  # Increased update interval
        }
        
        # Channel variables
        self.channel_vars = {f'CH{i}': tk.BooleanVar() for i in range(1, 4)}
        self.plot_configurations = {}
        self.metrics = ['Voltage', 'Current', 'Resistance', 'Power']
        
        # Metric to key mapping
        self.metric_keys = {
            'Voltage': 'V',
            'Current': 'I',
            'Resistance': 'R',
            'Power': 'P'
        }
        
        # Metric colors and ylabels
        self.metric_properties = {
            'Voltage': {'color': 'blue', 'ylabel': 'Voltage (V)'},
            'Current': {'color': 'red', 'ylabel': 'Current (A)'},
            'Resistance': {'color': 'green', 'ylabel': 'Resistance (Ω)'},
            'Power': {'color': 'purple', 'ylabel': 'Power (W)'}
        }
        
        # Data buffers
        self.data_buffer = {f'CH{i}': {} for i in range(1, 4)}
        self.MAX_POINTS = 200  # Reduced points for performance
        
        # Plot windows storage
        self.plot_windows = {}
        
        # Animation reference
        self.anim = None
        
        # Last data point time for x-axis reference
        self.start_time = None
        
        # Setup UI
        self.setup_ui()
        
        # Set close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.close)
    
    def setup_ui(self):
        # Port frame
        port_frame = ttk.LabelFrame(self.root, text=" 🔌 Serial Port ", padding=(10, 5))
        port_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        # Port combobox
        ttk.Label(port_frame, text="Port:").grid(row=0, column=0)
        self.port_combo = ttk.Combobox(port_frame, values=self.get_available_ports(), state="readonly")
        self.port_combo.grid(row=0, column=1, padx=5)
        
        # Control buttons
        ttk.Button(port_frame, text="🔍 Refresh", command=self.refresh_ports).grid(row=0, column=2)
        self.connect_button = ttk.Button(port_frame, text="🚀 Connect", command=self.connect_serial)
        self.connect_button.grid(row=0, column=3)
        
        # Add Disconnect button
        self.disconnect_button = ttk.Button(port_frame, text="🔌 Disconnect", command=self.disconnect_serial, state="disabled")
        self.disconnect_button.grid(row=0, column=4)
        
        # Channel configuration frame
        channel_frame = ttk.LabelFrame(self.root, text=" 🖥️ Channel Configuration ", padding=(10, 5))
        channel_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Channels and metrics
        for idx, (ch_name, ch_var) in enumerate(self.channel_vars.items()):
            ttk.Checkbutton(
                channel_frame, 
                text=ch_name, 
                variable=ch_var, 
                command=lambda ch=ch_name: self.toggle_channel_config(ch)
            ).grid(row=idx, column=0, sticky='w')
            
            # Metric settings for each channel
            self.plot_configurations[ch_name] = {
                metric: tk.BooleanVar(value=False) for metric in self.metrics
            }
            
            for j, metric in enumerate(self.metrics):
                ttk.Checkbutton(
                    channel_frame, 
                    text=metric, 
                    variable=self.plot_configurations[ch_name][metric]
                ).grid(row=idx, column=j+1, sticky='w')
            
            # Channel configuration frame
            config_frame = ttk.LabelFrame(channel_frame, text=f"{ch_name} Settings", padding=5)
            config_frame.grid(row=idx+3, column=0, columnspan=4, sticky='ew')
            
            ttk.Label(config_frame, text="Method:").grid(row=0, column=0)
            method_var = tk.StringVar()
            method_combo = ttk.Combobox(
                config_frame, 
                values=['R', 'I', 'P'], 
                textvariable=method_var, 
                state="readonly",
                width=5
            )
            method_combo.grid(row=0, column=1)
            
            ttk.Label(config_frame, text="Value:").grid(row=0, column=2)
            value_entry = ttk.Entry(config_frame, width=10)
            value_entry.grid(row=0, column=3)
            
            ttk.Button(
                config_frame, 
                text="Send", 
                command=lambda ch=ch_name, m=method_var, v=value_entry: self.send_channel_config(ch, m, v)
            ).grid(row=0, column=4)
        
        # Plot control frame
        plot_control_frame = ttk.LabelFrame(self.root, text=" 📊 Plot Controls ", padding=(10, 5))
        plot_control_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        
        controls = [
            ("Auto Scale", self.plot_settings['auto_scale']),
            ("Show Grid", self.plot_settings['grid_enabled']),
            ("Show Legend", self.plot_settings['legend_enabled'])
        ]
        
        for i, (label, var) in enumerate(controls):
            ttk.Checkbutton(
                plot_control_frame, 
                text=label, 
                variable=var
            ).grid(row=i, column=0, sticky='w')
        
        ttk.Label(plot_control_frame, text="Update Interval (ms):").grid(row=len(controls), column=0)
        ttk.Scale(
            plot_control_frame, 
            from_=10, 
            to=200, 
            variable=self.plot_settings['update_interval']
        ).grid(row=len(controls)+1, column=0, sticky='ew')
        
        # Add plot button
        ttk.Button(
            plot_control_frame,
            text="Start Plotting",
            command=self.start_plotting
        ).grid(row=len(controls)+2, column=0, sticky='ew', pady=10)
    
    def get_available_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]
    
    def refresh_ports(self):
        ports = self.get_available_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
    
    def connect_serial(self):
        port = self.port_combo.get()
        if not port:
            messagebox.showerror("Error", "No port selected!")
            return
        
        try:
            self.serial_connection = SerialCommunicationHandler(port)
            messagebox.showinfo("Success", f"Connected to {port}")
            # Initialize the start time when connecting
            self.start_time = time.time()
            # Update button states
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            self.connection_status = True
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
    
    def disconnect_serial(self):
        if self.serial_connection:
            try:
                # Stop animation if running
                if self.anim:
                    self.anim.event_source.stop()
                
                # Close all plot windows
                for channel_data in list(self.plot_windows.values()):
                    plt.close(channel_data['figure'])
                    channel_data['window'].destroy()
                self.plot_windows.clear()
                
                # Close the serial connection
                self.serial_connection.close()
                self.serial_connection = None
                
                # Update button states
                self.connect_button.config(state="normal")
                self.disconnect_button.config(state="disabled")
                self.connection_status = False
                
                messagebox.showinfo("Success", "Serial connection closed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to disconnect: {e}")
    
    def send_channel_config(self, channel, method_var, value_entry):
        if not self.serial_connection:
            messagebox.showwarning("Warning", "Connect to a serial port first!")
            return
        
        method = method_var.get()
        value = value_entry.get()
        
        if not method or not value:
            messagebox.showwarning("Warning", "Fill all fields!")
            return
        
        try:
            success = self.serial_connection.send_channel_config(channel, method, float(value))
            if success:
                messagebox.showinfo("Success", f"{channel} configuration sent successfully!")
            else:
                messagebox.showerror("Error", "Failed to send configuration")
        except ValueError:
            messagebox.showerror("Error", "Invalid value!")
    
    def toggle_channel_config(self, channel):
        # Can implement logic to show/hide channel settings
        pass
    
    def start_plotting(self):
        # Close all previous plot windows
        for channel_data in list(self.plot_windows.values()):
            plt.close(channel_data['figure'])
        self.plot_windows.clear()
        
        # Stop any existing animation
        if self.anim:
            self.anim.event_source.stop()
        
        if not self.serial_connection:
            messagebox.showwarning("Warning", "Connect to a serial port first!")
            return
        
        # Reset start time reference
        if self.start_time is None:
            self.start_time = time.time()
        
        # Find active channels
        active_channels = []
        for ch, ch_var in self.channel_vars.items():
            if ch_var.get():
                if any(var.get() for var in self.plot_configurations[ch].values()):
                    active_channels.append(ch)
        
        if not active_channels:
            messagebox.showwarning("Warning", "Select at least one channel and metric!")
            return
        
        # Create separate windows for each channel
        for channel in active_channels:
            active_metrics = [
                metric for metric, var in self.plot_configurations[channel].items() 
                if var.get()
            ]
            
            if not active_metrics:
                continue
            
            # Create new window for each channel
            plot_window = tk.Toplevel(self.root)
            plot_window.title(f"{channel} Metrics")
            plot_window.geometry("900x700")  # Larger window for multiple plots
            
            # Calculate the grid layout - try to make it as square as possible
            num_metrics = len(active_metrics)
            num_rows = int(np.ceil(np.sqrt(num_metrics)))
            num_cols = int(np.ceil(num_metrics / num_rows))
            
            # Create figure with subplots
            fig = plt.figure(figsize=(12, 8), dpi=100)
            axes = {}
            lines = {}
            
            # Create a subplot for each metric
            for i, metric in enumerate(active_metrics):
                row = i // num_cols
                col = i % num_cols
                
                # Create subplot and store reference
                ax = fig.add_subplot(num_rows, num_cols, i + 1)
                metric_key = self.metric_keys[metric]
                axes[metric_key] = ax
                
                # Set title and labels
                ax.set_title(f"{metric}")
                ax.set_xlabel('Time (s)')
                ax.set_ylabel(self.metric_properties[metric]['ylabel'])
                
                # Create line with appropriate color
                line, = ax.plot([], [], 
                                color=self.metric_properties[metric]['color'],
                                label=metric)
                lines[metric_key] = line
                
                # Apply grid setting
                ax.grid(self.plot_settings['grid_enabled'].get())
            
            # Adjust layout to prevent overlap
            fig.tight_layout(pad=3.0)
            
            # Add the figure to plot window
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add toolbar
            toolbar = NavigationToolbar2Tk(canvas, plot_window)
            toolbar.update()
            
            # Attach close handler
            plot_window.protocol("WM_DELETE_WINDOW", lambda w=plot_window, f=fig: self.on_plot_window_close(w, f))
            
            # Initialize data buffers for this channel
            for metric in active_metrics:
                metric_key = self.metric_keys[metric]
                
                if metric_key not in self.data_buffer[channel]:
                    self.data_buffer[channel][metric_key] = {
                        'x': [],
                        'y': []
                    }
            
            # Store plot window information
            self.plot_windows[channel] = {
                'window': plot_window,
                'figure': fig,
                'axes': axes,
                'lines': lines,
                'canvas': canvas
            }
            
            # Draw and flush canvas
            fig.canvas.draw()
            fig.canvas.flush_events()
        
        # Start animation
        self.start_animation()
    
    def start_animation(self):
        # Configure plot updating with proper interval
        interval = self.plot_settings['update_interval'].get()
        
        # Create a figure manager to handle all plots
        # We'll use the first figure as the animation's figure
        if self.plot_windows:
            first_channel = list(self.plot_windows.keys())[0]
            fig = self.plot_windows[first_channel]['figure']
            
            # Start animation
            self.anim = animation.FuncAnimation(
                fig, 
                self.update_plot, 
                interval=interval,
                cache_frame_data=False  # Memory optimization
            )
            
            # Update all canvases
            for channel_data in self.plot_windows.values():
                channel_data['canvas'].draw()
    
    def update_plot(self, frame):
        if not self.serial_connection:
            return []
        
        # Get data from serial connection
        data = self.serial_connection.get_data()
        
        if not data or not data.get('time'):
            return []
        
        # Use relative time to make x-axis more readable
        if self.start_time is None:
            self.start_time = data['time']
        
        relative_time = data['time'] - self.start_time
        
        # Update each active channel with the current data
        lines_updated = []
        
        for channel, channel_data in list(self.plot_windows.items()):
            for metric_key, line in channel_data['lines'].items():
                if metric_key not in data:
                    continue
                
                # Update data buffer for this metric
                buffer = self.data_buffer[channel][metric_key]
                buffer['x'].append(relative_time)
                buffer['y'].append(data[metric_key])
                
                # Limit data points for performance
                if len(buffer['x']) > self.MAX_POINTS:
                    buffer['x'] = buffer['x'][-self.MAX_POINTS:]
                    buffer['y'] = buffer['y'][-self.MAX_POINTS:]
                
                # Update line data
                line.set_data(buffer['x'], buffer['y'])
                lines_updated.append(line)
                
                # Get the axes for this metric and update its range
                ax = channel_data['axes'][metric_key]
                
                # Update x-axis range
                ax.set_xlim(min(buffer['x']) if buffer['x'] else 0, 
                            max(buffer['x']) if buffer['x'] else 10)
                
                # Update y-axis range if auto-scale is enabled
                if self.plot_settings['auto_scale'].get():
                    if buffer['y']:
                        min_y = min(buffer['y'])
                        max_y = max(buffer['y'])
                        y_range = max(0.1, max_y - min_y)
                        ax.set_ylim(min_y - 0.1 * y_range, max_y + 0.1 * y_range)
                
                # Update grid based on settings
                ax.grid(self.plot_settings['grid_enabled'].get())
            
            # Redraw canvas
            try:
                channel_data['canvas'].draw_idle()  # More efficient than full draw
            except Exception as e:
                print(f"Plot update error: {e}")
        
        return lines_updated
    
    def on_plot_window_close(self, window, figure):
        # Close window and release resources
        plt.close(figure)
        window.destroy()
        
        # Remove from plot windows dictionary
        for channel, data in list(self.plot_windows.items()):
            if data['window'] == window:
                del self.plot_windows[channel]
                break
        
        # Stop animation if no plot windows remain
        if self.anim and self.anim.event_source:
            self.anim.event_source.stop()
    
    def close(self):
        # Close serial connection if it exists
        if self.serial_connection:
            try:
                self.serial_connection.close()
                print("Serial port closed successfully")
            except Exception as e:
                print(f"Error closing serial port: {e}")
        
        # Stop animation if it's running
        if self.anim:
            self.anim.event_source.stop()
        
        # Close all plot windows
        for channel_data in list(self.plot_windows.values()):
            try:
                plt.close(channel_data['figure'])
                channel_data['window'].destroy()
            except Exception as e:
                print(f"Error closing plot window: {e}")
        
        # Destroy the main window
        self.root.destroy()

def main():
    root = tbs.Window(themename="superhero")
    app = AdvancedSerialMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
>>>>>>> f17dcd9 (complete project?)
