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


  
