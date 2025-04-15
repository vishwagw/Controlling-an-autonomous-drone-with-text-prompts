# secind attempt is to build a more advanced promt-based controller:
# The controlle program has a better user interface included with animation effect and more robust button controller unit as well.
import tkinter as tk
import threading
import time
import math
from tkinter import scrolledtext, messagebox, Canvas

class DroneSimulator:
    # basic simulation data:
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

    # take off command:    
    def take_off(self):
        """Command the drone to take off to default altitude"""
        if not self.is_flying:
            self.is_flying = True
            return self._change_altitude(self.default_altitude)
        else:
            return "Drone is already flying!"
    
    # landing command:
    def land(self):
        """Command the drone to land"""
        if self.is_flying:
            self.is_flying = False
            return self._change_altitude(0)
        else:
            return "Drone is already on the ground!"
    
    # ascend command:
    def ascend(self, target_altitude=None):
        """Command the drone to ascend"""
        if not self.is_flying:
            return "Drone needs to take off first!"
        
        if target_altitude is None:
            target_altitude = self.altitude + 5
        
        if target_altitude > self.max_altitude:
            target_altitude = self.max_altitude
            
        return self._change_altitude(target_altitude)
    
    # descend command:
    def descend(self, target_altitude=None):
        """Command the drone to descend"""
        if not self.is_flying:
            return "Drone is not flying!"
        
        if target_altitude is None:
            target_altitude = max(0, self.altitude - 5)
            
        return self._change_altitude(target_altitude)
    
    # altitude changes:
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
    
    # control movements:
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
        elif direction == "backward":
            self.y_position += speed
        elif direction == "left":
            self.x_position -= speed
        elif direction == "right":
            self.x_position += speed
        
        return f"Moving {direction} at {speed} m/s"
    
    # stop the movement to make the drone in hover mode:
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
        
        return f"Stopped moving {previous_direction}"
    
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
            
        return "\n".join(status)

