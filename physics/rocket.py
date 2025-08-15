"""
Pure rocket physics implementation.
Contains no rendering or audio code - only physics calculations.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any
from config import PhysicsConfig, RocketConfig


@dataclass
class RocketState:
    """Complete state of the rocket for external systems."""
    # Position and motion
    x: float
    y: float
    vx: float
    vy: float
    angle: float
    angular_velocity: float
    
    # Mass and fuel
    fuel_mass: float
    total_mass: float
    
    # Engine state
    main_thruster_on: bool
    left_thruster_on: bool
    right_thruster_on: bool
    engine_percentage: float
    
    # Status
    landed: bool
    crashed: bool
    message: str
    
    # Calculated values
    speed: float
    thrust_to_weight_ratio: float


@dataclass
class Controls:
    """Input controls for the rocket."""
    increase_throttle: bool = False
    decrease_throttle: bool = False
    rotate_left: bool = False
    rotate_right: bool = False
    engine_shutdown: bool = False


class RocketPhysics:
    """Pure physics simulation of a rocket."""
    
    def __init__(self, x: float = 0, y: float = 500):
        # Position and velocity (world units - meters)
        self.x = x
        self.y = y
        self.vx = 0.0  # Horizontal velocity in m/s
        self.vy = 0.0  # Vertical velocity in m/s
        
        # Rotation (radians, 0 = pointing up)
        self.angle = 0.0
        self.angular_velocity = 0.0
        
        # Physical properties
        self.fuel_mass = RocketConfig.START_FUEL
        
        # Engine state
        self.engine_percentage = RocketConfig.MIN_ENGINE_PERCENTAGE
        self.main_thruster_on = False
        self.left_thruster_on = False
        self.right_thruster_on = False
        
        # Status
        self.landed = False
        self.crashed = False
        self.message = ""
    
    def get_total_mass(self) -> float:
        """Calculate current total mass (dry mass + remaining fuel)."""
        return RocketConfig.DRY_MASS + self.fuel_mass
    
    def get_thrust_to_weight_ratio(self) -> float:
        """Calculate current thrust-to-weight ratio."""
        weight = self.get_total_mass() * PhysicsConfig.CURRENT_GRAVITY
        max_thrust = RocketConfig.MAIN_ENGINE_THRUST
        return max_thrust / weight if weight > 0 else 0
    
    def get_speed(self) -> float:
        """Calculate current speed magnitude."""
        return math.sqrt(self.vx**2 + self.vy**2)
    
    def get_state(self) -> RocketState:
        """Get complete rocket state for external systems."""
        return RocketState(
            x=self.x,
            y=self.y,
            vx=self.vx,
            vy=self.vy,
            angle=self.angle,
            angular_velocity=self.angular_velocity,
            fuel_mass=self.fuel_mass,
            total_mass=self.get_total_mass(),
            main_thruster_on=self.main_thruster_on,
            left_thruster_on=self.left_thruster_on,
            right_thruster_on=self.right_thruster_on,
            engine_percentage=self.engine_percentage,
            landed=self.landed,
            crashed=self.crashed,
            message=self.message,
            speed=self.get_speed(),
            thrust_to_weight_ratio=self.get_thrust_to_weight_ratio()
        )
    
    def update(self, controls: Controls, dt: float) -> Dict[str, Any]:
        """
        Update physics simulation.
        Returns events for other systems (audio, etc.).
        """
        if self.landed or self.crashed:
            return {}
        
        events = {}
        
        # Reset thruster states
        self.left_thruster_on = False
        self.right_thruster_on = False
        
        current_mass = self.get_total_mass()
        
        # --- Engine Control ---
        old_engine_on = self.main_thruster_on
        old_engine_percentage = self.engine_percentage
        
        if controls.increase_throttle:
            self.main_thruster_on = True
            self.engine_percentage = min(1.0, 
                self.engine_percentage + RocketConfig.ENGINE_INCREASE_RATE * dt)
        
        if controls.decrease_throttle and self.main_thruster_on:
            self.engine_percentage = max(RocketConfig.MIN_ENGINE_PERCENTAGE,
                self.engine_percentage - RocketConfig.ENGINE_DECREASE_RATE * dt)
        
        if controls.engine_shutdown:
            self.main_thruster_on = False
            self.engine_percentage = RocketConfig.MIN_ENGINE_PERCENTAGE
        
        # --- Main Engine Physics ---
        if (self.main_thruster_on and 
            self.engine_percentage >= RocketConfig.MIN_ENGINE_PERCENTAGE and 
            self.fuel_mass > 0):
            
            # Calculate thrust force
            thrust_force = RocketConfig.MAIN_ENGINE_THRUST * self.engine_percentage
            
            # Apply thrust acceleration
            thrust_accel_x = (math.sin(self.angle) * thrust_force) / current_mass
            thrust_accel_y = (math.cos(self.angle) * thrust_force) / current_mass
            
            self.vx += thrust_accel_x * dt
            self.vy += thrust_accel_y * dt
            
            # Consume fuel
            fuel_consumed = (RocketConfig.FUEL_CONSUMPTION_RATE * 
                           self.engine_percentage * dt)
            self.fuel_mass = max(0, self.fuel_mass - fuel_consumed)
            
            # Engine sound event
            if not old_engine_on or old_engine_percentage != self.engine_percentage:
                events['engine_state_changed'] = {
                    'active': True,
                    'throttle': self.engine_percentage
                }
        else:
            self.main_thruster_on = False
            if old_engine_on:
                events['engine_state_changed'] = {'active': False, 'throttle': 0}
        
        # --- RCS Physics ---
        rcs_active = False
        
        if controls.rotate_left and self.fuel_mass > 0:
            torque_arm = RocketConfig.HEIGHT / 2
            torque = RocketConfig.RCS_THRUST * torque_arm
            angular_accel = -torque / RocketConfig.MOMENT_OF_INERTIA
            
            self.angular_velocity += angular_accel * dt
            fuel_consumed = RocketConfig.FUEL_CONSUMPTION_RATE * 0.1 * dt
            self.fuel_mass = max(0, self.fuel_mass - fuel_consumed)
            self.left_thruster_on = True
            rcs_active = True
        
        if controls.rotate_right and self.fuel_mass > 0:
            torque_arm = RocketConfig.HEIGHT / 2
            torque = RocketConfig.RCS_THRUST * torque_arm
            angular_accel = torque / RocketConfig.MOMENT_OF_INERTIA
            
            self.angular_velocity += angular_accel * dt
            fuel_consumed = RocketConfig.FUEL_CONSUMPTION_RATE * 0.1 * dt
            self.fuel_mass = max(0, self.fuel_mass - fuel_consumed)
            self.right_thruster_on = True
            rcs_active = True
        
        # RCS sound event
        events['rcs_active'] = rcs_active
        
        # --- Gravity ---
        gravity_accel = -PhysicsConfig.CURRENT_GRAVITY
        self.vy += gravity_accel * dt
        
        # --- Update Position and Rotation ---
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.angular_velocity * dt
        
        # Apply damping
        self.angular_velocity *= PhysicsConfig.ANGULAR_DAMPING
        self.vx *= PhysicsConfig.ATMOSPHERIC_DRAG
        self.vy *= PhysicsConfig.ATMOSPHERIC_DRAG
        
        # --- Collision Detection ---
        rocket_bottom = self.y - (RocketConfig.HEIGHT / 2)
        if rocket_bottom <= 0:
            self.y = RocketConfig.HEIGHT / 2
            landing_result = self._check_landing()
            events.update(landing_result)
        
        return events
    
    def _check_landing(self) -> Dict[str, Any]:
        """Check landing conditions and return events."""
        speed = self.get_speed()
        
        # Landing conditions
        on_landing_pad = abs(self.x) <= PhysicsConfig.LANDING_PAD_RANGE
        safe_speed = speed < PhysicsConfig.SAFE_LANDING_SPEED
        upright = abs(self.angle) < PhysicsConfig.SAFE_LANDING_ANGLE
        
        if safe_speed and upright and on_landing_pad:
            self.landed = True
            self.message = "LANDING SUCCESSFUL!"
            event_type = 'landing_success'
        else:
            self.crashed = True
            reasons = []
            if not safe_speed:
                reasons.append(f"High Speed ({speed:.1f} m/s)")
            if not upright:
                reasons.append(f"Bad Angle ({abs(self.angle * 180/math.pi):.0f}°)")
            if not on_landing_pad:
                reasons.append("Missed Landing Pad")
            
            self.message = f"CRASHED: {', '.join(reasons)}"
            event_type = 'landing_crash'
        
        # Stop all movement
        self.vx = self.vy = self.angular_velocity = 0
        
        return {event_type: True}
    
    def reset(self, x: float = None, y: float = None):
        """Reset rocket to initial state."""
        self.x = x if x is not None else RocketConfig.START_X
        self.y = y if y is not None else RocketConfig.START_Y
        self.vx = self.vy = 0.0
        self.angle = self.angular_velocity = 0.0
        self.fuel_mass = RocketConfig.START_FUEL
        self.engine_percentage = RocketConfig.MIN_ENGINE_PERCENTAGE
        self.main_thruster_on = False
        self.left_thruster_on = self.right_thruster_on = False
        self.landed = self.crashed = False
        self.message = ""