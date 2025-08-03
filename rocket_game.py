import pygame
import math
import random

# --- INIT ---
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.init()
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Burn & Learn - Realistic Physics")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)
big_font = pygame.font.SysFont("Arial", 48, bold=True)

# --- SOUND EFFECTS ---
try:
    engine_sound = pygame.mixer.Sound("rocket_engine_sound.mp3")
    engine_sound.set_volume(1)

    rcs_sound = pygame.mixer.Sound("rocket_rcs_sound.mp3")
    rcs_sound.set_volume(0.5)
    
    explosion_sound = pygame.mixer.Sound("rocket_crash_sound.mp3")
    explosion_sound.set_volume(0.5)
    
    success_sound = pygame.mixer.Sound("rocket_success_landing_sound.mp3")
    success_sound.set_volume(0.5)
    
    SOUNDS_ENABLED = True
except:
    # If sound files don't exist, disable sounds
    SOUNDS_ENABLED = False
    print("Sound files not found - running without audio")

# --- CONSTANTS & COLORS ---
# World Physics
MOON_GRAVITY = 1.62      # Moon's gravity m/s^2
EARTH_GRAVITY = 9.81    # Earth's gravity m/s^2
SAFE_LANDING_SPEED = 5.0 # m/s (safe landing speed)
SAFE_LANDING_ANGLE = 0.2  # Radians (~11.5 degrees)

# Visuals
SCALE = 2.0          # pixels per meter
BG_COLOR = (10, 10, 30)
ROCKET_COLOR = (220, 220, 220)
FLAME_COLOR = (255, 150, 0)
TEXT_COLOR = (255, 255, 255)
SUCCESS_COLOR = (0, 255, 0)
FAIL_COLOR = (255, 0, 0)

# REALISTIC ROCKET CONSTANTS (SpaceX-inspired values)
ROCKET_WIDTH = 4   # meters
ROCKET_HEIGHT = 25 # meters
DRY_MASS = 5000  # kg (empty rocket mass)
FUEL_CAPACITY = 15000  # kg (maximum fuel mass)
MAIN_ENGINE_THRUST = 300000  # N (main engine thrust)
RCS_THRUST = 1000  # N (RCS thrusters thrust)
FUEL_CONSUMPTION_RATE = 85.0  # kg/s (fuel consumption at 100% throttle)
MOMENT_OF_INERTIA = 50000  # kg⋅m² (rotational inertia)

