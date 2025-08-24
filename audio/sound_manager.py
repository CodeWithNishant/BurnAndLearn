"""
Audio management system for the rocket simulation.
Handles all sound effects and audio state management.
"""

import pygame
from typing import Dict, Any, Optional
from config import AudioConfig


class SoundManager:
    """Manages all audio for the rocket simulation."""
    
    def __init__(self):
        self.enabled = AudioConfig.ENABLED
        self.sounds = {}
        self.channels = {}
        
        # Audio state tracking
        self.engine_sound_playing = False
        self.rcs_sound_playing = False
        
        if self.enabled:
            self._initialize_audio()
    
    def _initialize_audio(self):
        """Initialize pygame audio and load sound files."""
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            
            # Load sound files
            self.sounds = {
                'engine': pygame.mixer.Sound(AudioConfig.ENGINE_SOUND),
                'rcs': pygame.mixer.Sound(AudioConfig.RCS_SOUND),
                'explosion': pygame.mixer.Sound(AudioConfig.EXPLOSION_SOUND),
                'success': pygame.mixer.Sound(AudioConfig.SUCCESS_SOUND)
            }
            
            # Set volumes
            self.sounds['engine'].set_volume(AudioConfig.ENGINE_BASE_VOLUME)
            self.sounds['rcs'].set_volume(AudioConfig.RCS_VOLUME)
            self.sounds['explosion'].set_volume(AudioConfig.EXPLOSION_VOLUME)
            self.sounds['success'].set_volume(AudioConfig.SUCCESS_VOLUME)
            
            print("Audio system initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize audio: {e}")
            self.enabled = False
    
    def handle_events(self, events: Dict[str, Any]):
        """Handle audio events from the physics system."""
        if not self.enabled:
            return
        
        # Engine sound management
        if 'engine_state_changed' in events:
            engine_data = events['engine_state_changed']
            if engine_data['active']:
                self._start_engine_sound(engine_data['throttle'])
            else:
                self._stop_engine_sound()
        
        # RCS sound management
        if 'rcs_active' in events:
            if events['rcs_active']:
                self._start_rcs_sound()
            else:
                self._stop_rcs_sound()
        
        # Landing sounds
        if 'landing_success' in events:
            self._stop_all_sounds()
            self._play_sound('success')
        
        if 'landing_crash' in events:
            self._stop_all_sounds()
            self._play_sound('explosion')
    
    def _start_engine_sound(self, throttle_percentage: float):
        """Start or update engine sound."""
        if not self.engine_sound_playing:
            self.channels['engine'] = self.sounds['engine'].play(-1)  # Loop
            self.engine_sound_playing = True
        
        # Update volume based on throttle
        if self.channels.get('engine'):
            volume = (AudioConfig.ENGINE_BASE_VOLUME + 
                     (throttle_percentage * 
                      (AudioConfig.ENGINE_MAX_VOLUME - AudioConfig.ENGINE_BASE_VOLUME)))
            self.channels['engine'].set_volume(volume)
    
    def _stop_engine_sound(self):
        """Stop engine sound."""
        if self.engine_sound_playing and self.channels.get('engine'):
            self.channels['engine'].stop()
            self.engine_sound_playing = False
    
    def _start_rcs_sound(self):
        """Start RCS sound if not already playing."""
        if not self.rcs_sound_playing:
            self.channels['rcs'] = self.sounds['rcs'].play(-1)  # Loop
            self.rcs_sound_playing = True
    
    def _stop_rcs_sound(self):
        """Stop RCS sound."""
        if self.rcs_sound_playing and self.channels.get('rcs'):
            self.channels['rcs'].stop()
            self.rcs_sound_playing = False
    
    def _play_sound(self, sound_name: str):
        """Play a one-shot sound effect."""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
    
    def _stop_all_sounds(self):
        """Stop all currently playing sounds."""
        self._stop_engine_sound()
        self._stop_rcs_sound()
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.enabled:
            self._stop_all_sounds()
            pygame.mixer.quit()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable audio."""
        if not enabled and self.enabled:
            self._stop_all_sounds()
        self.enabled = enabled