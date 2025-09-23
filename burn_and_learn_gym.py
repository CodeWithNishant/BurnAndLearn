import gymnasium as gym
import numpy as np
import pygame
from gymnasium import spaces
import math

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
        # self.action_space = spaces.Discrete(6)


        # Action: [throttle, rotation]
        # throttle: continuous in [0.3, 1.0]
        # rotation: discrete encoded as {-1, 0, 1}
        self.action_space = gym.spaces.Box(
            low=np.array([0.3, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            dtype=np.float32
        )

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
        """
        Reset the environment to initial state and initialize tracking variables for reward shaping.

        Changes:
        - Randomize starting altitude (so the agent learns a general strategy).
        - Reset physics, timers, and tracking variables for reward calculation.
        """
        if seed is not None:
            np.random.seed(seed)

        # ------------------------------
        # 1. Randomize starting state
        # ------------------------------
        # Random altitude between 400m and 1200m
        start_y = np.random.uniform(400, 1200)
        start_x = RocketConfig.START_X  # keep horizontal start fixed (or randomize later if needed)
    
        # Reset rocket physics with randomized starting position
        self.rocket.reset(x=start_x, y=start_y)

        self.starting_altitude = start_y  # store starting altitude if needed for rewards/metrics
        self.timer = 0.0
        self.done = False

        # ------------------------------
        # 2. Set landing pad position (can stay fixed)
        # ------------------------------
        self.landing_pad_x = getattr(RocketConfig, "LANDING_PAD_X", 0.0)

        # ------------------------------
        # 3. Initialize tracking variables for reward shaping
        # ------------------------------
        self._prev_pad_dist = math.hypot(self.rocket.x - self.landing_pad_x, self.rocket.y - 0.0)
        self._prev_abs_vy = abs(self.rocket.vy)
        self._prev_speed = self.rocket.get_speed()
        self._prev_fuel = self.rocket.fuel_mass

        # ------------------------------
        # 4. Return initial observation
        # ------------------------------
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
        # if action == 1:
        #     controls.increase_throttle = True
        # elif action == 2:
        #     controls.decrease_throttle = True
        # elif action == 3:
        #     controls.rotate_left = True
        # elif action == 4:
        #     controls.rotate_right = True
        # elif action == 5:
        #     controls.engine_shutdown = True

        #Apply throttle and rotation from continuous action space
        throttle = float(action[0]) # in [0.3, 1.0]
        rotation = int(np.round(action[1]))   # in {-1, 0, 1}

        if throttle >= 0.3:
            self.rocket.main_thruster_on = True
            self.rocket.engine_percentage = throttle
        else:
            self.rocket.main_thruster_on = False
            self.rocket.engine_percentage = RocketConfig.MIN_ENGINE_PERCENTAGE

        # Apply rotation commands
        if rotation == -1:
            controls.rotate_left = True
        elif rotation == 1:
            controls.rotate_right = True
        # if rotation == 0, do nothing (no rotation command)    

        # Update rocket physics
        self.rocket.update(controls, self.dt)
        self.timer += self.dt

        # Get next state
        obs = self._get_obs()

        # Calculate reward
        reward = self._calculate_reward_approach1()

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
        Dense, potential-based reward shaping for rocket landing.

        Core ideas:
        - Encourage the rocket to descend safely (no extra upward travel).
        - Reward progress toward the landing pad (reducing distance).
        - Encourage reducing vertical/horizontal speed and tilt (stability).
        - Penalize wasted fuel and unnecessary steps (efficiency).
        - Give big terminal bonuses for good landings, heavy penalties for crashes.
        """

        reward = 0.0  # baseline each step

        # ------------------------------
        # 1. Progress toward landing pad
        # ------------------------------
        # Distance from rocket to landing pad (x position + ground at y=0).
        curr_pad_dist = math.hypot(self.rocket.x - self.landing_pad_x, self.rocket.y - 0.0)

        # Reward is proportional to reduction in distance since last step.
        # If the rocket got closer -> positive reward, if farther -> negative.
        reward += (self._prev_pad_dist - curr_pad_dist) * 0.01
        self._prev_pad_dist = curr_pad_dist

        # ------------------------------
        # 2. Vertical speed control
        # ------------------------------
        # Encourage reducing vertical speed magnitude (avoid freefall).
        abs_vy = abs(self.rocket.vy)
        reward += (self._prev_abs_vy - abs_vy) * 0.05
        self._prev_abs_vy = abs_vy

        # ------------------------------
        # 3. Total speed control
        # ------------------------------
        # Encourage reducing total speed (both vx and vy).
        speed = self.rocket.get_speed()
        reward += (self._prev_speed - speed) * 0.02
        self._prev_speed = speed

        # ------------------------------
        # 4. Stability penalties
        # ------------------------------
        # Penalize sideways velocity (keep rocket near vertical path).
        reward -= abs(self.rocket.vx) * 0.02

        # Penalize tilt away from vertical (keep rocket upright).
        reward -= min(abs(self.rocket.angle), math.pi) * 0.5

        # ------------------------------
        # 5. Efficiency penalties
        # ------------------------------
        # Small negative reward every step to encourage faster landing.
        reward -= 0.01

        # Penalize fuel usage (slightly), so the agent learns to be efficient.
        fuel_used = max(0.0, self._prev_fuel - self.rocket.fuel_mass)
        reward -= fuel_used * 0.001
        self._prev_fuel = self.rocket.fuel_mass

        # ------------------------------
        # 6. Terminal conditions
        # ------------------------------
        if self.rocket.landed:
            # Bonus based on landing quality: soft, slow, upright.
            vx_ok = abs(self.rocket.vx) < 2.0
            vy_ok = abs(self.rocket.vy) < 2.0
            angle_ok = abs(self.rocket.angle) < 0.1

            quality = 0.0
            if vx_ok: quality += 0.33
            if vy_ok: quality += 0.33
            if angle_ok: quality += 0.34

            reward += 100 + 900.0 * quality  # big bonus for good landing

        if self.rocket.crashed:
            reward -= 1000.0  # heavy penalty for crashing

        return float(reward)

    def _calculate_reward_approach1(self):
        """
        Reward approach focusing on:
        1. Reward being closer to the ground.
        2. Penalize moving upward (farther from ground).
        3. Penalize horizontal motion.
        4. On ground contact, reward smoother vertical velocity (lower vy).
        5. Large reward for landing, smaller but significant penalty for crash.
        """
        reward = 0.0

        # 1. Reward being closer to the ground (y=0)
        reward += (1000.0 - self.rocket.y) * 0.01  # the lower y is, the higher the reward

        # 2. Penalize moving upward (if vertical velocity is negative, i.e., going up)
        if self.rocket.vy < 0:
            reward -= abs(self.rocket.vy) * 0.1

        # 3. Penalize horizontal motion (vx)
        reward -= abs(self.rocket.vx) * 0.05

        # 4. On ground contact (landed), reward smoother vertical velocity (lower vy magnitude)
        if self.rocket.landed:
            reward += max(0, 10 - abs(self.rocket.vy))  # smoother (lower vy) gets higher reward

        # 5. Large reward for landing, smaller but significant penalty for crash
        if self.rocket.landed:
            reward += 500.0  # big reward for landing
        if self.rocket.crashed:
            reward -= 300.0  # penalty for crash

        return float(reward)