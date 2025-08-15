"""
Configuration constants for the rocket physics simulation.
All game constants are centralized here for easy modification.
"""

# Display Settings
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 800
FPS = 60
SCALE = 2.0  # pixels per meter

# Colors
BG_COLOR = (10, 10, 30)
ROCKET_COLOR = (220, 220, 220)
FLAME_COLOR = (255, 150, 0)
TEXT_COLOR = (255, 255, 255)
SUCCESS_COLOR = (0, 255, 0)
FAIL_COLOR = (255, 0, 0)
GROUND_COLOR = (100, 100, 100)
STAR_COLOR = (100, 100, 150)

# Physics Constants
class PhysicsConfig:
    MOON_GRAVITY = 1.62      # Moon's gravity m/s^2
    EARTH_GRAVITY = 9.81     # Earth's gravity m/s^2
    CURRENT_GRAVITY = EARTH_GRAVITY  # Change this to switch planets
    
    SAFE_LANDING_SPEED = 5.0   # m/s (safe landing speed)
    SAFE_LANDING_ANGLE = 0.2   # Radians (~11.5 degrees)
    LANDING_PAD_RANGE = 50     # meters (±50m from center)
    
    # Damping factors
    ANGULAR_DAMPING = 0.98
    ATMOSPHERIC_DRAG = 0.999

# Rocket Configuration
class RocketConfig:
    WIDTH = 4           # meters
    HEIGHT = 25         # meters
    DRY_MASS = 5000    # kg (empty rocket mass)
    FUEL_CAPACITY = 15000  # kg (maximum fuel mass)
    
    # Engine specifications
    MAIN_ENGINE_THRUST = 300000  # N (main engine thrust)
    RCS_THRUST = 1000           # N (RCS thrusters thrust)
    FUEL_CONSUMPTION_RATE = 85.0  # kg/s (fuel consumption at 100% throttle)
    MOMENT_OF_INERTIA = 50000    # kg⋅m² (rotational inertia)
    
    # Engine control
    MIN_ENGINE_PERCENTAGE = 0.3  # Minimum throttle setting
    ENGINE_INCREASE_RATE = 1.5   # Per second
    ENGINE_DECREASE_RATE = 2.0   # Per second
    
    # Starting conditions
    START_X = 0
    START_Y = 500
    START_FUEL = FUEL_CAPACITY

# Audio Configuration
class AudioConfig:
    ENABLED = True
    ENGINE_BASE_VOLUME = 0.3
    ENGINE_MAX_VOLUME = 0.8
    RCS_VOLUME = 0.5
    EXPLOSION_VOLUME = 0.5
    SUCCESS_VOLUME = 0.5
    
    # Sound file paths
    ENGINE_SOUND = "sound_files/rocket_engine_sound.mp3"
    RCS_SOUND = "sound_files/rocket_rcs_sound.mp3"
    EXPLOSION_SOUND = "sound_files/rocket_crash_sound.mp3"
    SUCCESS_SOUND = "sound_files/rocket_success_landing_sound.mp3"

# Camera Configuration
class CameraConfig:
    FOLLOW_SMOOTHNESS = 0.05  # Lower = smoother, higher = more responsive
    Y_OFFSET = -100          # Camera looks ahead in Y direction

# UI Configuration
class UIConfig:
    INFO_PANEL_X = 10
    INFO_PANEL_Y = 10
    INFO_LINE_HEIGHT = 25
    FONT_SIZE = 22
    BIG_FONT_SIZE = 48
    
    FUEL_DISPLAY_X_OFFSET = 200  # From right edge
    WARNING_TEXT_Y = 35
    
    # Star field
    STAR_COUNT = 100
    STAR_RADIUS = 1