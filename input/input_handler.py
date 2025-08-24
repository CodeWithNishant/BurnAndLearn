"""
Input handling system for the rocket simulation.
Converts pygame input to physics control commands.
"""

import pygame
from physics.rocket import Controls


class InputHandler:
    """Handles input and converts to physics control commands."""
    
    def __init__(self):
        self.controls = Controls()
    
    def update(self, keys: pygame.key.ScancodeWrapper) -> Controls:
        """Update controls based on current key states."""
        self.controls.increase_throttle = keys[pygame.K_UP]
        self.controls.decrease_throttle = keys[pygame.K_DOWN]
        self.controls.rotate_left = keys[pygame.K_LEFT]
        self.controls.rotate_right = keys[pygame.K_RIGHT]
        self.controls.engine_shutdown = keys[pygame.K_o]
        
        return self.controls
    
    def handle_events(self, events: list) -> dict:
        """Handle discrete input events (key presses, not holds)."""
        result = {}
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    result['restart'] = True
                elif event.key == pygame.K_h:
                    result['toggle_help'] = True
                elif event.key == pygame.K_m:
                    result['toggle_audio'] = True
        
        return result