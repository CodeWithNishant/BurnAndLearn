"""
Main rendering system that coordinates all visual elements.
"""

import pygame
import math
import random
from typing import Optional
from physics.rocket import RocketState
from utils.camera import Camera
from config import (
    BG_COLOR, DISPLAY_WIDTH, DISPLAY_HEIGHT, SCALE, GROUND_COLOR, 
    SUCCESS_COLOR, STAR_COLOR, PhysicsConfig, UIConfig
)


class Renderer:
    """Main rendering coordinator for the rocket simulation."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", UIConfig.FONT_SIZE)
        self.big_font = pygame.font.SysFont("Arial", UIConfig.BIG_FONT_SIZE, bold=True)
        
        # Initialize sub-renderers
        from rendering.rocket_renderer import RocketRenderer
        from rendering.ui_renderer import UIRenderer
        
        self.rocket_renderer = RocketRenderer()
        self.ui_renderer = UIRenderer(self.font, self.big_font)
    
    def render_frame(self, rocket_state: RocketState, camera: Camera, timer: float):
        """Render a complete frame."""
        # Clear screen
        self.screen.fill(BG_COLOR)
        
        # Render background elements
        self._render_stars()
        self._render_ground(camera)
        
        # Render rocket
        self.rocket_renderer.render(self.screen, rocket_state, camera)
        
        # Render UI
        self.ui_renderer.render_hud(self.screen, rocket_state)
        
        # Render end screen if needed
        if rocket_state.landed or rocket_state.crashed:
            self.ui_renderer.render_end_screen(self.screen, rocket_state, timer)
    
    def _render_stars(self):
        """Render background star field."""
        for i in range(UIConfig.STAR_COUNT):
            star_x = (i * 137) % DISPLAY_WIDTH
            star_y = (i * 149) % (DISPLAY_HEIGHT - 100)
            pygame.draw.circle(self.screen, STAR_COLOR, 
                             (star_x, star_y), UIConfig.STAR_RADIUS)
    
    def _render_ground(self, camera: Camera):
        """Render ground line and landing pad."""
        # Ground line
        ground_world_y = 0
        _, ground_screen_y = camera.world_to_screen(0, ground_world_y)
        
        if 0 <= ground_screen_y <= DISPLAY_HEIGHT + 100:
            # Draw ground line
            pygame.draw.line(self.screen, GROUND_COLOR, 
                           (0, ground_screen_y), (DISPLAY_WIDTH, ground_screen_y), 2)
            
            # Landing pad
            pad_center_x, _ = camera.world_to_screen(0, ground_world_y)
            pad_width = PhysicsConfig.LANDING_PAD_RANGE * 2 * SCALE
            
            # Landing pad line
            pygame.draw.line(self.screen, SUCCESS_COLOR,
                           (pad_center_x - pad_width/2, ground_screen_y),
                           (pad_center_x + pad_width/2, ground_screen_y), 8)
            
            # Landing pad markers
            for i in range(-1, 2):
                marker_x = pad_center_x + i * pad_width/4
                pygame.draw.line(self.screen, SUCCESS_COLOR,
                               (marker_x, ground_screen_y - 10),
                               (marker_x, ground_screen_y + 10), 3)