class DroneControlApp:
    # basic simulation data:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Drone Control System")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        self.drone = DroneSimulator()
        self.command_history = []
        self.animation_speed = 50  # milliseconds between animation updates
        self.visualization_scale = 5  # pixels per meter
        
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
        
        self.altitude_var = tk.StringVar(value="Altitude: 0m")
        self.altitude_label = tk.Label(self.status_frame, textvariable=self.altitude_var, font=("Arial", 10, "bold"))
        self.altitude_label.pack(side=tk.LEFT, padx=10)
        
        self.position_var = tk.StringVar(value="Position: X=0m, Y=0m")
        self.position_label = tk.Label(self.status_frame, textvariable=self.position_var, font=("Arial", 10, "bold"))
        self.position_label.pack(side=tk.LEFT, padx=10)
        
        self.direction_var = tk.StringVar(value="Direction: None")
        self.direction_label = tk.Label(self.status_frame, textvariable=self.direction_var, font=("Arial", 10, "bold"))
        self.direction_label.pack(side=tk.LEFT, padx=10)
        
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
        
        return [body, prop1, prop2, prop3, prop4]
    
    def update_output(self, message):
        self.output_display.config(state=tk.NORMAL)
        self.output_display.insert(tk.END, message + "\n\n")
        self.output_display.see(tk.END)
        self.output_display.config(state=tk.DISABLED)
    
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
            response = self.drone.take_off()
            self.update_output(response)
        
        elif command == "land":
            response = self.drone.land()
            self.update_output(response)
        
        elif command in ("up", "ascend"):
            response = self.drone.ascend()
            self.update_output(response)
        
        elif command in ("down", "descend"):
            response = self.drone.descend()
            self.update_output(response)
        
        elif command.startswith("ascend to "):
            try:
                altitude = float(command.split("to ")[1])
                response = self.drone.ascend(altitude)
                self.update_output(response)
            except (ValueError, IndexError):
                self.update_output("Invalid altitude. Please specify a number.")
        
        elif command.startswith("descend to "):
            try:
                altitude = float(command.split("to ")[1])
                response = self.drone.descend(altitude)
                self.update_output(response)
            except (ValueError, IndexError):
                self.update_output("Invalid altitude. Please specify a number.")
        
        elif command in ("forward", "backward", "left", "right"):
            response = self.drone.move(command)
            self.update_output(response)
        
        elif command.startswith(("go forward", "go backward", "go left", "go right")):
            parts = command.split()
            direction = parts[1]
            speed = 5  # default speed
            
            if len(parts) > 2 and parts[2] == "at" and len(parts) > 3:
                try:
                    speed = float(parts[3])
                except ValueError:
                    self.update_output("Invalid speed. Using default 5 m/s.")
            
            response = self.drone.move(direction, speed)
            self.update_output(response)
        
        elif command == "stop":
            response = self.drone.stop()
            self.update_output(response)
        
        elif command in ("status", "info"):
            response = self.drone.get_status()
            self.update_output(response)
        
        elif command == "reset":
            self.drone = DroneSimulator()
            self.update_output("Drone reset to initial position.")
        
        elif command in ("exit", "quit"):
            self.root.quit()
        
        else:
            self.update_output(f"Unknown command: '{command}'. Type 'help' for available commands.")
    
    def show_help(self):
        help_text = """
Available Commands:
- take off: Take off to default altitude
- land: Land the drone
- up/ascend: Go up 5 meters
- down/descend: Go down 5 meters
- ascend to [altitude]: Ascend to specific altitude
- descend to [altitude]: Descend to specific altitude
- forward, backward, left, right: Move in that direction
- go [direction] at [speed]: Move with specific speed
- stop: Stop moving
- status/info: Show drone status
- reset: Reset drone to initial position
- help/commands: Show this help
- exit/quit: Exit the program
        """
        self.update_output(help_text)
    
    def start_animation(self):
        """Start the animation loop for drone visualization"""
        self.animate()
    
    def animate(self):
        """Update drone visualization based on current state"""
        # Calculate canvas coordinates
        canvas_width = self.canvas.winfo_width() or 400
        canvas_height = self.canvas.winfo_height() or 400
        
        # Calculate drone position
        center_x = canvas_width / 2 + (self.drone.x_position * self.visualization_scale)
        
        # Limit x position to stay on canvas
        center_x = max(self.drone_size, min(canvas_width - self.drone_size, center_x))
        
        # Y position - lower value means higher in the sky (0 at top of canvas)
        ground_y = canvas_height - 20  # Ground level
        max_height_pixels = ground_y - 50  # Leave some space at the top
        
        # Calculate vertical position - reversed as higher altitude = lower y-coordinate
        altitude_ratio = self.drone.altitude / self.drone.max_altitude
        height_pixels = max(0, min(1, altitude_ratio)) * max_height_pixels
        center_y = ground_y - height_pixels
        
        # Move drone to new position
        # First calculate the current position
        bbox = self.canvas.bbox(self.drone_obj[0])
        if bbox:
            current_x = (bbox[0] + bbox[2]) / 2
            current_y = (bbox[1] + bbox[3]) / 2
            
            # Calculate movement
            dx = center_x - current_x
            dy = center_y - current_y
            
            # Move all drone parts
            for part in self.drone_obj:
                self.canvas.move(part, dx, dy)
        
        # Animate propellers if flying
        if self.drone.is_flying:
            # Rotate propellers by removing and redrawing
            for i in range(1, 5):
                self.canvas.delete(self.drone_obj[i])
            
            # Redraw propellers with animated rotation
            angle = time.time() * 10  # Rotation angle based on time
            bbox = self.canvas.bbox(self.drone_obj[0])
            if bbox:
                body_x = (bbox[0] + bbox[2]) / 2
                body_y = (bbox[1] + bbox[3]) / 2
                radius = self.drone_size / 2
                
                # Create new propellers
                prop_size = self.drone_size / 3
                
                # Calculate propeller endpoints with rotation
                def calc_prop_end(start_x, start_y, angle_offset):
                    prop_angle = math.radians(angle + angle_offset)
                    end_x = start_x + prop_size * math.cos(prop_angle)
                    end_y = start_y + prop_size * math.sin(prop_angle)
                    return end_x, end_y
                
                # Top-left propeller
                tl_x, tl_y = body_x - radius, body_y - radius
                tl_end_x, tl_end_y = calc_prop_end(tl_x, tl_y, 45)
                prop1 = self.canvas.create_line(tl_x, tl_y, tl_end_x, tl_end_y, width=3)
                
                # Top-right propeller
                tr_x, tr_y = body_x + radius, body_y - radius
                tr_end_x, tr_end_y = calc_prop_end(tr_x, tr_y, 135)
                prop2 = self.canvas.create_line(tr_x, tr_y, tr_end_x, tr_end_y, width=3)
                
                # Bottom-left propeller
                bl_x, bl_y = body_x - radius, body_y + radius
                bl_end_x, bl_end_y = calc_prop_end(bl_x, bl_y, -45)
                prop3 = self.canvas.create_line(bl_x, bl_y, bl_end_x, bl_end_y, width=3)
                
                # Bottom-right propeller
                br_x, br_y = body_x + radius, body_y + radius
                br_end_x, br_end_y = calc_prop_end(br_x, br_y, -135)
                prop4 = self.canvas.create_line(br_x, br_y, br_end_x, br_end_y, width=3)
                
                # Update the drone object with new propellers
                self.drone_obj[1] = prop1
                self.drone_obj[2] = prop2
                self.drone_obj[3] = prop3
                self.drone_obj[4] = prop4
        
        # Update status indicators
        self.altitude_var.set(f"Altitude: {self.drone.altitude}m")
        self.position_var.set(f"Position: X={self.drone.x_position}m, Y={self.drone.y_position}m")
        direction_text = self.drone.direction if self.drone.is_moving and self.drone.direction else "None"
        self.direction_var.set(f"Direction: {direction_text}")
        
        # Continue animation loop
        self.root.after(self.animation_speed, self.animate)


  