# --- ROCKET CLASS ---
class Rocket:
    def __init__(self, x, y):
        # Position and velocity are in world units (meters)
        self.x = x
        self.y = y
        self.vx = 0.0  # Horizontal velocity in m/s
        self.vy = 0.0  # Vertical velocity in m/s
        # Angle is in radians (0 is pointing up)
        self.angle = 0  # Start pointing straight up
        self.angular_velocity = 0  # rad/s
        self.width = ROCKET_WIDTH   # meters
        self.height = ROCKET_HEIGHT # meters
        self.fuel_mass = FUEL_CAPACITY  # Start with full fuel
        self.landed = False
        self.crashed = False
        self.message = ""
        self.engine_percentage = 0.3  # 0.3 to 1.0, controls main engine power
        self.main_thruster_on = False
        self.left_thruster_on = False
        self.right_thruster_on = False
        
        # Sound management
        self.engine_channel = None
        self.rcs_channel = None
        self.engine_sound_playing = False
        self.rcs_sound_playing = False

    def get_total_mass(self):
        """Calculate current total mass (dry mass + remaining fuel)"""
        return DRY_MASS + self.fuel_mass

    def get_thrust_to_weight_ratio(self):
        """Calculate current thrust-to-weight ratio"""
        weight = self.get_total_mass() * EARTH_GRAVITY
        max_thrust = MAIN_ENGINE_THRUST
        return max_thrust / weight

    def apply_physics(self, keys, dt):
        if self.landed or self.crashed:
            return
        
        # Reset thruster states
        self.left_thruster_on = False
        self.right_thruster_on = False
        
        # Get current mass
        current_mass = self.get_total_mass()
        
        # --- Engine Percentage Controls ---
        # Increase engine power (Up Arrow)
        if keys[pygame.K_UP]:
            self.main_thruster_on = True
            self.engine_percentage = min(1.0, self.engine_percentage + 1.5 * dt)
        
        # Decrease engine power (Down Arrow)
        if keys[pygame.K_DOWN] and self.main_thruster_on:
            self.engine_percentage = max(0.3, self.engine_percentage - 2.0 * dt)
        
        # Engine shutdown (O key)
        if keys[pygame.K_o]:
            self.main_thruster_on = False
            self.engine_percentage = 0.3  # Reset to minimum for next ignition

        # --- MAIN ENGINE PHYSICS ---
        if self.main_thruster_on and self.engine_percentage >= 0.3 and self.fuel_mass > 0:
            # Calculate actual thrust force
            thrust_force = MAIN_ENGINE_THRUST * self.engine_percentage
            
            # Apply thrust as acceleration (F = ma → a = F/m)
            thrust_acceleration_x = (math.sin(self.angle) * thrust_force) / current_mass
            thrust_acceleration_y = (math.cos(self.angle) * thrust_force) / current_mass
            
            # Update velocity based on thrust acceleration
            self.vx += thrust_acceleration_x * dt
            self.vy += thrust_acceleration_y * dt
            
            # Consume fuel
            fuel_consumed = FUEL_CONSUMPTION_RATE * self.engine_percentage * dt
            self.fuel_mass = max(0, self.fuel_mass - fuel_consumed)
            
            # Engine sound
            if SOUNDS_ENABLED and not self.engine_sound_playing:
                self.engine_channel = engine_sound.play(-1)  # Loop
                self.engine_sound_playing = True
            
            # Adjust engine volume based on throttle
            if SOUNDS_ENABLED and self.engine_channel:
                volume = 0.3 + (self.engine_percentage * 0.5)  # 30% to 80% volume
                self.engine_channel.set_volume(volume)
                
        else:
            self.main_thruster_on = False
            
            # Stop engine sound
            if SOUNDS_ENABLED and self.engine_sound_playing:
                if self.engine_channel:
                    self.engine_channel.stop()
                self.engine_sound_playing = False

        # --- RCS THRUSTER PHYSICS ---
        rcs_active = False
        
        if keys[pygame.K_LEFT] and self.fuel_mass > 0:
            # Apply torque for rotation (τ = I⋅α → α = τ/I)
            # Assume RCS thrusters are at distance of height/2 from center of mass
            torque_arm = self.height / 2
            torque = RCS_THRUST * torque_arm
            angular_acceleration = -torque / MOMENT_OF_INERTIA
            
            self.angular_velocity += angular_acceleration * dt
            self.fuel_mass = max(0, self.fuel_mass - FUEL_CONSUMPTION_RATE * 0.1 * dt)
            self.left_thruster_on = True
            rcs_active = True
            
        if keys[pygame.K_RIGHT] and self.fuel_mass > 0:
            torque_arm = self.height / 2
            torque = RCS_THRUST * torque_arm
            angular_acceleration = torque / MOMENT_OF_INERTIA
            
            self.angular_velocity += angular_acceleration * dt
            self.fuel_mass = max(0, self.fuel_mass - FUEL_CONSUMPTION_RATE * 0.1 * dt)
            self.right_thruster_on = True
            rcs_active = True

        # RCS sound management
        if SOUNDS_ENABLED:
            if rcs_active and not self.rcs_sound_playing:
                self.rcs_channel = rcs_sound.play(-1)  # Loop
                self.rcs_sound_playing = True
            elif not rcs_active and self.rcs_sound_playing:
                if self.rcs_channel:
                    self.rcs_channel.stop()
                self.rcs_sound_playing = False

        # --- GRAVITATIONAL PHYSICS ---
        # Apply gravity acceleration (always downward)
        gravity_acceleration = -EARTH_GRAVITY  # Negative because down is negative Y
        self.vy += gravity_acceleration * dt

        # --- UPDATE KINEMATICS ---
        # Update position based on velocity
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Update rotation
        self.angle += self.angular_velocity * dt
        
        # Apply damping
        self.angular_velocity *= 0.98  # Angular damping
        self.vx *= 0.999  # Very light atmospheric drag
        self.vy *= 0.999

        # --- COLLISION DETECTION ---
        # Check if bottom of rocket touches ground (rocket center - half height)
        rocket_bottom = self.y - (self.height / 2)
        if rocket_bottom <= 0:
            # Position rocket so its bottom is exactly on the ground
            self.y = self.height / 2
            self.check_landing()

    def check_landing(self):
        # Calculate total speed
        speed = math.sqrt(self.vx**2 + self.vy**2)
        
        # Check if rocket is within landing pad area (±50m from center)
        landing_pad_range = 50
        on_landing_pad = abs(self.x) <= landing_pad_range
        
        # Check landing conditions
        is_safe_speed = speed < SAFE_LANDING_SPEED
        is_upright = abs(self.angle) < SAFE_LANDING_ANGLE
        
        if is_safe_speed and is_upright and on_landing_pad:
            self.landed = True
            self.message = "LANDING SUCCESSFUL!"
            
            # Stop all sounds and play success sound
            if SOUNDS_ENABLED:
                if self.engine_channel:
                    self.engine_channel.stop()
                if self.rcs_channel:
                    self.rcs_channel.stop()
                success_sound.play()
                
        else:
            self.crashed = True
            reasons = []
            if not is_safe_speed: 
                reasons.append(f"High Speed ({speed:.1f} m/s)")
            if not is_upright: 
                reasons.append(f"Bad Angle ({abs(self.angle * 180/math.pi):.0f}°)")
            if not on_landing_pad:
                reasons.append("Missed Landing Pad")
            
            self.message = f"CRASHED: {', '.join(reasons)}"
            
            # Stop all sounds and play explosion sound
            if SOUNDS_ENABLED:
                if self.engine_channel:
                    self.engine_channel.stop()
                if self.rcs_channel:
                    self.rcs_channel.stop()
                explosion_sound.play()
        
        # Stop all movement on impact
        self.vx, self.vy, self.angular_velocity = 0, 0, 0

    def draw(self, surface, camera_x, camera_y):
        # Convert world coordinates to screen coordinates
        screen_x = (self.x - camera_x) * SCALE + WIDTH / 2
        screen_y = HEIGHT - ((self.y - camera_y) * SCALE + HEIGHT / 2)

        # Create rocket polygon
        w = self.width * SCALE / 2
        h = self.height * SCALE / 2
        points = [
            (0, -h),      # Nose cone
            (w, h),       # Bottom right
            (w/2, h*0.8), # Inner bottom right
            (-w/2, h*0.8),# Inner bottom left
            (-w, h)       # Bottom left
        ]

        # Rotate points
        rotated_points = []
        for x, y in points:
            new_x = x * math.cos(self.angle) - y * math.sin(self.angle)
            new_y = x * math.sin(self.angle) + y * math.cos(self.angle)
            rotated_points.append((new_x + screen_x, new_y + screen_y))
        
        # Draw rocket body
        pygame.draw.polygon(surface, ROCKET_COLOR, rotated_points)
        
        # Draw main engine flame
        if self.main_thruster_on and self.engine_percentage >= 0.3:
            flame_intensity = self.engine_percentage
            flame_h = h * (0.5 + flame_intensity * 0.8 + random.random() * 0.3 * flame_intensity)
            flame_w = w * (0.4 + flame_intensity * 0.4 + random.random() * 0.2 * flame_intensity)
            flame_points = [
                (-flame_w/2, h*0.8),
                (flame_w/2, h*0.8),
                (0, h + flame_h)
            ]
            rotated_flame_points = []
            for x, y in flame_points:
                new_x = x * math.cos(self.angle) - y * math.sin(self.angle)
                new_y = x * math.sin(self.angle) + y * math.cos(self.angle)
                rotated_flame_points.append((new_x + screen_x, new_y + screen_y))
            
            # Flame color based on intensity
            if flame_intensity > 0.8:
                flame_colors = [(255, 255, 150), (255, 200, 100), (255, 150, 0)]
            elif flame_intensity > 0.5:
                flame_colors = [(255, 200, 50), (255, 150, 0), (255, 100, 0)]
            else:
                flame_colors = [(255, 100, 0), (200, 80, 0), (150, 60, 0)]
            
            pygame.draw.polygon(surface, random.choice(flame_colors), rotated_flame_points)
        
        # Draw RCS thruster flames
        if self.left_thruster_on:
            flame_points = [(w*0.8, 0), (w + 15, -5), (w + 15, 5)]
            rotated_flame_points = []
            for x, y in flame_points:
                new_x = x * math.cos(self.angle) - y * math.sin(self.angle)
                new_y = x * math.sin(self.angle) + y * math.cos(self.angle)
                rotated_flame_points.append((new_x + screen_x, new_y + screen_y))
            pygame.draw.polygon(surface, (100, 150, 255), rotated_flame_points)
            
        if self.right_thruster_on:
            flame_points = [(-w*0.8, 0), (-w - 15, -5), (-w - 15, 5)]
            rotated_flame_points = []
            for x, y in flame_points:
                new_x = x * math.cos(self.angle) - y * math.sin(self.angle)
                new_y = x * math.sin(self.angle) + y * math.cos(self.angle)
                rotated_flame_points.append((new_x + screen_x, new_y + screen_y))
            pygame.draw.polygon(surface, (100, 150, 255), rotated_flame_points)

