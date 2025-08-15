"""
Rocket-specific rendering system.
Handles rocket body, flames, and visual effects.
"""

import pygame
import math
import random
from physics.rocket import RocketState
from utils.camera import Camera
from config import ROCKET_COLOR, FLAME_COLOR, SCALE, RocketConfig


class RocketRenderer:
    """Handles all rocket-specific rendering."""
    
    def render(self, surface: pygame.Surface, rocket_state: RocketState, camera: Camera):
        """Render the rocket and its effects."""
        screen_x, screen_y = camera.world_to_screen(rocket_state.x, rocket_state.y)
        
        # Draw main engine flame first (so it appears behind rocket)
        if rocket_state.main_thruster_on and rocket_state.engine_percentage >= 0.3:
            self._draw_main_engine_flame(surface, rocket_state, screen_x, screen_y)
        
        # Draw rocket body
        self._draw_rocket_body(surface, rocket_state, screen_x, screen_y)
        
        # Draw RCS flames
        if rocket_state.left_thruster_on:
            self._draw_rcs_flame(surface, rocket_state, screen_x, screen_y, 'left')
        
        if rocket_state.right_thruster_on:
            self._draw_rcs_flame(surface, rocket_state, screen_x, screen_y, 'right')
    
    def _draw_rocket_body(self, surface: pygame.Surface, rocket_state: RocketState, 
                         screen_x: float, screen_y: float):
        """Draw the main rocket body."""
        w = RocketConfig.WIDTH * SCALE / 2
        h = RocketConfig.HEIGHT * SCALE / 2
        
        # Define rocket shape points (relative to center)
        points = [
            (0, -h),        # Nose cone
            (w, h),         # Bottom right
            (w/2, h*0.8),   # Inner bottom right
            (-w/2, h*0.8),  # Inner bottom left
            (-w, h)         # Bottom left
        ]
        
        # Rotate points based on rocket angle
        rotated_points = []
        for x, y in points:
            new_x = x * math.cos(rocket_state.angle) - y * math.sin(rocket_state.angle)
            new_y = x * math.sin(rocket_state.angle) + y * math.cos(rocket_state.angle)
            rotated_points.append((new_x + screen_x, new_y + screen_y))
        
        # Draw rocket polygon
        pygame.draw.polygon(surface, ROCKET_COLOR, rotated_points)
    
    def _draw_main_engine_flame(self, surface: pygame.Surface, rocket_state: RocketState,
                               screen_x: float, screen_y: float):
        """Draw main engine flame effect behind the rocket body."""
        w = RocketConfig.WIDTH * SCALE / 2
        h = RocketConfig.HEIGHT * SCALE / 2

        # Intensity (0..1) controls length; add flicker
        intensity = max(0.0, min(1.0, float(rocket_state.engine_percentage)))
        flicker = 0.85 + random.random() * 0.3
        flame_length = h * (0.55 + intensity * 1.0) * flicker

        # Nozzle width smaller than body width
        nozzle_half_w = max(2.0, w * 0.28)
        base_y = h * 0.90  # inside bottom of body

        # Outer flame triangle (local coords)
        p1 = (-nozzle_half_w, base_y)
        p2 = ( nozzle_half_w, base_y)
        p3 = ( 0.0,          base_y + flame_length)

        # Inner hot core triangle (smaller and shorter)
        core_scale_w = 0.55
        core_scale_l = 0.60
        p1c = (-nozzle_half_w * core_scale_w, base_y)
        p2c = ( nozzle_half_w * core_scale_w, base_y)
        p3c = ( 0.0,                           base_y + flame_length * core_scale_l)

        # Rotate + translate points to screen coords
        def rot_translate(pt):
            x, y = pt
            ca = math.cos(rocket_state.angle)
            sa = math.sin(rocket_state.angle)
            nx = x * ca - y * sa
            ny = x * sa + y * ca
            return (nx + screen_x, ny + screen_y)

        outer_poly = [rot_translate(p) for p in (p1, p2, p3)]
        core_poly  = [rot_translate(p) for p in (p1c, p2c, p3c)]

        # Core color slightly brighter
        core_color = (
            min(255, FLAME_COLOR[0] + 35),
            min(255, FLAME_COLOR[1] + 35),
            min(255, FLAME_COLOR[2])
        )

        pygame.draw.polygon(surface, FLAME_COLOR, outer_poly)
        pygame.draw.polygon(surface, core_color, core_poly)

        """Draw a small RCS puff on the requested side ('left' or 'right'). """

    def _draw_rcs_flame(self, surface: pygame.Surface, rocket_state: RocketState,
                        screen_x: float, screen_y: float, side: str):
        w = RocketConfig.WIDTH * SCALE / 2
        h = RocketConfig.HEIGHT * SCALE / 2
        # Position thrusters around the mid-body
        offset_y = 0.0 # center of rocket body in local frame
        x_offset = w * 0.95 if side == 'right' else -w * 0.95
        # Small nozzle height and variable flame length with flicker
        nozzle_h = max (2.0, h * 0.12)
        flicker = 0.85 + random.random() * 0.4
        base_len = w * 1
        flame_len = base_len * flicker
        # Define local-frame triangle pointing outward
        if side == 'left':
            base_top = (x_offset, offset_y - nozzle_h * 0.5)
            base_bottom = (x_offset, offset_y + nozzle_h * 0.5)
            tip = (x_offset - flame_len, offset_y)
        else:
            base_top = (x_offset, offset_y - nozzle_h * 0.5)
            base_bottom = (x_offset, offset_y + nozzle_h * 0.5)
            tip = (x_offset + flame_len, offset_y)

        # Rotation + translation
        def rot_translate(pt):
                x, y = pt
                ca = math.cos(rocket_state.angle)
                sa = math.sin(rocket_state.angle)
                nx = x * ca - y * sa
                ny = x * sa + y * ca
                return (nx + screen_x, ny + screen_y)

        poly = [rot_translate(p) for p in (base_top, base_bottom, tip)]
        pygame.draw.polygon(surface, FLAME_COLOR, poly)