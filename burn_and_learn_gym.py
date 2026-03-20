import gymnasium as gym
import numpy as np
import pygame
import math
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
        """
        Reward system focused purely on landing.

        Goals:
        1. Encourage the rocket to move closer to the ground.
        2. Penalize moving away from the ground.
        3. Penalize sideways motion.
        4. Reward slower vertical speed near landing.
        5. Give a large reward for successful landing and moderate penalty for crash.
        """

        reward = 0.0

        # --- 1. Encourage getting closer to the ground ---
        # Ground is y = 0. Smaller altitude should give higher reward
        reward += (1000.0 - self.rocket.y) * 0.01

        # --- 2. Penalize moving upward (positive vy means going up) ---
        if self.rocket.vy > 0:
            reward -= abs(self.rocket.vy) * 0.1

        # --- 3. Penalize sideways velocity ---
        reward -= abs(self.rocket.vx) * 0.05

        # --- 4. Reward gentle vertical speed near ground ---
        if self.rocket.y < 100:  # only care near landing
            reward += max(0, 10 - abs(self.rocket.vy))

        # --- 5. Terminal rewards ---
        if self.rocket.landed:
            # Reward based on how soft the landing was
            reward += max(0, 10 - abs(self.rocket.vy)) * 50
            reward += 500

        if self.rocket.crashed:
            reward -= 300

        return float(reward)