# --- HELPER FUNCTIONS ---
def draw_info(rocket):
    speed = math.sqrt(rocket.vx**2 + rocket.vy**2)
    
    # Basic flight info
    alt_text = font.render(f"Altitude: {max(0, rocket.y-ROCKET_HEIGHT/2):.1f} m", True, TEXT_COLOR)
    speed_text = font.render(f"Speed: {speed:.2f} m/s", True, SUCCESS_COLOR if speed < SAFE_LANDING_SPEED else FAIL_COLOR)
    v_speed_text = font.render(f"V-Speed: {rocket.vy:.2f} m/s", True, SUCCESS_COLOR if abs(rocket.vy) < SAFE_LANDING_SPEED else FAIL_COLOR)
    h_speed_text = font.render(f"H-Speed: {rocket.vx:.2f} m/s", True, SUCCESS_COLOR if abs(rocket.vx) < SAFE_LANDING_SPEED else FAIL_COLOR)
    angle_text = font.render(f"Angle: {(rocket.angle * 180/math.pi):.1f}°", True, SUCCESS_COLOR if abs(rocket.angle) < SAFE_LANDING_ANGLE else FAIL_COLOR)
    
    # Engine and fuel info
    engine_text = font.render(f"Engine: {int(rocket.engine_percentage * 100)}%", True, 
                             SUCCESS_COLOR if rocket.engine_percentage < 0.8 else (255, 255, 0) if rocket.engine_percentage < 1.0 else FAIL_COLOR)
    fuel_text = font.render(f"Fuel: {int(rocket.fuel_mass)} kg", True, (255, 255, 0) if rocket.fuel_mass > 1000 else FAIL_COLOR)
    
    # Physics info
    mass_text = font.render(f"Mass: {int(rocket.get_total_mass())} kg", True, TEXT_COLOR)
    twr_text = font.render(f"TWR: {rocket.get_thrust_to_weight_ratio():.2f}", True, 
                          SUCCESS_COLOR if rocket.get_thrust_to_weight_ratio() > 1.0 else FAIL_COLOR)
    
    # Position info
    pos_text = font.render(f"Position: ({rocket.x:.1f}, {rocket.y:.1f})", True, TEXT_COLOR)

    # Display all info
    info_items = [alt_text, speed_text, v_speed_text, h_speed_text, angle_text, 
                  engine_text, mass_text, twr_text, pos_text]
    
    for i, item in enumerate(info_items):
        screen.blit(item, (10, 10 + i * 25))
    
    screen.blit(fuel_text, (WIDTH - 200, 10))

    # Critical warnings
    if not rocket.main_thruster_on:
        engine_off_text = font.render("ENGINE OFF", True, FAIL_COLOR)
        screen.blit(engine_off_text, (WIDTH/2-60, 35))
    
    if rocket.fuel_mass <= 0:
        no_fuel_text = font.render("NO FUEL", True, FAIL_COLOR)
        screen.blit(no_fuel_text, (WIDTH/2-40, 60))
    
    # Controls info
    # controls = [
    #     "UP: Increase Engine Power",
    #     "DOWN: Decrease Engine Power", 
    #     "LEFT/RIGHT: Rotate",
    #     "O: Engine Shutdown",
    #     "R: Restart"
    # ]
    # for i, control in enumerate(controls):
    #     control_text = font.render(control, True, (150, 150, 150))
    #     screen.blit(control_text, (WIDTH - 350, 40 + i * 25))

