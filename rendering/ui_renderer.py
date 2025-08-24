"""
UI and HUD rendering system.
Handles flight information, warnings, and end-game screens.
"""

import pygame
import math
from physics.rocket import RocketState
from config import (
    TEXT_COLOR, SUCCESS_COLOR, FAIL_COLOR, DISPLAY_WIDTH, DISPLAY_HEIGHT,
    PhysicsConfig, RocketConfig, UIConfig
)


class UIRenderer:
    """Handles all UI and HUD rendering."""
    
    def __init__(self, font: pygame.font.Font, big_font: pygame.font.Font):
        self.font = font
        self.big_font = big_font
    
    def render_hud(self, surface: pygame.Surface, rocket_state: RocketState):
        """Render the heads-up display with flight information."""
        # Calculate display values
        altitude = max(0, rocket_state.y - RocketConfig.HEIGHT/2)
        angle_degrees = rocket_state.angle * 180 / math.pi
        engine_percentage = int(rocket_state.engine_percentage * 100)
        fuel_kg = int(rocket_state.fuel_mass)
        mass_kg = int(rocket_state.total_mass)
        
        # Create text surfaces with appropriate colors
        info_items = [
            (f"Altitude: {altitude:.1f} m", TEXT_COLOR),
            (f"Speed: {rocket_state.speed:.2f} m/s", 
             SUCCESS_COLOR if rocket_state.speed < PhysicsConfig.SAFE_LANDING_SPEED else FAIL_COLOR),
            (f"V-Speed: {rocket_state.vy:.2f} m/s",
             SUCCESS_COLOR if abs(rocket_state.vy) < PhysicsConfig.SAFE_LANDING_SPEED else FAIL_COLOR),
            (f"H-Speed: {rocket_state.vx:.2f} m/s",
             SUCCESS_COLOR if abs(rocket_state.vx) < PhysicsConfig.SAFE_LANDING_SPEED else FAIL_COLOR),
            (f"Angle: {angle_degrees:.1f}°",
             SUCCESS_COLOR if abs(rocket_state.angle) < PhysicsConfig.SAFE_LANDING_ANGLE else FAIL_COLOR),
            (f"Engine: {engine_percentage}%", self._get_engine_color(rocket_state.engine_percentage)),
            (f"Mass: {mass_kg} kg", TEXT_COLOR),
            (f"TWR: {rocket_state.thrust_to_weight_ratio:.2f}",
             SUCCESS_COLOR if rocket_state.thrust_to_weight_ratio > 1.0 else FAIL_COLOR),
            (f"Position: ({rocket_state.x:.1f}, {rocket_state.y:.1f})", TEXT_COLOR)
        ]
        
        # Render flight info panel
        for i, (text, color) in enumerate(info_items):
            text_surface = self.font.render(text, True, color)
            surface.blit(text_surface, (UIConfig.INFO_PANEL_X, 
                                      UIConfig.INFO_PANEL_Y + i * UIConfig.INFO_LINE_HEIGHT))
        
        # Render fuel display (top right)
        fuel_color = (255, 255, 0) if rocket_state.fuel_mass > 1000 else FAIL_COLOR
        fuel_text = self.font.render(f"Fuel: {fuel_kg} kg", True, fuel_color)
        surface.blit(fuel_text, (DISPLAY_WIDTH - UIConfig.FUEL_DISPLAY_X_OFFSET, UIConfig.INFO_PANEL_Y))
        
        # Render warnings
        self._render_warnings(surface, rocket_state)
    
    def _get_engine_color(self, engine_percentage: float) -> tuple:
        """Get appropriate color for engine percentage display."""
        if engine_percentage < 0.8:
            return SUCCESS_COLOR
        elif engine_percentage < 1.0:
            return (255, 255, 0)  # Yellow for high throttle
        else:
            return FAIL_COLOR     # Red for maximum throttle
    
    def _render_warnings(self, surface: pygame.Surface, rocket_state: RocketState):
        """Render critical warnings."""
        warning_y = UIConfig.WARNING_TEXT_Y
        
        # Engine off warning
        if not rocket_state.main_thruster_on:
            engine_off_text = self.font.render("ENGINE OFF", True, FAIL_COLOR)
            text_rect = engine_off_text.get_rect(center=(DISPLAY_WIDTH/2, warning_y))
            surface.blit(engine_off_text, text_rect)
            warning_y += UIConfig.INFO_LINE_HEIGHT
        
        # No fuel warning
        if rocket_state.fuel_mass <= 0:
            no_fuel_text = self.font.render("NO FUEL", True, FAIL_COLOR)
            text_rect = no_fuel_text.get_rect(center=(DISPLAY_WIDTH/2, warning_y))
            surface.blit(no_fuel_text, text_rect)
    
    def render_end_screen(self, surface: pygame.Surface, rocket_state: RocketState, timer: float):
        """Render the end game screen (success or failure)."""
        # Semi-transparent overlay
        overlay = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Main message
        color = SUCCESS_COLOR if rocket_state.landed else FAIL_COLOR
        message_surface = self.big_font.render(rocket_state.message, True, color)
        message_rect = message_surface.get_rect(center=(DISPLAY_WIDTH/2, DISPLAY_HEIGHT/2 - 50))
        surface.blit(message_surface, message_rect)
        
        # Mission statistics
        fuel_used = RocketConfig.FUEL_CAPACITY - rocket_state.fuel_mass
        stats = [
            f"Fuel Used: {fuel_used:.1f} kg",
            f"Time: {timer:.1f} seconds"
        ]
        
        for i, stat in enumerate(stats):
            stat_surface = self.font.render(stat, True, TEXT_COLOR)
            stat_rect = stat_surface.get_rect(center=(DISPLAY_WIDTH/2, DISPLAY_HEIGHT/2 + 20 + i * 40))
            surface.blit(stat_surface, stat_rect)
        
        # Restart instruction
        restart_surface = self.font.render("Press 'R' to Restart", True, TEXT_COLOR)
        restart_rect = restart_surface.get_rect(center=(DISPLAY_WIDTH/2, DISPLAY_HEIGHT/2 + 120))
        surface.blit(restart_surface, restart_rect)
    
    def render_controls_help(self, surface: pygame.Surface):
        """Render control instructions (optional)."""
        controls = [
            "UP: Increase Engine Power",
            "DOWN: Decrease Engine Power",
            "LEFT/RIGHT: Rotate",
            "O: Engine Shutdown",
            "R: Restart"
        ]
        
        start_x = DISPLAY_WIDTH - 350
        start_y = 40
        
        for i, control in enumerate(controls):
            control_surface = self.font.render(control, True, (150, 150, 150))
            surface.blit(control_surface, (start_x, start_y + i * UIConfig.INFO_LINE_HEIGHT))