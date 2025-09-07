import gymnasium as gym
import numpy as np
import pygame
from gymnasium import spaces

from physics.rocket import RocketPhysics, Controls
from rendering.renderer import Renderer
from utils.camera import Camera
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT, RocketConfig


class RocketEnv(gym.Env):
    """OpenAI Gym-compatible environment for Burn&Learn rocket simulation."""

    metadata = {"render.modes": ["human"]}

    def __init__(self):
        super(RocketEnv, self).__init__()

        # --- Physics & Rocket ---
        self.rocket = RocketPhysics(RocketConfig.START_X, RocketConfig.START_Y)
        self.dt = 0.1  # fixed timestep in seconds

        # --- Rendering (optional) ---
        self.screen = None
        self.renderer = None
        self.camera = None

        # --- Spaces ---
        # Actions: 0=no-op, 1=main engine up 2=main engine down, 3=rcs_left, 4=rcs_right, 5=cut engines
        self.action_space = spaces.Discrete(6)

        # Observations: x, y, vx, vy, angle, angular_velocity, fuel
        low = np.array(
            [-np.inf, -np.inf, -np.inf, -np.inf, -np.pi, -np.inf, 0],
            dtype=np.float32,
        )
        high = np.array(
            [np.inf, np.inf, np.inf, np.inf, np.pi, np.inf, RocketConfig.FUEL_CAPACITY],
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(low, high, dtype=np.float32)

        # --- Internal state ---
        self.timer = 0.0
        self.done = False

    # --- Gym API ---

    def reset(self, *, seed=None, options=None):
        """Reset the environment to initial state."""
        if seed is not None:
            np.random.seed(seed)
        self.rocket.reset()
        self.timer = 0.0
        self.done = False

        obs = self._get_obs()
        info = {}
        return obs, info

    def step(self, action: int):
        """Apply one action and update the environment."""

        '''
            increase_throttle: bool = False
            decrease_throttle: bool = False
            rotate_left: bool = False
            rotate_right: bool = False
            engine_shutdown: bool = False
        '''

        # Use Controls dataclass instead of dict
        controls = Controls()
        if action == 1:
            controls.increase_throttle = True
        elif action == 2:
            controls.decrease_throttle = True
        elif action == 3:
            controls.rotate_left = True
        elif action == 4:
            controls.rotate_right = True
        elif action == 5:
            controls.engine_shutdown = True

        # Update rocket physics
        self.rocket.update(controls, self.dt)
        self.timer += self.dt

        # Get next state
        obs = self._get_obs()

        # Calculate reward
        reward = self._calculate_reward()

        # Episode termination
        terminated = self.rocket.landed or self.rocket.crashed or self.rocket.fuel_mass <= 0

        truncated = False 
        if self.timer > 2000:  # e.g., 2000 timesteps
            truncated = True

        info = {
            "time": self.timer,
            "fuel": self.rocket.fuel_mass,
            "altitude": self.rocket.y,
            "velocity": self.rocket.get_speed(),
            "landed": self.rocket.landed,
            "crashed": self.rocket.crashed,
        }

        return obs, reward, terminated, truncated, info

    def render(self):
        """Render the environment with pygame."""
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
            self.renderer = Renderer(self.screen)
            self.camera = Camera(self.rocket.x, self.rocket.y)

        # Update camera
        rocket_speed = self.rocket.get_speed()
        if rocket_speed < 100:
            self.camera.follow(self.rocket.x, self.rocket.y, 0.05)
        else:
            self.camera.follow(self.rocket.x, self.rocket.y, rocket_speed/1000)

        # Draw frame
        self.screen.fill((0, 0, 0))
        rocket_state = self.rocket.get_state()
        self.renderer.render_frame(rocket_state, self.camera, self.timer)
        pygame.display.flip()

    def close(self):
        """Close the environment and cleanup."""
        if self.screen is not None:
            pygame.quit()
            self.screen = None

    # --- Helpers ---

    def _get_obs(self):
        """Return current state as numpy array."""
        state = self.rocket.get_state()
        return np.array(
            [
                state.x,
                state.y,
                state.vx,
                state.vy,
                state.angle,
                state.angular_velocity,
                state.fuel_mass,
            ],
            dtype=np.float32,
        )

    def _calculate_reward(self):
        """Reward shaping logic."""
        reward = -1  # small penalty every step

        if self.rocket.landed:
            if (
                abs(self.rocket.vx) < 2
                and abs(self.rocket.vy) < 2
                and abs(self.rocket.angle) < 0.1
            ):
                reward += 1000  # perfect landing
            else:
                reward += 500  # okay landing
        elif self.rocket.crashed:
            reward -= 1000  # big penalty for crash

        return reward