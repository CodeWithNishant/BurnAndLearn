"""
Main game loop for the rocket physics simulation.
Coordinates all systems and handles the game flow.
"""

import pygame
import sys
from physics.rocket import RocketPhysics
from audio.sound_manager import SoundManager
from rendering.renderer import Renderer
from utils.camera import Camera
from input.input_handler import InputHandler
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT, FPS, RocketConfig


class RocketSimulation:
    """Main game class that coordinates all systems."""
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption("Burn & Learn - Realistic Physics")
        
        # Create main systems
        self.screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Initialize game systems
        self.rocket = RocketPhysics(RocketConfig.START_X, RocketConfig.START_Y)
        self.camera = Camera(self.rocket.x, self.rocket.y)
        self.sound_manager = SoundManager()
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler()
        
        # Game state
        self.running = True
        self.timer = 0.0
        self.show_help = False
    
    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # Update timer (only when rocket is active)
            if not self.rocket.landed and not self.rocket.crashed:
                self.timer += dt
            
            # Handle input
            self._handle_input()
            
            # Update game systems
            self._update_systems(dt)
            
            # Render frame
            self._render_frame()
            
            pygame.display.flip()
        
        # Cleanup
        self._cleanup()
    
    def _handle_input(self):
        """Handle all input events."""
        # Get events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
        
        # Handle discrete events
        input_events = self.input_handler.handle_events(events)
        
        if 'restart' in input_events:
            self._restart_game()
        
        if 'toggle_help' in input_events:
            self.show_help = not self.show_help
        
        if 'toggle_audio' in input_events:
            self.sound_manager.set_enabled(not self.sound_manager.enabled)
        
        # Get continuous input
        keys = pygame.key.get_pressed()
        controls = self.input_handler.update(keys)
        
        # Update rocket physics
        physics_events = self.rocket.update(controls, self.clock.get_time() / 1000.0)
        
        # Send events to audio system
        self.sound_manager.handle_events(physics_events)
    
    def _update_systems(self, dt: float):
        """Update all game systems."""
        # Update camera to follow rocket
        self.camera.follow(self.rocket.x, self.rocket.y)
    
    def _render_frame(self):
        """Render the current frame."""
        rocket_state = self.rocket.get_state()
        self.renderer.render_frame(rocket_state, self.camera, self.timer)
        
        # Optionally show controls help
        if self.show_help:
            self.renderer.ui_renderer.render_controls_help(self.screen)
    
    def _restart_game(self):
        """Restart the game with a fresh rocket."""
        # Stop all sounds
        self.sound_manager._stop_all_sounds()
        
        # Reset game state
        self.rocket.reset()
        self.camera.reset(self.rocket.x, self.rocket.y)
        self.timer = 0.0
    
    def _cleanup(self):
        """Clean up resources."""
        self.sound_manager.cleanup()
        pygame.quit()


def main():
    """Entry point for the rocket simulation."""
    try:
        game = RocketSimulation()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"Game crashed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()