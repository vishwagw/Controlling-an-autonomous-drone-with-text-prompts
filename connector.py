# adding a new feature to connect a drone via drone control system
import tkinter as tk
import threading
import time
import math
import serial
import serial.tools.list_ports
import json
import struct
from tkinter import scrolledtext, messagebox, Canvas, ttk

class DroneConnection:
    """Class to handle communication with a physical drone via USB"""
    def __init__(self):
        self.serial_port = None
        self.connected = False
        self.available_ports = []
        self.baudrate = 115200  # Default baudrate
        self.connection_thread = None
        self.stop_thread = False
        self.last_command_time = 0
        self.command_interval = 0.05  # Minimum seconds between commands
        self.command_queue = []
        self.telemetry = {
            "altitude": 0,
            "x_position": 0,
            "y_position": 0,
            "battery": 100,
            "attitude": {"roll": 0, "pitch": 0, "yaw": 0}
        }
    
    def scan_ports(self):
        """Scan for available serial ports"""
        self.available_ports = [port.device for port in serial.tools.list_ports.comports()]
        return self.available_ports
    
    def connect(self, port, baudrate=115200):
        """Connect to the specified serial port"""
        try:
            if self.connected:
                self.disconnect()
                
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            self.baudrate = baudrate
            self.connected = True
            self.stop_thread = False
            
            # Start the communication thread
            self.connection_thread = threading.Thread(target=self._communication_loop)
            self.connection_thread.daemon = True
            self.connection_thread.start()
            
            # Send connection status request
            self.send_command({"type": "status_request"})
            
            return True, "Connected to drone on " + port
        except serial.SerialException as e:
            return False, f"Error connecting to port {port}: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def disconnect(self):
        """Disconnect from the serial port"""
        if self.connected:
            self.stop_thread = True
            # Wait for the thread to finish
            if self.connection_thread and self.connection_thread.is_alive():
                self.connection_thread.join(timeout=1.0)
            
            if self.serial_port:
                try:
                    self.serial_port.close()
                except:
                    pass
                
            self.connected = False
            return True, "Disconnected from drone"
        return False, "Not connected"
    
    def _communication_loop(self):
        """Background thread to handle serial communication"""
        while not self.stop_thread:
            try:
                # Check if there are commands to send
                if self.command_queue and time.time() - self.last_command_time >= self.command_interval:
                    command = self.command_queue.pop(0)
                    self._send_raw_command(command)
                    self.last_command_time = time.time()
                
                # Check if there's data to read
                if self.serial_port and self.serial_port.in_waiting > 0:
                    data = self._read_response()
                    if data:
                        self._process_response(data)
                        
                time.sleep(0.01)  # Small delay to prevent CPU hogging
            except Exception as e:
                print(f"Communication error: {str(e)}")
                time.sleep(0.1)
    
    def _send_raw_command(self, command):
        """Send a raw command to the drone"""
        if not self.connected or not self.serial_port:
            return False
        
        try:
            # Convert command to JSON and add newline
            command_str = json.dumps(command) + "\n"
            self.serial_port.write(command_str.encode('utf-8'))
            self.serial_port.flush()
            return True
        except Exception as e:
            print(f"Error sending command: {str(e)}")
            return False
    
    def send_command(self, command):
        """Add a command to the sending queue"""
        self.command_queue.append(command)
    
    def _read_response(self):
        """Read response from the drone"""
        if not self.connected or not self.serial_port:
            return None
        
        try:
            # Read a line (assuming JSON responses end with newline)
            response = self.serial_port.readline().decode('utf-8').strip()
            if response:
                return response
        except Exception as e:
            print(f"Error reading response: {str(e)}")
        
        return None
    
    def _process_response(self, data):
        """Process a response from the drone"""
        try:
            # Parse JSON response
            response = json.loads(data)
            
            # Update telemetry if it's a telemetry response
            if response.get("type") == "telemetry":
                self.telemetry.update(response.get("data", {}))
        except json.JSONDecodeError:
            print(f"Invalid JSON response: {data}")
        except Exception as e:
            print(f"Error processing response: {str(e)}")
    
    def get_telemetry(self):
        """Get the latest telemetry data"""
        return self.telemetry
    
    def take_off(self, target_altitude=10):
        """Command the drone to take off"""
        command = {
            "type": "command",
            "action": "takeoff",
            "altitude": target_altitude
        }
        self.send_command(command)
    
    def land(self):
        """Command the drone to land"""
        command = {
            "type": "command",
            "action": "land"
        }
        self.send_command(command)
    
    def move(self, direction, speed):
        """Command the drone to move in a direction"""
        # Map direction to velocity components
        vx, vy = 0, 0
        if direction == "forward":
            vx = speed
        elif direction == "backward":
            vx = -speed
        elif direction == "left":
            vy = -speed
        elif direction == "right":
            vy = speed
            
        command = {
            "type": "command",
            "action": "move",
            "velocity": {
                "vx": vx,
                "vy": vy
            }
        }
        self.send_command(command)
    
    def change_altitude(self, target_altitude):
        """Command the drone to change altitude"""
        command = {
            "type": "command",
            "action": "altitude",
            "target": target_altitude
        }
        self.send_command(command)
    
    def stop(self):
        """Command the drone to stop moving"""
        command = {
            "type": "command",
            "action": "stop"
        }
        self.send_command(command)


