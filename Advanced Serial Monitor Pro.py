import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.animation as animation
import numpy as np  
import time
import ttkbootstrap as tbs
import os
from datetime import datetime
import gc
import queue
import traceback


class Logger:
    def __init__(self):
        self.log_file = None
        self.is_logging = False
    
    def start_logging(self, file_path=None):
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            file_path = os.path.join(log_dir, f"serial_data_{timestamp}.txt")
        
        try:
            self.log_file = open(file_path, 'w')
            self.log_file.write("Timestamp,Channel,Metric,Value\n")
            self.is_logging = True
            return True, file_path
        except Exception as e:
            return False, str(e)
    
    def log_data_point(self, timestamp, channel, metric, value):
        if self.is_logging and self.log_file:
            try:
                self.log_file.write(f"{timestamp},{channel},{metric},{value}\n")
                self.log_file.flush() 
            except Exception as e:
                print(f"Error writing to log: {e}")
    
    def close(self):
        if self.log_file:
            self.log_file.close()
            self.is_logging = False

class SerialCommunicationHandler:
    def __init__(self, port):
        self.ser = serial.Serial(port, 115200, timeout=1)
        self.last_read_time = time.time()
        self.read_interval = 0.05 
        self.buffer = bytearray()
    
    def send_channel_config(self, channel, method, value):
        try:
            channel_map = {'CH1': 1, 'CH2': 2, 'CH3': 3}
            method_map = {'I': 1, 'R': 2, 'P': 3}

            if channel not in channel_map or method not in method_map:
                print(f"[ERROR] Invalid channel or method: {channel}, {method}")
                return False

            try:
                value = float(value)
            except ValueError:
                print("[ERROR] Value is not a valid float")
                return False

            int_value = max(0, min(int(value), 65535))
            high_byte = (int_value >> 8) & 0xFF
            low_byte = int_value & 0xFF
            packet = bytearray([
                ord('<'),
                ord(':'),
                channel_map[channel],
                ord(':'),             
                method_map[method],  
                ord(':'),            
                high_byte,
                low_byte,
                ord(':'),
                ord('>')
            ])

            print(f"[DEBUG] Sending packet: {list(packet)}") 

            self.ser.write(packet)
            print(packet)
            return True

        except Exception as e:
            print(f"[ERROR] Exception during send: {e}")
            return False

    def get_data(self):
        try:
            if self.ser.in_waiting > 0:

                new_data = self.ser.read(self.ser.in_waiting)
                self.buffer.extend(new_data)
                

                result = None
                while True:
                    start = self.buffer.find(b'<:')
                    end = self.buffer.find(b':>', start)
                    
                    if start != -1 and end != -1 and end > start:
                        line_end = end + 2
                        raw_data = self.buffer[start:line_end]
                        self.buffer = self.buffer[line_end:] 
                        

                        str_line = raw_data.decode('utf-8', errors="ignore").strip()
  
                        if not str_line:
                            continue  
                        
                        elapsed_time = time.time()
                        result = {"time": elapsed_time}
                        for channel in ["CH1", "CH2", "CH3"]:
                            result[channel] = {
                                "V": 0,
                                "I": 0,
                                "R": 0,
                                "P": 0
                            }

                        G1 = 0
                        G2 = 0
                        G3 = 0

                        try:
                            if len(raw_data) > 3:
                                V1_val = raw_data[2] * 256 + raw_data[3]
                                result["CH1"]["V"] = V1_val
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH1 V: {e}")
                            
                        try:
                            if len(raw_data) > 6:
                                I1_val = raw_data[5] * 256 + raw_data[6]
                                result["CH1"]["I"] = I1_val
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH1 I: {e}")
                        
                        try:
                            if len(raw_data) > 10:
                                G1 = raw_data[9] * 256 + raw_data[10]
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH1 G: {e}")
                            G1 = 0
                            
                        if result["CH1"]["I"] != 0:
                            result["CH1"]["R"] = result["CH1"]["V"] / result["CH1"]["I"]
                        else:
                            result["CH1"]["R"] = 0
                        result["CH1"]["P"] = result["CH1"]["V"] * result["CH1"]["I"] *1000
                            
                        try:
                            if len(raw_data) > 8:
                                mode = raw_data[8]
                                if mode == 1:
                                    result["CH1"]["I"] = G1
                                elif mode == 2:
                                    result["CH1"]["R"] = G1
                                elif mode == 3:
                                    result["CH1"]["P"] = G1
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH1 mode: {e}")
                        
                        try:
                            if len(raw_data) > 13:
                                V2_val = raw_data[12] * 256 + raw_data[13]
                                result["CH2"]["V"] = V2_val
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH2 V: {e}")
                            
                        try:
                            if len(raw_data) > 16:
                                I2_val = raw_data[15] * 256 + raw_data[16]
                                result["CH2"]["I"] = I2_val
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH2 I: {e}")
                            
                        try:
                            if len(raw_data) > 20:
                                G2 = raw_data[19] * 256 + raw_data[20]
                        except (IndexError, TypeError, ZeroDivisionError) as e:
                            print(f"Error reading CH2 G: {e}")
                            G2 = 0

                        if result["CH2"]["I"] != 0:
                            result["CH2"]["R"] = result["CH2"]["V"] / result["CH2"]["I"]
                        else:
                            result["CH2"]["R"] = 0
                        result["CH2"]["P"] = result["CH2"]["V"] * result["CH2"]["I"] *1000
                            
                        try:
                            if len(raw_data) > 18:
                                mode = raw_data[18]
                                if mode == 1:
                                    result["CH2"]["I"] = G2
                                elif mode == 2:
                                    result["CH2"]["R"] = G2
                                elif mode == 3:
                                    result["CH2"]["P"] = G2
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH2 mode: {e}")
                        
                        try:
                            if len(raw_data) > 23:
                                V3_val = raw_data[22] * 256 + raw_data[23] 
                                result["CH3"]["V"] = V3_val
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH3 V: {e}")

                        try:
                            if len(raw_data) > 26:
                                I3_val = raw_data[25] * 256 + raw_data[26]
                                result["CH3"]["I"] = I3_val
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH3 I: {e}")
                            
                        try:
                            if len(raw_data) > 30:
                                G3 = raw_data[29] * 256 + raw_data[30]
                        except (IndexError, TypeError, ZeroDivisionError) as e:
                            print(f"Error reading CH3 G: {e}")
                            G3 = 0
                            
                        if result["CH3"]["I"] != 0:
                            result["CH3"]["R"] = result["CH3"]["V"] / result["CH3"]["I"]
                        else:
                            result["CH3"]["R"] = 0
                        result["CH3"]["P"] = result["CH3"]["V"] * result["CH3"]["I"] *1000
                            
                        try:
                            if len(raw_data) > 28:
                                mode = raw_data[28]
                                if mode == 1:
                                    result["CH3"]["I"] = G3
                                elif mode == 2:
                                    result["CH3"]["R"] = G3 
                                elif mode == 3:
                                    result["CH3"]["P"] = G3
                        except (IndexError, TypeError) as e:
                            print(f"Error reading CH3 mode: {e}")
                    else:
                        break
                        
                if len(self.buffer) > 1024:
                    self.buffer = self.buffer[-100:]
                
                return result if result else {}
            else:
                return {}
        except Exception as e:
            print(f"Error receiving data: {e}")
            return {}
    def create_notification(self):
        try:
            bytes_to_read = min(35, self.ser.in_waiting) 
            new_data = self.ser.read(bytes_to_read)
                
            temp_buffer = bytearray()
            temp_buffer.extend(new_data)
                
            if b'\n' in temp_buffer:
                line_end = temp_buffer.find(b'\n')
                str_line = temp_buffer[:line_end].decode('utf-8', errors="ignore").strip()
            
            if len(str_line) <= 34:
                return
                
            try:
                Flags = ord(str_line[34])
                Flagsbyte = format(Flags, '08b')
                

                if len(Flagsbyte) >= 8:
                    if Flagsbyte[0] == '1':
                        messagebox.showinfo("Error: Temperature exceeded 70°C.\
                                \nSystem shut down to prevent damage.\
                                \nPlease restart manually after cooling.")
                    
                    if Flagsbyte[1] == '1':
                        messagebox.showinfo("Error: Channel 1 current limit exceeded.\
                                \nMaximum allowed current is 1A.")
                    
                    if Flagsbyte[2] == '1':
                        messagebox.showinfo("Error: Channel 2 current limit exceeded.\
                                \nMaximum allowed current is 1A.")
                    
                    if Flagsbyte[3] == '1':
                        messagebox.showinfo("Error: Channel 3 current limit exceeded.\
                                \nMaximum allowed current is 1A.")
            except (IndexError, TypeError, ValueError) as e:
                print(f"Error processing flags: {e}")
                
        except Exception as e:
            print(f"Error in create_notification: {e}")

    def close(self):
        if self.ser.is_open:
            self.ser.close()

class AdvancedSerialMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Advanced Serial Monitor Pro")
        self.root.geometry("1000x600")
        self.data_queue = queue.Queue()
        self.running = False
        self.data_thread = None
        self.plotting_thread = None
        try:
            self.root.iconbitmap("serial_port.ico")
        except:
            pass
        self.MAX_POINTS = 200 
        self.data_buffer = {f'CH{i}': {} for i in range(1, 4)}
        self.cleanup_interval = 10000
        self.last_cleanup = time.time()
        self.FONT = ("Segoe UI", 11, "bold")
        self.serial_connection = None
        self.connection_status = False
        self.plot_settings = {
            'auto_scale': tk.BooleanVar(value=True),
            'grid_enabled': tk.BooleanVar(value=True),
            'legend_enabled': tk.BooleanVar(value=True),
            'update_interval': tk.IntVar(value=100)
        }
        self.channel_vars = {f'CH{i}': tk.BooleanVar() for i in range(1, 4)}
        self.plot_configurations = {}
        self.metrics = ['Voltage', 'Current', 'Resistance', 'Power']
        self.metric_keys = {
            'Voltage': 'V',
            'Current': 'I',
            'Resistance': 'R',
            'Power': 'P'
        }
        self.metric_properties = {
            'Voltage': {'color': 'blue', 'ylabel': 'Voltage (mV)'},
            'Current': {'color': 'red', 'ylabel': 'Current (mA)'},
            'Resistance': {'color': 'green', 'ylabel': 'Resistance (Ω)'},
            'Power': {'color': 'purple', 'ylabel': 'Power (mW)'}
        }
        self.data_buffer = {f'CH{i}': {} for i in range(1, 4)}
        self.MAX_POINTS = 200 
        self.plot_windows = {}
        self.anim = None
        self.start_time = None
        self.logger = Logger()
        self.is_plotting_paused = False
        self.buffered_data = []
        
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
    
    def setup_ui(self):
        plt.rcParams['figure.autolayout'] = False
        plt.rcParams['toolbar'] = 'None'  
        
        port_frame = ttk.LabelFrame(self.root, text=" 🔌 Serial Port ", padding=(10, 5))
        port_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        

        ttk.Label(port_frame, text="Port:").grid(row=0, column=0)
        self.port_combo = ttk.Combobox(port_frame, values=self.get_available_ports(), state="readonly")
        self.port_combo.grid(row=0, column=1, padx=5)
        

        ttk.Button(port_frame, text="🔍 Refresh", command=self.refresh_ports).grid(row=0, column=2)
        self.connect_button = ttk.Button(port_frame, text="🚀 Connect", command=self.connect_serial)
        self.connect_button.grid(row=0, column=3)
        

        self.disconnect_button = ttk.Button(port_frame, text="🔌 Disconnect", command=self.disconnect_serial, state="disabled")
        self.disconnect_button.grid(row=0, column=4)
        
        # Add logging button
        self.logging_button = ttk.Button(port_frame, text="📝 Start Logging", command=self.toggle_logging)
        self.logging_button.grid(row=0, column=5, padx=5)

        channel_frame = ttk.LabelFrame(self.root, text=" 🖥️ Channel Configuration ", padding=(10, 5))
        channel_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        

        for idx, (ch_name, ch_var) in enumerate(self.channel_vars.items()):
            ttk.Checkbutton(
                channel_frame, 
                text=ch_name, 
                variable=ch_var, 
                command=lambda ch=ch_name: self.toggle_channel_config(ch)
            ).grid(row=idx, column=0, sticky='w')
            

            self.plot_configurations[ch_name] = {
                metric: tk.BooleanVar(value=False) for metric in self.metrics
            }
            
            for j, metric in enumerate(self.metrics):
                ttk.Checkbutton(
                    channel_frame, 
                    text=metric, 
                    variable=self.plot_configurations[ch_name][metric]
                ).grid(row=idx, column=j+1, sticky='w')
            

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
        

        button_frame = ttk.Frame(plot_control_frame)
        button_frame.grid(row=len(controls)+3, column=0, sticky='ew', pady=5)
        
        ttk.Button(
            button_frame,
            text="Start Plotting",
            command=self.start_plotting
        ).grid(row=0, column=0, sticky='ew', padx=2)
        
        self.pause_button = ttk.Button(
            button_frame,
            text="⏸️ Pause",
            command=self.pause_plotting,
            state="disabled"
        )
        self.pause_button.grid(row=0, column=1, sticky='ew', padx=2)
        self.resume_button = ttk.Button(
            button_frame,
            text="▶️ Resume",
            command=self.resume_plotting,
            state="disabled"
        )
        self.resume_button.grid(row=0, column=2, sticky='ew', padx=2)
    
    def toggle_logging(self):
        if not self.logger.is_logging:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Select log file location"
            )
            
            if file_path:
                success, msg = self.logger.start_logging(file_path)
                if success:
                    self.logging_button.config(text="📝 Stop Logging")
                    messagebox.showinfo("Logging Started", f"Logging data to: {msg}")
                else:
                    messagebox.showerror("Logging Error", f"Failed to start logging: {msg}")
        else:
            self.logger.close()
            self.logging_button.config(text="📝 Start Logging")
            messagebox.showinfo("Logging Stopped", "Data logging has been stopped")
    
    def pause_plotting(self):
        if self.anim and not self.is_plotting_paused:
            self.anim.event_source.stop()
            self.is_plotting_paused = True
            self.pause_button.config(state="disabled")
            self.resume_button.config(state="normal")
            self.buffered_data = []
    
    def resume_plotting(self):
        if self.is_plotting_paused:
            self.is_plotting_paused = False
            
            interval = self.plot_settings['update_interval'].get()
            if self.plot_windows:
                first_channel = list(self.plot_windows.keys())[0]
                fig = self.plot_windows[first_channel]['figure']
                

                for channel_data in self.plot_windows.values():
                    channel_data['canvas'].draw_idle()
                
                self.anim = animation.FuncAnimation(
                    fig, 
                    self.update_plot, 
                    interval=interval,
                    blit=True,
                    cache_frame_data=False
                )
            
            self.pause_button.config(state="normal")
            self.resume_button.config(state="disabled")


    
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

            self.start_time = time.time()
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            self.connection_status = True
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
    
    def disconnect_serial(self):
        if self.serial_connection:
            try:
                if self.anim is not None and self.anim.event_source is not None:
                    self.anim.event_source.stop()

                for channel_data in list(self.plot_windows.values()):
                    if channel_data.get('figure'):
                        plt.close(channel_data['figure'])
                    if channel_data.get('window'):
                        channel_data['window'].destroy()
                self.plot_windows.clear()
                
                self.serial_connection.close()
                self.serial_connection = None
                
                if self.logger.is_logging:
                    self.logger.close()
                    self.logging_button.config(text="📝 Start Logging")
                
                self.connect_button.config(state="normal")
                self.disconnect_button.config(state="disabled")
                self.pause_button.config(state="disabled")
                self.resume_button.config(state="disabled")
                self.connection_status = False
                
                messagebox.showinfo("Success", "Serial connection closed")
            except Exception as e:
                print(f"Error while disconnecting serial: {e}")
    
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
        pass
    
    def start_plotting(self):
        interval = self.plot_settings['update_interval'].get()
        
        if self.plot_windows:
            first_channel = list(self.plot_windows.keys())[0]
            fig = self.plot_windows[first_channel]['figure']
            self.schedule_memory_cleanup()
            
            self.anim = animation.FuncAnimation(
                fig, 
                self.update_plot, 
                interval=interval,
                cache_frame_data=False  
            )
            
            for channel_data in self.plot_windows.values():
                channel_data['canvas'].draw()
        for channel_data in list(self.plot_windows.values()):
            plt.close(channel_data['figure'])
        self.plot_windows.clear()
        
        if self.anim is not None and self.anim.event_source is not None:
            self.anim.event_source.stop()
        
        if not self.serial_connection:
            messagebox.showwarning("Warning", "Connect to a serial port first!")
            return
        
        if self.start_time is None:
            self.start_time = time.time()
        
        active_channels = []
        for ch, ch_var in self.channel_vars.items():
            if ch_var.get():
                if any(var.get() for var in self.plot_configurations[ch].values()):
                    active_channels.append(ch)
        
        if not active_channels:
            messagebox.showwarning("Warning", "Select at least one channel and metric!")
            return
        
        for channel in active_channels:
            active_metrics = [
                metric for metric, var in self.plot_configurations[channel].items() 
                if var.get()
            ]
            
            if not active_metrics:
                continue
            
            plot_window = tk.Toplevel(self.root)
            plot_window.title(f"{channel} Metrics")
            plot_window.geometry("900x700")
            

            num_metrics = len(active_metrics)
            num_rows = int(np.ceil(np.sqrt(num_metrics)))
            num_cols = int(np.ceil(num_metrics / num_rows))
            

            fig = plt.figure(figsize=(12, 8), dpi=100)
            axes = {}
            lines = {}
            

            for i, metric in enumerate(active_metrics):
                row = i // num_cols
                col = i % num_cols
                

                ax = fig.add_subplot(num_rows, num_cols, i + 1)
                metric_key = self.metric_keys[metric]
                axes[metric_key] = ax
                
                ax.set_title(f"{metric}")
                ax.set_xlabel('Time (s)')
                ax.set_ylabel(self.metric_properties[metric]['ylabel'])
                

                line, = ax.plot([], [], 
                                color=self.metric_properties[metric]['color'],
                                label=metric)
                lines[metric_key] = line
                

                ax.grid(self.plot_settings['grid_enabled'].get())
            

            fig.tight_layout(pad=3.0)
            

            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            

            toolbar = NavigationToolbar2Tk(canvas, plot_window)
            toolbar.update()
            

            plot_window.protocol("WM_DELETE_WINDOW", lambda w=plot_window, f=fig: self.on_plot_window_close(w, f))
            

            for metric in active_metrics:
                metric_key = self.metric_keys[metric]
                
                if metric_key not in self.data_buffer[channel]:
                    self.data_buffer[channel][metric_key] = {
                        'x': [],
                        'y': []
                    }
            

            self.plot_windows[channel] = {
                'window': plot_window,
                'figure': fig,
                'axes': axes,
                'lines': lines,
                'canvas': canvas
            }
            

            fig.canvas.draw()
            fig.canvas.flush_events()
        
        self.pause_button.config(state="normal")
        self.resume_button.config(state="disabled")
        self.is_plotting_paused = False
        self.buffered_data = []

        self.start_animation()
    
    def schedule_memory_cleanup(self):
        self.root.after(self.cleanup_interval, self.perform_memory_cleanup)
    
    def perform_memory_cleanup(self):
        try:
            active_channels = [ch for ch, var in self.channel_vars.items() if var.get()]
            
            for channel in list(self.data_buffer.keys()):
                if channel not in active_channels:
                    self.data_buffer[channel] = {}
            

            for channel in active_channels:
                for metric_key in list(self.data_buffer.get(channel, {}).keys()):
                    buffer = self.data_buffer[channel][metric_key]
                    if len(buffer.get('x', [])) > self.MAX_POINTS:
                        buffer['x'] = buffer['x'][-self.MAX_POINTS//2:]
                        buffer['y'] = buffer['y'][-self.MAX_POINTS//2:]
        
            gc.collect()
            
            if self.plot_settings['auto_scale'].get():
                for channel_data in self.plot_windows.values():
                    for ax in channel_data['axes'].values():
                        ax.relim()
                        ax.autoscale_view()
            

            self.schedule_memory_cleanup()
            
        except Exception as e:
            print(f"Error during memory cleanup: {e}")
            self.schedule_memory_cleanup()
    def start_animation(self):
        interval = self.plot_settings['update_interval'].get()
        

        if self.plot_windows:
            first_channel = list(self.plot_windows.keys())[0]
            fig = self.plot_windows[first_channel]['figure']
            

            self.anim = animation.FuncAnimation(
                fig, 
                self.update_plot, 
                interval=interval,
                cache_frame_data=False  
            )
            

            for channel_data in self.plot_windows.values():
                channel_data['canvas'].draw()
    
    def update_plot(self, frame):
        if not self.serial_connection:
            return []

        data = {}
        if self.serial_connection.ser.in_waiting > 0:
            data = self.serial_connection.get_data()

        if not data or not data.get('time'):
            return []

        if self.start_time is None:
            self.start_time = data['time']

        relative_time = data['time'] - self.start_time

        if self.logger.is_logging:
            for ch in ["CH1", "CH2", "CH3"]:
                if ch in data:
                    for key in ['V', 'I', 'R', 'P']:
                        if self.channel_vars[ch].get():
                            metric_name = next((m for m, k in self.metric_keys.items() if k == key), None)
                            if metric_name and self.plot_configurations[ch][metric_name].get():
                                self.logger.log_data_point(relative_time, ch, key, data[ch][key])

        if self.is_plotting_paused:
            self.buffered_data.append((relative_time, data))
            return []

        if self.buffered_data:
            for t, d in self.buffered_data:
                self.update_data_buffers(t, d)
            self.buffered_data = []


        self.update_data_buffers(relative_time, data)

        updated_lines = []

        for channel, win in self.plot_windows.items():
            for metric_key, line in win['lines'].items():
                buf = self.data_buffer.get(channel, {}).get(metric_key, {'x': [], 'y': []})
                x_data, y_data = buf['x'], buf['y']
                line.set_data(x_data, y_data)
                updated_lines.append(line)

                if self.plot_settings['auto_scale'].get():
                    ax = win['axes'][metric_key]
                    ax.relim()
                    ax.autoscale_view()

                    if y_data:
                        ymax = max(y_data)
                        margin = 0.1 * ymax if ymax != 0 else 1.0
                        ax.set_ylim(0, ymax + margin)

        return updated_lines

        
    def update_data_buffers(self, relative_time, data):
        for channel, channel_data in list(self.plot_windows.items()):
            if channel in data:
                for metric_key in channel_data['lines'].keys():
                    if metric_key in data[channel]:

                        if channel not in self.data_buffer:
                            self.data_buffer[channel] = {}
                        
                        if metric_key not in self.data_buffer[channel]:
                            self.data_buffer[channel][metric_key] = {'x': [], 'y': []}
                        
                        buffer = self.data_buffer[channel][metric_key]
                        buffer['x'].append(relative_time)
                        buffer['y'].append(data[channel][metric_key])
                        
                        if len(buffer['x']) > self.MAX_POINTS:
                            buffer['x'] = buffer['x'][-self.MAX_POINTS:]
                            buffer['y'] = buffer['y'][-self.MAX_POINTS:]
    def on_plot_window_close(self, window, figure):
        plt.close(figure)
        window.destroy()

        for channel, data in list(self.plot_windows.items()):
            if data['window'] == window:
                del self.plot_windows[channel]
                if channel in self.data_buffer:
                    self.data_buffer[channel] = {}  
                break

        if self.anim is not None and self.anim.event_source is not None:
            self.anim.event_source.stop()

        if not self.plot_windows:
            self.pause_button.config(state="disabled")
            self.resume_button.config(state="disabled")

    
    def close(self):
        if self.logger.is_logging:
            self.logger.close()

        if self.serial_connection:
            try:
                self.serial_connection.close()
                print("Serial port closed successfully")
            except Exception as e:
                print(f"Error closing serial port: {e}")
        

        if hasattr(self, 'anim') and self.anim and self.anim.event_source is not None:
            self.anim.event_source.stop()
        
        for channel_data in list(self.plot_windows.values()):
            try:
                plt.close(channel_data['figure'])
                channel_data['window'].destroy()
            except Exception as e:
                print(f"Error closing plot window: {e}")
        

        self.data_buffer.clear()
        self.plot_windows.clear()
        
        import gc
        gc.collect()
        
        self.root.destroy()

def main():
    root = tbs.Window(themename="superhero")
    app = AdvancedSerialMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()