"""
Camera system for smooth following and world-to-screen coordinate conversion.
"""

from typing import Tuple
from config import CameraConfig, DISPLAY_WIDTH, DISPLAY_HEIGHT, SCALE


class Camera:
    """Handles camera positioning and coordinate transformations."""
    
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    def follow(self, target_x: float, target_y: float, follow_smoothness: float):
        """Smoothly follow a target position."""
        # Calculate target camera position with offset
        target_camera_x = target_x
        target_camera_y = target_y + CameraConfig.Y_OFFSET
        
        # Smooth interpolation to target
        self.x += (target_camera_x - self.x) * follow_smoothness
        self.y += (target_camera_y - self.y) * follow_smoothness

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates."""
        screen_x = (world_x - self.x) * SCALE + DISPLAY_WIDTH / 2
        screen_y = DISPLAY_HEIGHT - ((world_y - self.y) * SCALE + DISPLAY_HEIGHT / 2)
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        world_x = (screen_x - DISPLAY_WIDTH / 2) / SCALE + self.x
        world_y = ((DISPLAY_HEIGHT - screen_y) - DISPLAY_HEIGHT / 2) / SCALE + self.y
        return world_x, world_y
    
    def get_position(self) -> Tuple[float, float]:
        """Get current camera position."""
        return self.x, self.y
    
    def set_position(self, x: float, y: float):
        """Set camera position directly (no smoothing)."""
        self.x = x
        self.y = y
    
    def reset(self, target_x: float = 0, target_y: float = 0):
        """Reset camera to follow a new target immediately."""
        self.x = target_x
        self.y = target_y + CameraConfig.Y_OFFSET