class DroneSimulator:
    def __init__(self):
        self.altitude = 0
        self.is_flying = False
        self.default_altitude = 10  # meters
        self.max_altitude = 120  # meters
        self.ascent_rate = 1  # meters per second
        self.descent_rate = 0.7  # meters per second
        self.is_moving = False
        self.direction = None
        self.speed = 0  # meters per second
        self.x_position = 0  # relative x position
        self.y_position = 0  # relative y position
        self.battery = 100  # battery percentage
        self.attitude = {"roll": 0, "pitch": 0, "yaw": 0}  # orientation
        
    def take_off(self):
        """Command the drone to take off to default altitude"""
        if not self.is_flying:
            self.is_flying = True
            return self._change_altitude(self.default_altitude)
        else:
            return "Drone is already flying!"
    
    def land(self):
        """Command the drone to land"""
        if self.is_flying:
            self.is_flying = False
            return self._change_altitude(0)
        else:
            return "Drone is already on the ground!"
    
    def ascend(self, target_altitude=None):
        """Command the drone to ascend"""
        if not self.is_flying:
            return "Drone needs to take off first!"
        
        if target_altitude is None:
            target_altitude = self.altitude + 5
        
        if target_altitude > self.max_altitude:
            target_altitude = self.max_altitude
            
        return self._change_altitude(target_altitude)
    
    def descend(self, target_altitude=None):
        """Command the drone to descend"""
        if not self.is_flying:
            return "Drone is not flying!"
        
        if target_altitude is None:
            target_altitude = max(0, self.altitude - 5)
            
        return self._change_altitude(target_altitude)
    
    def _change_altitude(self, target_altitude):
        """Simulate changing altitude with a progress report"""
        if target_altitude == self.altitude:
            return f"Already at {self.altitude}m altitude."
        
        start_altitude = self.altitude
        message = []
        
        if target_altitude > start_altitude:
            message.append(f"Ascending from {start_altitude}m to {target_altitude}m...")
            rate = self.ascent_rate
        else:
            message.append(f"Descending from {start_altitude}m to {target_altitude}m...")
            rate = self.descent_rate
        
        # Calculate time needed for altitude change
        time_needed = abs(target_altitude - start_altitude) / rate
        
        # This would be where we'd actually send commands to a real drone
        # For simulation, we'll just update the altitude
        self.altitude = target_altitude
        
        if target_altitude == 0:
            message.append(f"Landed safely after {time_needed:.1f} seconds.")
        else:
            message.append(f"Reached target altitude of {target_altitude}m in {time_needed:.1f} seconds.")
        
        return "\n".join(message)
    
    def move(self, direction, speed=5):
        """Command the drone to move in a specific direction"""
        if not self.is_flying:
            return "Drone needs to take off first!"
        
        self.direction = direction
        self.speed = speed
        self.is_moving = True
        
        # Update position for visualization
        if direction == "forward":
            self.y_position -= speed
            self.attitude["pitch"] = 10  # Pitch forward
        elif direction == "backward":
            self.y_position += speed
            self.attitude["pitch"] = -10  # Pitch backward
        elif direction == "left":
            self.x_position -= speed
            self.attitude["roll"] = -10  # Roll left
        elif direction == "right":
            self.x_position += speed
            self.attitude["roll"] = 10  # Roll right
        
        return f"Moving {direction} at {speed} m/s"
    
    def stop(self):
        """Command the drone to stop moving"""
        if not self.is_flying:
            return "Drone is not flying!"
        
        if not self.is_moving:
            return "Drone is already stationary!"
        
        self.is_moving = False
        previous_direction = self.direction
        self.direction = None
        self.speed = 0
        
        # Reset attitude
        self.attitude = {"roll": 0, "pitch": 0, "yaw": 0}
        
        return f"Stopped moving {previous_direction}"
    
    def update_from_telemetry(self, telemetry):
        """Update simulator state from telemetry data"""
        if "altitude" in telemetry:
            self.altitude = telemetry["altitude"]
            self.is_flying = self.altitude > 0
            
        if "x_position" in telemetry:
            self.x_position = telemetry["x_position"]
            
        if "y_position" in telemetry:
            self.y_position = telemetry["y_position"]
            
        if "battery" in telemetry:
            self.battery = telemetry["battery"]
        
        if "attitude" in telemetry:
            self.attitude.update(telemetry["attitude"])
    
    def get_status(self):
        """Get the current status of the drone"""
        status = []
        
        if self.is_flying:
            status.append(f"Status: Flying at {self.altitude}m altitude")
        else:
            status.append("Status: Landed")
            
        if self.is_moving and self.direction:
            status.append(f"Movement: {self.direction} at {self.speed} m/s")
        else:
            status.append("Movement: Stationary")
            
        status.append(f"Position: X={self.x_position}m, Y={self.y_position}m")
        status.append(f"Battery: {self.battery}%")
        status.append(f"Attitude: Roll={self.attitude['roll']}°, Pitch={self.attitude['pitch']}°, Yaw={self.attitude['yaw']}°")
            
        return "\n".join(status)


class DroneControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Drone Control System")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        self.drone = DroneSimulator()
        self.drone_connection = DroneConnection()
        self.command_history = []
        self.animation_speed = 50  # milliseconds between animation updates
        self.visualization_scale = 5  # pixels per meter
        self.using_real_drone = False
        
        self._setup_ui()
        self.start_animation()
        
    def _setup_ui(self):
        # Create main frames
        self.left_frame = tk.Frame(self.root, padx=10, pady=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = tk.Frame(self.root, padx=10, pady=10)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        # Left frame components (command input and output)
        self.command_frame = tk.Frame(self.left_frame, padx=5, pady=5)
        self.command_frame.pack(fill=tk.X)
        
        tk.Label(self.command_frame, text="Enter command:").pack(side=tk.LEFT)
        self.command_entry = tk.Entry(self.command_frame, width=30)
        self.command_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.command_entry.bind("<Return>", self.process_command)
        self.send_button = tk.Button(self.command_frame, text="Send", command=self.process_command)
        self.send_button.pack(side=tk.LEFT)
        
        # Connection frame
        self.connection_frame = tk.LabelFrame(self.left_frame, text="Drone Connection", padx=5, pady=5)
        self.connection_frame.pack(fill=tk.X)
        
        self.port_frame = tk.Frame(self.connection_frame)
        self.port_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(self.port_frame, text="Port:").pack(side=tk.LEFT, padx=5)
        self.port_combo = ttk.Combobox(self.port_frame, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.scan_button = tk.Button(self.port_frame, text="Scan Ports", command=self.scan_ports)
        self.scan_button.pack(side=tk.LEFT, padx=5)
        
        self.connect_button = tk.Button(self.port_frame, text="Connect", command=self.connect_drone)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        self.connection_status_var = tk.StringVar(value="Status: Disconnected")
        self.connection_status = tk.Label(self.connection_frame, textvariable=self.connection_status_var, fg="red")
        self.connection_status.pack(fill=tk.X, pady=5)
        
        # Output display
        self.output_frame = tk.LabelFrame(self.left_frame, text="Command Output", padx=5, pady=5)
        self.output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_display = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD)
        self.output_display.pack(fill=tk.BOTH, expand=True)
        self.output_display.config(state=tk.DISABLED)
        
        # Quick command buttons
        self.buttons_frame = tk.LabelFrame(self.left_frame, text="Quick Commands", padx=5, pady=5)
        self.buttons_frame.pack(fill=tk.X)
        
        # Row 1 of buttons
        self.btn_row1 = tk.Frame(self.buttons_frame)
        self.btn_row1.pack(fill=tk.X, pady=2)
        
        self.takeoff_button = tk.Button(self.btn_row1, text="Take Off", 
                                       command=lambda: self.execute_command("take off"))
        self.takeoff_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.land_button = tk.Button(self.btn_row1, text="Land", 
                                    command=lambda: self.execute_command("land"))
        self.land_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.status_button = tk.Button(self.btn_row1, text="Status", 
                                     command=lambda: self.execute_command("status"))
        self.status_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Row 2 of buttons
        self.btn_row2 = tk.Frame(self.buttons_frame)
        self.btn_row2.pack(fill=tk.X, pady=2)
        
        self.up_button = tk.Button(self.btn_row2, text="Ascend", 
                                  command=lambda: self.execute_command("ascend"))
        self.up_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.down_button = tk.Button(self.btn_row2, text="Descend", 
                                    command=lambda: self.execute_command("descend"))
        self.down_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.stop_button = tk.Button(self.btn_row2, text="Stop", 
                                    command=lambda: self.execute_command("stop"))
        self.stop_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Row 3 of buttons - Directional controls
        self.btn_row3 = tk.Frame(self.buttons_frame)
        self.btn_row3.pack(fill=tk.X, pady=2)
        
        self.forward_button = tk.Button(self.btn_row3, text="Forward", 
                                       command=lambda: self.execute_command("forward"))
        self.forward_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.backward_button = tk.Button(self.btn_row3, text="Backward", 
                                        command=lambda: self.execute_command("backward"))
        self.backward_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Row 4 of buttons
        self.btn_row4 = tk.Frame(self.buttons_frame)
        self.btn_row4.pack(fill=tk.X, pady=2)
        
        self.left_button = tk.Button(self.btn_row4, text="Left", 
                                    command=lambda: self.execute_command("left"))
        self.left_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.right_button = tk.Button(self.btn_row4, text="Right", 
                                     command=lambda: self.execute_command("right"))
        self.right_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.help_button = tk.Button(self.btn_row4, text="Help", 
                                   command=self.show_help)
        self.help_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Right frame components (visualization)
        self.viz_frame = tk.LabelFrame(self.right_frame, text="Drone Visualization", padx=5, pady=5)
        self.viz_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = Canvas(self.viz_frame, width=400, height=400, bg="sky blue")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create ground
        self.ground = self.canvas.create_rectangle(0, 380, 400, 400, fill="green")
        
        # Create drone object
        self.drone_size = 30
        self.drone_obj = self.create_drone(200, 350)
        
        # Altitude and position indicators
        self.status_frame = tk.Frame(self.right_frame, padx=5, pady=5)
        self.status_frame.pack(fill=tk.X)
        
        # Status indicators - first row
        self.status_row1 = tk.Frame(self.status_frame)
        self.status_row1.pack(fill=tk.X)
        
        self.altitude_var = tk.StringVar(value="Altitude: 0m")
        self.altitude_label = tk.Label(self.status_row1, textvariable=self.altitude_var, font=("Arial", 10, "bold"))
        self.altitude_label.pack(side=tk.LEFT, padx=10)
        
        self.position_var = tk.StringVar(value="Position: X=0m, Y=0m")
        self.position_label = tk.Label(self.status_row1, textvariable=self.position_var, font=("Arial", 10, "bold"))
        self.position_label.pack(side=tk.LEFT, padx=10)
        
        # Status indicators - second row
        self.status_row2 = tk.Frame(self.status_frame)
        self.status_row2.pack(fill=tk.X)
        
        self.direction_var = tk.StringVar(value="Direction: None")
        self.direction_label = tk.Label(self.status_row2, textvariable=self.direction_var, font=("Arial", 10, "bold"))
        self.direction_label.pack(side=tk.LEFT, padx=10)
        
        self.battery_var = tk.StringVar(value="Battery: 100%")
        self.battery_label = tk.Label(self.status_row2, textvariable=self.battery_var, font=("Arial", 10, "bold"))
        self.battery_label.pack(side=tk.LEFT, padx=10)
        
        # Perform initial port scan
        self.scan_ports()
        
        # Initial message
        self.update_output("Drone Control System initialized. Type 'help' for available commands.")
    
    def create_drone(self, x, y):
        # Create drone body
        body = self.canvas.create_oval(x-self.drone_size/2, y-self.drone_size/2, 
                                       x+self.drone_size/2, y+self.drone_size/2,
                                       fill="gray", outline="black", width=2)
        
        # Create propellers
        prop_size = self.drone_size/3
        prop1 = self.canvas.create_line(x-self.drone_size/2, y-self.drone_size/2, 
                                       x-self.drone_size/2-prop_size, y-self.drone_size/2-prop_size,
                                       width=3)
        prop2 = self.canvas.create_line(x+self.drone_size/2, y-self.drone_size/2, 
                                       x+self.drone_size/2+prop_size, y-self.drone_size/2-prop_size,
                                       width=3)
        prop3 = self.canvas.create_line(x-self.drone_size/2, y+self.drone_size/2, 
                                       x-self.drone_size/2-prop_size, y+self.drone_size/2+prop_size,
                                       width=3)
        prop4 = self.canvas.create_line(x+self.drone_size/2, y+self.drone_size/2, 
                                       x+self.drone_size/2+prop_size, y+self.drone_size/2+prop_size,
                                       width=3)
        
        # Add indicator for front direction
        indicator = self.canvas.create_polygon(
            x, y-self.drone_size/2-5,
            x-5, y-self.drone_size/2+5,
            x+5, y-self.drone_size/2+5,
            fill="red"
        )
        
        return [body, prop1, prop2, prop3, prop4, indicator]
    
    def update_output(self, message):
        self.output_display.config(state=tk.NORMAL)
        self.output_display.insert(tk.END, message + "\n\n")
        self.output_display.see(tk.END)
        self.output_display.config(state=tk.DISABLED)
    
    def scan_ports(self):
        """Scan for available serial ports"""
        ports = self.drone_connection.scan_ports()
        self.port_combo['values'] = ports
        
        if ports:
            self.port_combo.current(0)
            self.update_output(f"Found {len(ports)} serial ports: {', '.join(ports)}")
        else:
            self.update_output("No serial ports found")
    
    def connect_drone(self):
        """Connect or disconnect from the drone"""
        if self.drone_connection.connected:
            # Disconnect if already connected
            success, message = self.drone_connection.disconnect()
            if success:
                self.using_real_drone = False
                self.connection_status_var.set("Status: Disconnected")
                self.connection_status.config(fg="red")
                self.connect_button.config(text="Connect")
            self.update_output(message)
        else:
            # Connect to selected port
            port = self.port_combo.get()
            if not port:
                self.update_output("Please select a port first")
                return
                
            success, message = self.drone_connection.connect(port)
            if success:
                self.using_real_drone = True
                self.connection_status_var.set(f"Status: Connected to {port}")
                self.connection_status.config(fg="green")
                self.connect_button.config(text="Disconnect")
            self.update_output(message)
    
    def process_command(self, event=None):
        command = self.command_entry.get().strip().lower()
        if command:
            self.command_entry.delete(0, tk.END)
            self.update_output(f"> {command}")
            self.execute_command(command)
    
    def execute_command(self, command):
        # Add command to history
        self.command_history.append(command)
        
        # Process commands
        if command in ("help", "commands"):
            self.show_help()
        
        elif command in ("take off", "takeoff"):
            if self.using_real_drone:
                self.drone_connection.take_off()
                self.update_output("Command sent: Take off")
            else:
                response = self.drone.take_off()
                self.update_output(response)
        
        elif command == "land":
            if self.using_real_drone:
                self.drone_connection.land()
                self.update_output("Command sent: Land")
            else:
                response = self.drone.land()
                self.update_output(response)
        
        elif command in ("up", "ascend"):
            if self.using_real_drone:
                # Increase altitude by 5m
                current_alt = self.drone_connection.get_telemetry().get("altitude", 0)
                self.drone_connection.change_altitude(current_alt + 5)
                self.update_output(f"Command sent: Ascend to {current_alt + 5}m")
            else:
                response = self.drone.ascend()
                self.update_output(response)
        
        elif command in ("down", "descend"):
            if self.using_real_drone:
                # Decrease altitude by 5m
                current_alt = self.drone_connection.get_telemetry().get("altitude", 0)
                self.drone_connection.change_altitude(max(0, current_alt - 5))
                self.update_output(f"Command sent: Descend to {max(0, current_alt - 5)}m")
            else:
                response = self.drone.descend()
                self.update_output(response)
        
        elif command.startswith("ascend to "):
            try:
                altitude = float(command.split("to ")[1])
                if self.using_real_drone:
                    self.drone_connection.change_altitude(altitude)
                    self.update_output(f"Command sent: Ascend to {altitude}m")
                else:
                    response = self.drone.ascend(altitude)
                    self.update_output(response)
            except (ValueError, IndexError):
                self.update_output("Invalid altitude. Please specify a number.")
        
        elif command.startswith("descend to "):
            try:
                altitude = float(command.split("to ")[1])
                if self.using_real_drone:
                    self.drone_connection.change_altitude(altitude)
                    self.update_output(f"Command sent: Descend to {altitude}m")
                else:
                    response = self.drone.descend(altitude)
                    self.update_output(response)
            except (ValueError, IndexError):
                self.update_output("Invalid altitude. Please specify a number.")
        
        elif command in ("forward", "backward", "left", "right"):
            if self.using_real_drone:
                self.drone_connection.move(command, 5)  # Default speed 5 m/s
                self.update_output(f"Command sent: Move {command} at 5 m/s")
            else:
                response = self.drone.move