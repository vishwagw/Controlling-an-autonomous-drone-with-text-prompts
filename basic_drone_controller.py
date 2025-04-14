# first attempt:
# Graphical user interface based controller unit:
# libs:
import tkinter as tk
import threading
import time
from tkinter import scrolledtext, messagebox

# class for drone simulator:
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
            
        return "\n".join(status)
    
# DroneControlApp:
class DroneControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drone Control System")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.drone = DroneSimulator()
        self.command_history = []
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Create frames
        self.top_frame = tk.Frame(self.root, padx=10, pady=10)
        self.top_frame.pack(fill=tk.X)
        
        self.middle_frame = tk.Frame(self.root, padx=10)
        self.middle_frame.pack(fill=tk.BOTH, expand=True)
        
        self.bottom_frame = tk.Frame(self.root, padx=10, pady=10)
        self.bottom_frame.pack(fill=tk.X)
        
        # Command input
        tk.Label(self.top_frame, text="Enter command:").pack(side=tk.LEFT)
        self.command_entry = tk.Entry(self.top_frame, width=40)
        self.command_entry.pack(side=tk.LEFT, padx=5)
        self.command_entry.bind("<Return>", self.process_command)
        self.send_button = tk.Button(self.top_frame, text="Send", command=self.process_command)
        self.send_button.pack(side=tk.LEFT)
        
        # Output display
        self.output_display = scrolledtext.ScrolledText(self.middle_frame, wrap=tk.WORD, height=20)
        self.output_display.pack(fill=tk.BOTH, expand=True)
        self.output_display.config(state=tk.DISABLED)
        
        # Quick command buttons
        tk.Label(self.bottom_frame, text="Quick Commands:").pack(side=tk.LEFT)
        
        self.takeoff_button = tk.Button(self.bottom_frame, text="Take Off", 
                                       command=lambda: self.execute_command("take off"))
        self.takeoff_button.pack(side=tk.LEFT, padx=5)
        
        self.land_button = tk.Button(self.bottom_frame, text="Land", 
                                    command=lambda: self.execute_command("land"))
        self.land_button.pack(side=tk.LEFT, padx=5)
        
        self.status_button = tk.Button(self.bottom_frame, text="Status", 
                                     command=lambda: self.execute_command("status"))
        self.status_button.pack(side=tk.LEFT, padx=5)
        
        self.help_button = tk.Button(self.bottom_frame, text="Help", 
                                   command=self.show_help)
        self.help_button.pack(side=tk.LEFT, padx=5)
        
        # Initial message
        self.update_output("Drone Control System initialized. Type 'help' for available commands.")
    
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
- help/commands: Show this help
- exit/quit: Exit the program
        """
        self.update_output(help_text)


def main():
    root = tk.Tk()
    app = DroneControlApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