def draw_ground(camera_x, camera_y):
    ground_y = HEIGHT - ((-camera_y) * SCALE + HEIGHT / 2)
    
    if ground_y > 0 and ground_y < HEIGHT + 100:
        # Draw ground line
        pygame.draw.line(screen, (100, 100, 100), (0, ground_y), (WIDTH, ground_y), 2)
        
        # Landing pad
        pad_center_x = (-camera_x) * SCALE + WIDTH / 2
        pad_width = 100 * SCALE
        
        pygame.draw.line(screen, SUCCESS_COLOR, 
                        (pad_center_x - pad_width/2, ground_y), 
                        (pad_center_x + pad_width/2, ground_y), 8)
        
        # Landing pad markers
        for i in range(-1, 2):
            marker_x = pad_center_x + i * pad_width/4
            pygame.draw.line(screen, SUCCESS_COLOR,
                           (marker_x, ground_y - 10),
                           (marker_x, ground_y + 10), 3)

def draw_end_message(rocket, timer):
    color = SUCCESS_COLOR if rocket.landed else FAIL_COLOR
    message_surf = big_font.render(rocket.message, True, color)
    message_rect = message_surf.get_rect(center=(WIDTH/2, HEIGHT/2 - 50))
    
    restart_surf = font.render("Press 'R' to Restart", True, TEXT_COLOR)
    restart_rect = restart_surf.get_rect(center=(WIDTH/2, HEIGHT/2 + 120))

    # Critical information
    fuel_used = FUEL_CAPACITY - rocket.fuel_mass
    fuel_info = font.render(f"Fuel Used: {fuel_used:.1f} kg", True, TEXT_COLOR)
    time_info = font.render(f"Time: {timer:.1f} seconds", True, TEXT_COLOR)

    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    screen.blit(message_surf, message_rect)
    screen.blit(restart_surf, restart_rect)
    screen.blit(fuel_info, (WIDTH/2 - 100, HEIGHT/2 + 20))
    screen.blit(time_info, (WIDTH/2 - 100, HEIGHT/2 + 60))

# --- GAME LOOP ---
def main():
    timer = 0
    running = True
    rocket = Rocket(x=0, y=500)

    camera_x = rocket.x
    camera_y = rocket.y
    
    while running:
        dt = clock.tick(60) / 1000.0
        if not rocket.landed and not rocket.crashed:
            timer += dt

        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    rocket = Rocket(x=0, y=500)
                    camera_x = rocket.x
                    camera_y = rocket.y

        rocket.apply_physics(keys, dt)

        # Smooth camera following
        target_camera_x = rocket.x
        target_camera_y = rocket.y - 100
        
        camera_x += (target_camera_x - camera_x) * 0.05
        camera_y += (target_camera_y - camera_y) * 0.05

        # Drawing
        screen.fill(BG_COLOR)
        
        # Stars
        for i in range(100):
            star_x = (i * 137) % WIDTH
            star_y = (i * 149) % (HEIGHT - 100)
            pygame.draw.circle(screen, (100, 100, 150), (star_x, star_y), 1)
        
        draw_ground(camera_x, camera_y)
        rocket.draw(screen, camera_x, camera_y)
        draw_info(rocket)
        
        if rocket.landed or rocket.crashed:
            draw_end_message(rocket, timer)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()