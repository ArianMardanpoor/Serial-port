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

class Logger:
    def __init__(self):
        self.log_file = None
        self.is_logging = False
    
    def start_logging(self, file_path=None):
        if file_path is None:
            # Create a default log filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            file_path = os.path.join(log_dir, f"serial_data_{timestamp}.txt")
        
        try:
            self.log_file = open(file_path, 'w')
            self.log_file.write("Timestamp,Channel,Metric,Value\n")  # CSV header
            self.is_logging = True
            return True, file_path
        except Exception as e:
            return False, str(e)
    
    def log_data_point(self, timestamp, channel, metric, value):
        if self.is_logging and self.log_file:
            try:
                self.log_file.write(f"{timestamp},{channel},{metric},{value}\n")
                self.log_file.flush()  # Ensure data is written immediately
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
    def create_notification(self):
        try:
            if self.ser.in_waiting > 0:
                str_line = self.ser.readline().decode('utf-8', errors="ignore").strip()
                if not str_line:
                    return {}
            else:
                return {}
            if str_line[8]:
                messagebox.INFO("Channel 1 is working...")
            if str_line[18]:
                messagebox.INFO("Channel 2 is working...")
            if str_line[8]:
                messagebox.INFO("Channel 3 is working...")
            if str_line[33]:
                messagebox.WARNING("Temperture is too high....")
        except:
            pass
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
        try:
            self.root.iconbitmap("serial_port.ico")
        except:
            pass
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
            'Voltage': {'color': 'blue', 'ylabel': 'Voltage (V)'},
            'Current': {'color': 'red', 'ylabel': 'Current (A)'},
            'Resistance': {'color': 'green', 'ylabel': 'Resistance (Ω)'},
            'Power': {'color': 'purple', 'ylabel': 'Power (W)'}
        }
        self.data_buffer = {f'CH{i}': {} for i in range(1, 4)}
        self.MAX_POINTS = 200 
        self.plot_windows = {}
        self.anim = None
        self.start_time = None
        
        # New attributes for enhanced functionality
        self.logger = Logger()
        self.is_plotting_paused = False
        self.buffered_data = []
        
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
    
    def setup_ui(self):
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
        
        # Add buttons for control
        button_frame = ttk.Frame(plot_control_frame)
        button_frame.grid(row=len(controls)+3, column=0, sticky='ew', pady=5)
        
        ttk.Button(
            button_frame,
            text="Start Plotting",
            command=self.start_plotting
        ).grid(row=0, column=0, sticky='ew', padx=2)
        
        # Add Stop/Pause button
        self.pause_button = ttk.Button(
            button_frame,
            text="⏸️ Pause",
            command=self.pause_plotting,
            state="disabled"
        )
        self.pause_button.grid(row=0, column=1, sticky='ew', padx=2)
        
        # Add Continue/Resume button
        self.resume_button = ttk.Button(
            button_frame,
            text="▶️ Resume",
            command=self.resume_plotting,
            state="disabled"
        )
        self.resume_button.grid(row=0, column=2, sticky='ew', padx=2)
    
    def toggle_logging(self):
        if not self.logger.is_logging:
            # Start logging
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
            # Stop logging
            self.logger.close()
            self.logging_button.config(text="📝 Start Logging")
            messagebox.showinfo("Logging Stopped", "Data logging has been stopped")
    
    def pause_plotting(self):
        if self.anim and not self.is_plotting_paused:
            self.anim.event_source.stop()
            self.is_plotting_paused = True
            self.pause_button.config(state="disabled")
            self.resume_button.config(state="normal")
            
            # Create an empty buffer for collecting data while paused
            self.buffered_data = []
    
    def resume_plotting(self):
        if self.is_plotting_paused:
            # Process any buffered data first
            # Here we'll just restart the animation as we'll handle the buffered data in update_plot
            self.is_plotting_paused = False
            
            # Restart animation
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
                
                # Close the logger if it's open
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
            success = self.serial_connection.send_channel_config("<",":",channel,":", method,":", float(value),":",">")
            if success:
                messagebox.showinfo("Success", f"{channel} configuration sent successfully!")
            else:
                messagebox.showerror("Error", "Failed to send configuration")
        except ValueError:
            messagebox.showerror("Error", "Invalid value!")
    
    def toggle_channel_config(self, channel):
        pass
    
    def start_plotting(self):
        for channel_data in list(self.plot_windows.values()):
            plt.close(channel_data['figure'])
        self.plot_windows.clear()
        
        if self.anim:
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
        
        # Reset pause/resume buttons
        self.pause_button.config(state="normal")
        self.resume_button.config(state="disabled")
        self.is_plotting_paused = False
        self.buffered_data = []

        self.start_animation()
    
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
        
        # Always get data whether plotting is paused or not
        data = self.serial_connection.get_data()
        
        if not data or not data.get('time'):
            return []
        
        if self.start_time is None:
            self.start_time = data['time']
        
        relative_time = data['time'] - self.start_time
        
        # Log data to file if logging is enabled
        if self.logger.is_logging and data:
            for metric_key in ['V', 'I', 'R', 'P']:
                if metric_key in data:
                    # Find which channels are active
                    for channel in self.channel_vars.keys():
                        if self.channel_vars[channel].get():
                            # Check if this metric is being plotted for this channel
                            metric_name = next((m for m, k in self.metric_keys.items() if k == metric_key), None)
                            if metric_name and channel in self.plot_configurations:
                                if metric_name in self.plot_configurations[channel] and self.plot_configurations[channel][metric_name].get():
                                    self.logger.log_data_point(relative_time, channel, metric_key, data[metric_key])
        
        # If plotting is paused, store the data but don't update plots
        if self.is_plotting_paused:
            # Store the data for later when we resume
            self.buffered_data.append((relative_time, data))
            return []
        
        lines_updated = []
        
        # Process any buffered data first if we just resumed
        if self.buffered_data:
            for buffered_time, buffered_data in self.buffered_data:
                self.update_data_buffers(buffered_time, buffered_data)
            self.buffered_data = []  # Clear the buffer
        
        # Update with current data
        self.update_data_buffers(relative_time, data)
        
        # Update plot lines
        for channel, channel_data in list(self.plot_windows.items()):
            for metric_key, line in channel_data['lines'].items():
                if metric_key in data and channel in self.data_buffer and metric_key in self.data_buffer[channel]:
                    buffer = self.data_buffer[channel][metric_key]
                    line.set_data(buffer['x'], buffer['y'])
                    lines_updated.append(line)
                    
                    ax = channel_data['axes'][metric_key]
                    
                    x_min = min(buffer['x']) if buffer['x'] else 0
                    x_max = max(buffer['x']) if buffer['x'] else 1
                    if x_min == x_max:
                        x_max += 1
                    ax.set_xlim(x_min, x_max)
                    
                    if self.plot_settings['auto_scale'].get():
                        if buffer['y']:
                            min_y = min(buffer['y'])
                            max_y = max(buffer['y'])
                            y_range = max(0.1, max_y - min_y)
                            ax.set_ylim(min_y - 0.1 * y_range, max_y + 0.1 * y_range)
                    
                    ax.grid(self.plot_settings['grid_enabled'].get())
            
            try:
                channel_data['canvas'].draw_idle()
            except Exception as e:
                print(f"Plot update error: {e}")
        
        return lines_updated
    
    def update_data_buffers(self, relative_time, data):
        """Update data buffers for all active channels and metrics"""
        for channel, channel_data in list(self.plot_windows.items()):
            for metric_key in channel_data['lines'].keys():
                if metric_key in data:
                    buffer = self.data_buffer[channel][metric_key]
                    buffer['x'].append(relative_time)
                    buffer['y'].append(data[metric_key])
                    
                    if len(buffer['x']) > self.MAX_POINTS:
                        buffer['x'] = buffer['x'][-self.MAX_POINTS:]
                        buffer['y'] = buffer['y'][-self.MAX_POINTS:]
    
    def on_plot_window_close(self, window, figure):
        plt.close(figure)
        window.destroy()
        

        for channel, data in list(self.plot_windows.items()):
            if data['window'] == window:
                del self.plot_windows[channel]
                break
        

        if self.anim is not None and self.anim.event_source is not None:
            self.anim.event_source.stop()
        
        # Disable pause/resume buttons if no plot windows remain
        if not self.plot_windows:
            self.pause_button.config(state="disabled")
            self.resume_button.config(state="disabled")
    
    def close(self):
        # Close the logger if it's active
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
        

        self.root.destroy()

def main():
    root = tbs.Window(themename="superhero")
    app = AdvancedSerialMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()