#!/usr/bin/env python3
"""
Vibe Wolf (Python + PyOpenGL) — GL-renderer
-------------------------------------------
Denne varianten beholder logikken (kart, DDA-raycasting, input, sprites),
men tegner ALT med OpenGL (GPU). Vegger og sprites blir teksturerte quads,
og vi bruker depth-test i GPU for korrekt okklusjon (ingen CPU zbuffer).

Avhengigheter:
  - pygame >= 2.1 (for vindu/input)
  - PyOpenGL, PyOpenGL-accelerate
  - numpy

Kjør:
  python wolfie3d_gl.py

Taster:
  - WASD / piltaster: bevegelse
  - Q/E eller ← → : rotasjon
  - SPACE / venstre mus: skyte
  - ESC: avslutt
"""

from __future__ import annotations

import math
import random
import sys
import time
from typing import TYPE_CHECKING

import numpy as np
import pygame
from OpenGL import GL as gl
from pathlib import Path

if TYPE_CHECKING:  # kun for typing hints
    from collections.abc import Sequence

# ---------- Konfig ----------
WIDTH, HEIGHT = 1024, 600
HALF_W, HALF_H = WIDTH // 2, HEIGHT // 2
FPS = 60

# Kamera/FOV
FOV = 66 * math.pi / 180.0
PLANE_LEN = math.tan(FOV / 2)

# Bevegelse
MOVE_SPEED = 3.0      # enheter/sek
ROT_SPEED = 2.0       # rad/sek
STRAFE_SPEED = 2.5

# Tekstur-størrelse brukt på GPU (proseduralt generert)
TEX_W = TEX_H = 256

# Depth mapping (lineær til [0..1] for gl_FragDepth)
FAR_PLANE = 100.0

# ---------- Audio System ----------
MUSIC_VOLUME = 0.7  # Background music volume (0.0 to 1.0)
SOUND_VOLUME = 0.8  # Sound effects volume (0.0 to 1.0)

def init_audio() -> None:
    """Initialize pygame mixer for audio playback."""
    try:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(8)  # Allow multiple sound effects
        print("🔊 Audio system initialized")
    except pygame.error as e:
        print(f"⚠️  Audio initialization failed: {e}")

def load_background_music() -> None:
    """Load and start playing background music."""
    try:
        music_path = Path("assets/sounds/background_music.wav")
        if music_path.exists():
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            print(f"🎵 Background music loaded: {music_path}")
        else:
            print(f"⚠️  Background music not found: {music_path}")
    except pygame.error as e:
        print(f"⚠️  Failed to load background music: {e}")

def stop_background_music() -> None:
    """Stop background music playback."""
    pygame.mixer.music.stop()

def set_music_volume(volume: float) -> None:
    """Set background music volume (0.0 to 1.0)."""
    global MUSIC_VOLUME
    MUSIC_VOLUME = max(0.0, min(1.0, volume))
    pygame.mixer.music.set_volume(MUSIC_VOLUME)

# Sound effects storage
sound_effects: dict[str, pygame.mixer.Sound] = {}

def load_sound_effects() -> None:
    """Load all sound effects."""
    global sound_effects
    sounds_dir = Path("assets/sounds")

    sound_files = {
        "gunshot": "gunshot.wav",
        "empty_click": "empty_click.wav",
        "bullet_impact": "bullet_impact.wav",
        "enemy_death": "enemy_death.wav",
        "ammo_pickup": "ammo_pickup.wav",
        "footstep": "footstep.wav",
        "wave_start": "wave_start.wav",
        "wave_complete": "wave_complete.wav",
    }

    for sound_name, filename in sound_files.items():
        sound_path = sounds_dir / filename
        try:
            if sound_path.exists():
                sound_effects[sound_name] = pygame.mixer.Sound(str(sound_path))
                sound_effects[sound_name].set_volume(SOUND_VOLUME)
                print(f"🔊 Loaded sound: {sound_name}")
            else:
                print(f"⚠️  Sound file not found: {sound_path}")
        except pygame.error as e:
            print(f"⚠️  Failed to load sound {sound_name}: {e}")

def play_sound(sound_name: str, volume_multiplier: float = 1.0) -> None:
    """Play a sound effect."""
    if sound_name in sound_effects:
        try:
            sound = sound_effects[sound_name]
            sound.set_volume(SOUND_VOLUME * volume_multiplier)
            sound.play()
        except pygame.error as e:
            print(f"⚠️  Failed to play sound {sound_name}: {e}")

def set_sound_volume(volume: float) -> None:
    """Set sound effects volume (0.0 to 1.0)."""
    global SOUND_VOLUME
    SOUND_VOLUME = max(0.0, min(1.0, volume))
    for sound in sound_effects.values():
        sound.set_volume(SOUND_VOLUME)

# Kart (0=tomt, >0=veggtype/tekstur-id)
MAP: list[list[int]] = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,2,0,0,0,0,0,0,0,0,3,0,0,0,0,0,4,0,1],
    [1,0,2,0,0,0,0,0,0,0,0,3,0,0,0,0,0,4,0,1],
    [1,0,2,0,0,0,0,0,0,0,0,3,0,0,0,0,0,4,0,1],
    [1,0,2,0,0,0,0,0,0,0,0,3,0,0,0,0,0,4,0,1],
    [1,0,2,0,0,0,0,0,0,0,0,3,0,0,0,0,0,4,0,1],
    [1,0,2,0,0,0,0,0,0,0,0,3,0,0,0,0,0,4,0,1],
    [1,0,2,0,0,0,0,0,0,0,0,3,0,0,0,0,0,4,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,2,2,2,2,2,0,0,0,0,3,3,3,0,0,4,4,4,1],
    [1,0,0,0,0,0,2,0,0,0,0,3,0,0,0,0,4,0,0,1],
    [1,0,0,0,0,0,2,0,0,0,0,3,0,0,0,0,0,0,0,1],  # Created entrance to the room in the lower right
    [1,0,0,0,0,0,2,0,0,0,0,3,0,0,0,0,4,0,0,1],
    [1,0,0,0,0,0,2,0,0,0,0,3,0,0,0,0,4,0,0,1],
    [1,0,0,0,0,0,2,0,0,0,0,3,0,0,0,0,4,0,0,1],
    [1,0,0,0,0,0,2,0,0,0,0,3,0,0,0,0,4,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]
MAP_W = len(MAP[0])
MAP_H = len(MAP)

# Startpos og retning
player_x = 3.5
player_y = 10.5
dir_x, dir_y = 1.0, 0.0
plane_x, plane_y = 0.0, PLANE_LEN
# Player ammo - limited resource that decreases when shooting
# The ammo count is displayed as a colored bar next to the weapon
# Green: > 10 ammo, Yellow: 6-10 ammo, Red: <= 5 ammo
player_ammo = 20  # Starting ammo count

# ---------- Hjelpere ----------
def in_map(ix: int, iy: int) -> bool:
    return 0 <= ix < MAP_W and 0 <= iy < MAP_H

def is_wall(ix: int, iy: int) -> bool:
    return in_map(ix, iy) and MAP[iy][ix] > 0

def clamp01(x: float) -> float:
    if x < 0.0: return 0.0
    if x > 1.0: return 1.0
    return x

# ---------- Prosjektil ----------
class Bullet:
    def __init__(self, x: float, y: float, vx: float, vy: float) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.alive = True
        self.age = 0.0
        self.height_param = 0.2  # 0..~0.65 (stiger visuelt)

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt
        if is_wall(int(nx), int(ny)):
            self.alive = False
            return
        self.x, self.y = nx, ny
        self.age += dt
        self.height_param = min(0.65, self.height_param + 0.35 * dt)

# ---------- Fiende ----------
class Enemy:
    def __init__(self, x: float, y: float, health: int = 1, speed_multiplier: float = 1.0) -> None:
        self.x = x
        self.y = y
        self.alive = True
        self.radius = 0.35     # kollisjon/hitbox i kart-enheter
        self.base_speed = 1.4  # base speed value
        self.speed = self.base_speed * speed_multiplier  # enheter/sek (enkel jakt)
        self.height_param = 0.5  # hvor høyt sprite sentreres i skjerm
        self.health = health   # number of hits the enemy can take

    def _try_move(self, nx: float, ny: float) -> None:
        # enkel vegg-kollisjon (sirkulær hitbox mot grid)
        # prøv X:
        if not is_wall(int(nx), int(self.y)):
            self.x = nx
        # prøv Y:
        if not is_wall(int(self.x), int(ny)):
            self.y = ny

    def take_damage(self, amount: int = 1) -> bool:
        """
        Reduce enemy health by the given amount.
        Returns True if the enemy died from this damage, False otherwise.
        """
        self.health -= amount
        if self.health <= 0:
            self.alive = False
            return True
        return False

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        # enkel "chase": gå mot spilleren, stopp om rett foran vegg
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy) + 1e-9
        # ikke gå helt oppå spilleren
        if dist > 0.75:
            ux, uy = dx / dist, dy / dist
            step = self.speed * dt
            self._try_move(self.x + ux * step, self.y + uy * step)


# ---------- Wave Manager ----------
class WaveManager:
    def __init__(self) -> None:
        self.current_wave = 0
        self.enemies_spawned = 0
        self.wave_in_progress = False
        self.between_waves = False
        self.wave_start_time = 0.0
        self.wave_countdown = 0.0
        self.countdown_duration = 5.0  # seconds between waves

    def start_next_wave(self) -> None:
        """Start the next wave and reset wave state"""
        self.current_wave += 1
        self.enemies_spawned = 0
        self.wave_in_progress = True
        self.between_waves = False
        self.wave_start_time = time.time()
        print(f"Wave {self.current_wave} started!")

    def start_countdown(self) -> None:
        """Start countdown to next wave"""
        self.between_waves = True
        self.wave_in_progress = False
        self.wave_countdown = self.countdown_duration
        print(f"Next wave in {self.countdown_duration} seconds...")

    def update(self, dt: float, enemies: list[Enemy]) -> None:
        """Update wave state based on time and enemies"""
        # If between waves, update countdown
        if self.between_waves:
            self.wave_countdown -= dt
            if self.wave_countdown <= 0:
                self.start_next_wave()

        # If no wave in progress and not between waves, start first wave
        if not self.wave_in_progress and not self.between_waves:
            self.start_next_wave()

        # Check if all enemies are dead to end the wave
        if self.wave_in_progress and self.enemies_spawned > 0:
            alive_enemies = sum(1 for e in enemies if e.alive)
            if alive_enemies == 0:
                self.start_countdown()

    def get_enemies_for_wave(self) -> int:
        """Calculate how many enemies should be in the current wave"""
        # Base number of enemies plus additional enemies per wave
        return 3 + (self.current_wave - 1) * 2

    def get_enemy_health(self) -> int:
        """Calculate enemy health based on wave number"""
        # Increase health every 3 waves
        return 1 + (self.current_wave - 1) // 3

    def get_enemy_speed_multiplier(self) -> float:
        """Calculate enemy speed multiplier based on wave number"""
        # Gradually increase speed up to 2x
        return 1.0 + min(1.0, (self.current_wave - 1) * 0.1)

    def spawn_enemies(self, enemies: list[Enemy]) -> None:
        """Spawn enemies for the current wave"""
        if not self.wave_in_progress:
            return

        enemies_to_spawn = self.get_enemies_for_wave() - self.enemies_spawned
        if enemies_to_spawn <= 0:
            return

        health = self.get_enemy_health()
        speed_mult = self.get_enemy_speed_multiplier()

        for _ in range(enemies_to_spawn):
            x, y = find_random_valid_position()
            enemies.append(Enemy(x, y, health=health, speed_multiplier=speed_mult))
            self.enemies_spawned += 1

    def get_wave_info(self) -> tuple[int, float, bool]:
        """Return current wave info: wave number, countdown, between_waves flag"""
        return self.current_wave, self.wave_countdown, self.between_waves


# ---------- Ammo Box ----------
class AmmoBox:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.alive = True
        self.radius = 0.35     # kollisjon/hitbox i kart-enheter
        self.height_param = 0.3  # hvor høyt sprite sentreres i skjerm (lower than enemies)
        self.pickup_distance = 0.8  # distance at which player can pick up the ammo box

    def update(self, dt: float) -> None:
        """Check if player is close enough to pick up the ammo box"""
        if not self.alive:
            return

        # Calculate distance to player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)

        # If player is close enough, reload ammo and mark as not alive
        if dist <= self.pickup_distance:
            global player_ammo
            player_ammo = 20  # Reload ammo to 100% (20 bullets)
            self.alive = False
            print("Ammo reloaded to 100%!")


# ---------- Prosedural tekstur (pygame.Surface) ----------
def make_brick_texture() -> pygame.Surface:
    surf = pygame.Surface((TEX_W, TEX_H))
    surf.fill((150, 40, 40))
    mortar = (200, 200, 200)
    brick_h = TEX_H // 4
    brick_w = TEX_W // 4
    for row in range(0, TEX_H, brick_h):
        offset = 0 if (row // brick_h) % 2 == 0 else brick_w // 2
        for col in range(0, TEX_W, brick_w):
            rect = pygame.Rect((col + offset) % TEX_W, row, brick_w - 1, brick_h - 1)
            pygame.draw.rect(surf, (165, 52, 52), rect)
    for y in range(0, TEX_H, brick_h):
        pygame.draw.line(surf, mortar, (0, y), (TEX_W, y))
    for x in range(0, TEX_W, brick_w):
        pygame.draw.line(surf, mortar, (x, 0), (x, TEX_H))
    return surf

def make_stone_texture() -> pygame.Surface:
    surf = pygame.Surface((TEX_W, TEX_H))
    base = (110, 110, 120)
    surf.fill(base)
    for y in range(TEX_H):
        for x in range(TEX_W):
            if ((x * 13 + y * 7) ^ (x * 3 - y * 5)) & 15 == 0:
                c = 90 + ((x * y) % 40)
                surf.set_at((x, y), (c, c, c))
    for i in range(5):
        pygame.draw.line(surf, (80, 80, 85), (i*12, 0), (TEX_W-1, TEX_H-1 - i*6), 1)
    return surf

def make_wood_texture() -> pygame.Surface:
    surf = pygame.Surface((TEX_W, TEX_H))
    for y in range(TEX_H):
        for x in range(TEX_W):
            v = int(120 + 40 * math.sin((x + y*0.5) * 0.12) + 20 * math.sin(y * 0.3))
            v = max(60, min(200, v))
            surf.set_at((x, y), (140, v, 60))
    for x in range(0, TEX_W, TEX_W // 4):
        pygame.draw.line(surf, (90, 60, 30), (x, 0), (x, TEX_H))
    return surf

def make_metal_texture() -> pygame.Surface:
    surf = pygame.Surface((TEX_W, TEX_H), pygame.SRCALPHA)
    base = (140, 145, 150, 255)
    surf.fill(base)
    for y in range(8, TEX_H, 16):
        for x in range(8, TEX_W, 16):
            pygame.draw.circle(surf, (90, 95, 100, 255), (x, y), 2)
    for y in range(TEX_H):
        shade = 130 + (y % 8) * 2
        pygame.draw.line(surf, (shade, shade, shade+5, 255), (0, y), (TEX_W, y), 1)
    return surf

def make_bullet_texture() -> pygame.Surface:
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 240, 150, 220), (16, 16), 8)
    pygame.draw.circle(surf, (255, 255, 255, 255), (13, 13), 3)
    return surf

def make_ammo_box_texture() -> pygame.Surface:
    """Create a texture for the ammo box - a military-style ammunition box"""
    surf = pygame.Surface((64, 64), pygame.SRCALPHA)

    # Draw the main box (olive green/khaki)
    box_rect = pygame.Rect(4, 4, 56, 56)
    pygame.draw.rect(surf, (102, 107, 72, 255), box_rect)  # Military olive green

    # Add box texture/pattern
    for y in range(6, 58, 4):
        # Horizontal texture lines (slightly darker)
        pygame.draw.line(surf, (90, 95, 65, 100), (6, y), (58, y))

    # Draw box outline (darker olive)
    pygame.draw.rect(surf, (80, 85, 55, 255), box_rect, 2)

    # Draw metal clasps/latches
    clasp_color = (150, 150, 140, 255)  # Metallic color
    # Left clasp
    pygame.draw.rect(surf, clasp_color, pygame.Rect(10, 25, 8, 14))
    pygame.draw.line(surf, (70, 70, 65, 255), (10, 32), (18, 32), 2)
    # Right clasp
    pygame.draw.rect(surf, clasp_color, pygame.Rect(46, 25, 8, 14))
    pygame.draw.line(surf, (70, 70, 65, 255), (46, 32), (54, 32), 2)

    # Draw handle on top
    handle_color = (60, 65, 45, 255)  # Dark handle color
    pygame.draw.rect(surf, handle_color, pygame.Rect(24, 8, 16, 6))
    pygame.draw.rect(surf, clasp_color, pygame.Rect(22, 10, 20, 2))  # Metal part

    # Add text "AMMO" to the box
    # Since we can't use fonts directly, we'll draw it with lines
    # A
    pygame.draw.line(surf, (30, 30, 25, 255), (20, 45), (24, 38), 2)
    pygame.draw.line(surf, (30, 30, 25, 255), (24, 38), (28, 45), 2)
    pygame.draw.line(surf, (30, 30, 25, 255), (22, 42), (26, 42), 1)
    # M
    pygame.draw.line(surf, (30, 30, 25, 255), (30, 38), (30, 45), 2)
    pygame.draw.line(surf, (30, 30, 25, 255), (30, 38), (33, 42), 1)
    pygame.draw.line(surf, (30, 30, 25, 255), (33, 42), (36, 38), 1)
    pygame.draw.line(surf, (30, 30, 25, 255), (36, 38), (36, 45), 2)
    # O
    pygame.draw.circle(surf, (30, 30, 25, 255), (44, 42), 4, 2)

    # Add weathering/scratches
    for _ in range(5):
        x = random.randint(8, 56)
        y = random.randint(8, 56)
        length = random.randint(3, 8)
        angle = random.random() * 6.28
        ex = x + int(math.cos(angle) * length)
        ey = y + int(math.sin(angle) * length)
        pygame.draw.line(surf, (120, 125, 90, 100), (x, y), (ex, ey), 1)

    # Add highlight on edges
    pygame.draw.line(surf, (130, 135, 100, 150), (6, 6), (40, 6), 1)
    pygame.draw.line(surf, (130, 135, 100, 150), (6, 6), (6, 40), 1)

    return surf

# ---------- OpenGL utils ----------
VS_SRC = """
#version 330 core
layout (location = 0) in vec2 in_pos;    // NDC -1..1
layout (location = 1) in vec2 in_uv;
layout (location = 2) in vec3 in_col;    // per-vertex farge (for dimming/overlay)
layout (location = 3) in float in_depth; // 0..1 depth (0 nær, 1 fjern)

out vec2 v_uv;
out vec3 v_col;
out float v_depth;

void main() {
    v_uv = in_uv;
    v_col = in_col;
    v_depth = in_depth;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

FS_SRC = """
#version 330 core
in vec2 v_uv;
in vec3 v_col;
in float v_depth;

out vec4 fragColor;

uniform sampler2D uTexture;
uniform bool uUseTexture;

void main() {
    vec4 base = vec4(1.0);
    if (uUseTexture) {
        base = texture(uTexture, v_uv);
        if (base.a < 0.01) discard; // alpha for sprites
    }
    vec3 rgb = base.rgb * v_col;
    fragColor = vec4(rgb, base.a);
    // Skriv eksplisitt dybde (lineær i [0..1])
    gl_FragDepth = clamp(v_depth, 0.0, 1.0);
}
"""

def compile_shader(src: str, stage: int) -> int:
    sid = gl.glCreateShader(stage)
    gl.glShaderSource(sid, src)
    gl.glCompileShader(sid)
    status = gl.glGetShaderiv(sid, gl.GL_COMPILE_STATUS)
    if status != gl.GL_TRUE:
        log = gl.glGetShaderInfoLog(sid).decode()
        raise RuntimeError(f"Shader compile error:\n{log}")
    return sid

def make_program(vs_src: str, fs_src: str) -> int:
    vs = compile_shader(vs_src, gl.GL_VERTEX_SHADER)
    fs = compile_shader(fs_src, gl.GL_FRAGMENT_SHADER)
    prog = gl.glCreateProgram()
    gl.glAttachShader(prog, vs)
    gl.glAttachShader(prog, fs)
    gl.glLinkProgram(prog)
    ok = gl.glGetProgramiv(prog, gl.GL_LINK_STATUS)
    gl.glDeleteShader(vs)
    gl.glDeleteShader(fs)
    if ok != gl.GL_TRUE:
        log = gl.glGetProgramInfoLog(prog).decode()
        raise RuntimeError(f"Program link error:\n{log}")
    return prog

def surface_to_texture(surf: pygame.Surface) -> int:
    """Laster pygame.Surface til GL_TEXTURE_2D (RGBA8). Returnerer texture id."""
    data = pygame.image.tostring(surf.convert_alpha(), "RGBA", True)
    w, h = surf.get_width(), surf.get_height()
    tid = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, tid)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
    return tid

def make_white_texture() -> int:
    surf = pygame.Surface((1, 1), pygame.SRCALPHA)
    surf.fill((255, 255, 255, 255))
    return surface_to_texture(surf)

def make_enemy_texture() -> pygame.Surface:
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    # kropp
    pygame.draw.rect(s, (60, 60, 70, 255), (100, 80, 56, 120), border_radius=6)
    # hode
    pygame.draw.circle(s, (220, 200, 180, 255), (128, 70), 26)
    # hjelm-ish
    pygame.draw.arc(s, (40, 40, 50, 255), (92, 40, 72, 40), 3.14, 0, 6)
    # “arm”
    pygame.draw.rect(s, (60, 60, 70, 255), (86, 110, 24, 16))
    pygame.draw.rect(s, (60, 60, 70, 255), (146, 110, 24, 16))
    return s


# ---------- GL Renderer state ----------
from pathlib import Path
import os
import pygame
from OpenGL import GL as gl

# ---------- GL Renderer state ----------
class GLRenderer:
    def __init__(self) -> None:
        # Shader program
        self.prog = make_program(VS_SRC, FS_SRC)
        gl.glUseProgram(self.prog)
        self.uni_tex = gl.glGetUniformLocation(self.prog, "uTexture")
        self.uni_use_tex = gl.glGetUniformLocation(self.prog, "uUseTexture")
        gl.glUniform1i(self.uni_tex, 0)

        # VAO/VBO (dynamisk buffer per draw)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)

        stride = 8 * 4  # 8 float32 per vertex
        # in_pos (loc 0): 2 floats
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(0))
        # in_uv (loc 1): 2 floats
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(2 * 4))
        # in_col (loc 2): 3 floats
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(4 * 4))
        # in_depth (loc 3): 1 float
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribPointer(3, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(7 * 4))

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

        # Teksturer
        self.white_tex = make_white_texture()
        self.textures: dict[int, int] = {}  # tex_id -> GL texture

        # Last fra assets hvis tilgjengelig, ellers fall tilbake til proseduralt
        self.load_textures()

        # GL state
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)

    # ---------- teksturhjelpere ----------
    @staticmethod
    def _scale_if_needed(surf: pygame.Surface, size: int = 512) -> pygame.Surface:
        if surf.get_width() != size or surf.get_height() != size:
            surf = pygame.transform.smoothscale(surf, (size, size))
        return surf

    def _load_texture_file(self, path: str, size: int = 512) -> int:
        surf = pygame.image.load(path).convert_alpha()
        surf = self._scale_if_needed(surf, size)
        return surface_to_texture(surf)

    # ---------- offentlig laster ----------

    def _resolve_textures_base(self) -> Path:
        """
        Finn korrekt assets/textures-katalog robust, uavhengig av hvor vi kjører fra.
        Prøver i rekkefølge:
          - <her>/assets/textures
          - <her>/../assets/textures
          - <her>/../../assets/textures      <-- typisk når koden ligger i src/wolfie3d
          - <cwd>/assets/textures
        """
        here = Path(__file__).resolve().parent
        candidates = [
            here / "assets" / "textures",
            here.parent / "assets" / "textures",
            here.parent.parent / "assets" / "textures",
            Path.cwd() / "assets" / "textures",
            ]
        print("\n[GLRenderer] Prøver å finne assets/textures på disse stedene:")
        for c in candidates:
            print("  -", c)
            if c.exists():
                print("[GLRenderer] FANT:", c)
                return c

        raise FileNotFoundError(
            "Fant ikke assets/textures i noen av kandidatkatalogene over. "
            "Opprett assets/textures på prosjektnivå (samme nivå som src) eller justér stien."
        )

    def load_textures(self) -> None:
        """
        Debug-variant som bruker korrekt prosjekt-rot og feiler høyt hvis filer mangler.
        Forventer: bricks.png, stone.png, wood.png, metal.png i assets/textures/.
        """
        base = self._resolve_textures_base()
        print(f"[GLRenderer] pygame extended image support: {pygame.image.get_extended()}")
        print(f"[GLRenderer] Innhold i {base}: {[p.name for p in base.glob('*')]}")

        files = {
            1: base / "bricks.png",
            2: base / "stone.png",
            3: base / "wood.png",
            4: base / "metal.png",
        }
        missing = [p for p in files.values() if not p.exists()]
        if missing:
            print("[GLRenderer] MANGEL: følgende filer finnes ikke:")
            for m in missing:
                print("  -", m)
            raise FileNotFoundError(
                "Manglende teksturer. Sørg for at filene ligger i assets/textures/")

        def _load(path: Path, size: int = 512) -> int:
            print(f"[GLRenderer] Laster: {path}")
            surf = pygame.image.load(str(path)).convert_alpha()
            if surf.get_width() != size or surf.get_height() != size:
                print(
                    f"[GLRenderer]  - rescale {surf.get_width()}x{surf.get_height()} -> {size}x{size}")
                surf = pygame.transform.smoothscale(surf, (size, size))
            tex_id = surface_to_texture(surf)
            print(f"[GLRenderer]  - OK (GL tex id {tex_id})")
            return tex_id

        self.textures[1] = _load(files[1], 512)
        self.textures[2] = _load(files[2], 512)
        self.textures[3] = _load(files[3], 512)
        self.textures[4] = _load(files[4], 512)

        # Sprite (kule) – behold prosedyre
        self.textures[99] = surface_to_texture(make_bullet_texture())

        # Enemy sprite (ID 200): prøv fil, ellers prosedyral placeholder
        try:
            sprites_dir = self._resolve_textures_base().parent / "sprites"
            enemy_path = sprites_dir / "enemy.png"
            print(f"[GLRenderer] Leter etter enemy sprite i: {enemy_path}")
            if enemy_path.exists():
                self.textures[200] = self._load_texture_file(enemy_path, 512)
                print(f"[GLRenderer] Enemy OK (GL tex id {self.textures[200]})")
            else:
                # fallback – prosedural fiende
                self.textures[200] = surface_to_texture(make_enemy_texture())
                print("[GLRenderer] Enemy: bruker prosedural sprite")
        except Exception as ex:
            print(f"[GLRenderer] Enemy: FEIL ved lasting ({ex}), bruker prosedural")
            self.textures[200] = surface_to_texture(make_enemy_texture())

        # Ammo box sprite (ID 201): procedurally generated
        self.textures[201] = surface_to_texture(make_ammo_box_texture())
        print(f"[GLRenderer] Ammo box OK (GL tex id {self.textures[201]})")

        print("[GLRenderer] Teksturer lastet.\n")

    # ---------- draw ----------
    def draw_arrays(self, verts: np.ndarray, texture: int, use_tex: bool) -> None:
        if verts.size == 0:
            return
        gl.glUseProgram(self.prog)
        gl.glUniform1i(self.uni_use_tex, 1 if use_tex else 0)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture if use_tex else self.white_tex)

        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_DYNAMIC_DRAW)
        count = verts.shape[0]
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, count)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

# ---------- Raycasting + bygg GL-verts ----------
def column_ndc(x: int) -> tuple[float, float]:
    """Returnerer venstre/høyre NDC-X for en 1-px bred skjermkolonne."""
    x_left = (2.0 * x) / WIDTH - 1.0
    x_right = (2.0 * (x + 1)) / WIDTH - 1.0
    return x_left, x_right

def y_ndc(y_pix: int) -> float:
    """Konverter skjerm-Y (0 top) til NDC-Y (1 top, -1 bunn)."""
    return 1.0 - 2.0 * (y_pix / float(HEIGHT))

def dim_for_side(side: int) -> float:
    # dim litt på sidevegger (liknende BLEND_MULT tidligere)
    return 0.78 if side == 1 else 1.0

def cast_and_build_wall_batches() -> dict[int, list[float]]:
    batches: dict[int, list[float]] = {1: [], 2: [], 3: [], 4: []}
    for x in range(WIDTH):
        # Raydir
        camera_x = 2.0 * x / WIDTH - 1.0
        ray_dir_x = dir_x + plane_x * camera_x
        ray_dir_y = dir_y + plane_y * camera_x
        map_x = int(player_x)
        map_y = int(player_y)

        delta_dist_x = abs(1.0 / ray_dir_x) if ray_dir_x != 0 else 1e30
        delta_dist_y = abs(1.0 / ray_dir_y) if ray_dir_y != 0 else 1e30

        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (player_x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - player_x) * delta_dist_x
        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (player_y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - player_y) * delta_dist_y

        hit = 0
        side = 0
        tex_id = 1
        while hit == 0:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
            if not in_map(map_x, map_y):
                hit = 1
                tex_id = 1
                break
            if MAP[map_y][map_x] > 0:
                hit = 1
                tex_id = MAP[map_y][map_x]

        if side == 0:
            perp_wall_dist = (map_x - player_x + (1 - step_x) / 2.0) / (ray_dir_x if ray_dir_x != 0 else 1e-9)
            wall_x = player_y + perp_wall_dist * ray_dir_y
        else:
            perp_wall_dist = (map_y - player_y + (1 - step_y) / 2.0) / (ray_dir_y if ray_dir_y != 0 else 1e-9)
            wall_x = player_x + perp_wall_dist * ray_dir_x

        wall_x -= math.floor(wall_x)
        # u-koordinat (kontinuerlig) + flip for samsvar med klassisk raycaster
        u = wall_x
        if (side == 0 and ray_dir_x > 0) or (side == 1 and ray_dir_y < 0):
            u = 1.0 - u

        # skjermhøyde på vegg
        line_height = int(HEIGHT / (perp_wall_dist + 1e-6))
        draw_start = max(0, -line_height // 2 + HALF_H)
        draw_end = min(HEIGHT - 1, line_height // 2 + HALF_H)

        # NDC koordinater for 1-px bred stripe
        x_left, x_right = column_ndc(x)
        top_ndc = y_ndc(draw_start)
        bot_ndc = y_ndc(draw_end)

        # Farge-dim (samme på hele kolonnen)
        c = dim_for_side(side)
        r = g = b = c

        # Depth som lineær [0..1] (0 = nærmest)
        depth = clamp01(perp_wall_dist / FAR_PLANE)

        # 2 triangler (6 vertikser). Vertex-layout:
        # [x, y, u, v, r, g, b, depth]
        v = [
            # tri 1
            x_left,  top_ndc, u, 0.0, r, g, b, depth,
            x_left,  bot_ndc, u, 1.0, r, g, b, depth,
            x_right, top_ndc, u, 0.0, r, g, b, depth,
            # tri 2
            x_right, top_ndc, u, 0.0, r, g, b, depth,
            x_left,  bot_ndc, u, 1.0, r, g, b, depth,
            x_right, bot_ndc, u, 1.0, r, g, b, depth,
        ]
        batches.setdefault(tex_id, []).extend(v)
    return batches

def build_fullscreen_background() -> np.ndarray:
    """To store quads (himmel/gulv), farget med vertex-color, tegnes uten tekstur."""
    # Himmel (øverst halvdel)
    sky_col = (40/255.0, 60/255.0, 90/255.0)
    floor_col = (35/255.0, 35/255.0, 35/255.0)
    verts: list[float] = []

    # Quad helper
    def add_quad(x0, y0, x1, y1, col):
        r, g, b = col
        depth = 1.0  # lengst bak
        # u,v er 0 (vi bruker hvit 1x1 tekstur)
        verts.extend([
            x0, y0, 0.0, 0.0, r, g, b, depth,
            x0, y1, 0.0, 1.0, r, g, b, depth,
            x1, y0, 1.0, 0.0, r, g, b, depth,

            x1, y0, 1.0, 0.0, r, g, b, depth,
            x0, y1, 0.0, 1.0, r, g, b, depth,
            x1, y1, 1.0, 1.0, r, g, b, depth,
        ])

    # Koordinater i NDC
    add_quad(-1.0,  1.0,  1.0,  0.0, sky_col)   # øvre halvdel
    add_quad(-1.0,  0.0,  1.0, -1.0, floor_col) # nedre halvdel
    return np.asarray(verts, dtype=np.float32).reshape((-1, 8))

def build_sprites_batch(bullets: list[Bullet]) -> np.ndarray:
    """Bygger ett quad per kule i skjermen (billboard), med depth."""
    verts: list[float] = []

    for b in bullets:
        # Transform til kamera-rom
        spr_x = b.x - player_x
        spr_y = b.y - player_y
        inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y + 1e-9)
        trans_x = inv_det * (dir_y * spr_x - dir_x * spr_y)
        trans_y = inv_det * (-plane_y * spr_x + plane_x * spr_y)
        if trans_y <= 0:
            continue  # bak kamera

        sprite_screen_x = int((WIDTH / 2) * (1 + trans_x / trans_y))

        sprite_h = abs(int(HEIGHT / trans_y))
        sprite_w = sprite_h  # kvadratisk

        # vertikal offset: "stiger"
        v_shift = int((0.5 - b.height_param) * sprite_h)
        draw_start_y = max(0, -sprite_h // 2 + HALF_H + v_shift)
        draw_end_y   = min(HEIGHT - 1, draw_start_y + sprite_h)
        # horisontal
        draw_start_x = -sprite_w // 2 + sprite_screen_x
        draw_end_x   = draw_start_x + sprite_w

        # Klipp utenfor skjerm
        if draw_end_x < 0 or draw_start_x >= WIDTH:
            continue
        draw_start_x = max(0, draw_start_x)
        draw_end_x   = min(WIDTH - 1, draw_end_x)

        # Konverter til NDC
        x0 = (2.0 * draw_start_x) / WIDTH - 1.0
        x1 = (2.0 * (draw_end_x + 1)) / WIDTH - 1.0
        y0 = y_ndc(draw_start_y)
        y1 = y_ndc(draw_end_y)

        # Depth (basert på trans_y)
        depth = clamp01(trans_y / FAR_PLANE)

        r = g = bcol = 1.0  # ingen ekstra farge-dim
        # u,v: full tekstur
        u0, v0 = 0.0, 0.0
        u1, v1 = 1.0, 1.0

        verts.extend([
            x0, y0, u0, v0, r, g, bcol, depth,
            x0, y1, u0, v1, r, g, bcol, depth,
            x1, y0, u1, v0, r, g, bcol, depth,

            x1, y0, u1, v0, r, g, bcol, depth,
            x0, y1, u0, v1, r, g, bcol, depth,
            x1, y1, u1, v1, r, g, bcol, depth,
        ])



    if not verts:
        return np.zeros((0, 8), dtype=np.float32)
    return np.asarray(verts, dtype=np.float32).reshape((-1, 8))

def build_enemies_batch(enemies: list['Enemy']) -> np.ndarray:
    verts: list[float] = []
    for e in enemies:
        if not e.alive:
            continue
        spr_x = e.x - player_x
        spr_y = e.y - player_y
        inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y + 1e-9)
        trans_x = inv_det * (dir_y * spr_x - dir_x * spr_y)
        trans_y = inv_det * (-plane_y * spr_x + plane_x * spr_y)
        if trans_y <= 0:
            continue

        sprite_screen_x = int((WIDTH / 2) * (1 + trans_x / trans_y))
        sprite_h = abs(int(HEIGHT / trans_y))
        sprite_w = sprite_h  # kvadratisk
        v_shift = int((0.5 - e.height_param) * sprite_h)

        draw_start_y = max(0, -sprite_h // 2 + HALF_H + v_shift)
        draw_end_y   = min(HEIGHT - 1, draw_start_y + sprite_h)
        draw_start_x = -sprite_w // 2 + sprite_screen_x
        draw_end_x   = draw_start_x + sprite_w
        if draw_end_x < 0 or draw_start_x >= WIDTH:
            continue

        draw_start_x = max(0, draw_start_x)
        draw_end_x   = min(WIDTH - 1, draw_end_x)

        x0 = (2.0 * draw_start_x) / WIDTH - 1.0
        x1 = (2.0 * (draw_end_x + 1)) / WIDTH - 1.0
        y0 = 1.0 - 2.0 * (draw_start_y / HEIGHT)
        y1 = 1.0 - 2.0 * (draw_end_y   / HEIGHT)

        depth = clamp01(trans_y / FAR_PLANE)
        r = g = b = 1.0

        ENEMY_V_FLIP = True  # sett False hvis den blir riktig uten flip
        if ENEMY_V_FLIP:
            u0, v0, u1, v1 = 0.0, 1.0, 1.0, 0.0
        else:
            u0, v0, u1, v1 = 0.0, 0.0, 1.0, 1.0

        verts.extend([
            x0, y0, u0, v0, r, g, b, depth,
            x0, y1, u0, v1, r, g, b, depth,
            x1, y0, u1, v0, r, g, b, depth,

            x1, y0, u1, v0, r, g, b, depth,
            x0, y1, u0, v1, r, g, b, depth,
            x1, y1, u1, v1, r, g, b, depth,
        ])

    if not verts:
        return np.zeros((0, 8), dtype=np.float32)
    return np.asarray(verts, dtype=np.float32).reshape((-1, 8))

def build_ammo_boxes_batch(ammo_boxes: list['AmmoBox']) -> np.ndarray:
    """Build rendering batch for ammo boxes, similar to enemies but with different texture"""
    verts: list[float] = []
    for box in ammo_boxes:
        if not box.alive:
            continue

        # Transform to camera space
        spr_x = box.x - player_x
        spr_y = box.y - player_y
        inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y + 1e-9)
        trans_x = inv_det * (dir_y * spr_x - dir_x * spr_y)
        trans_y = inv_det * (-plane_y * spr_x + plane_x * spr_y)
        if trans_y <= 0:
            continue  # behind camera

        # Calculate screen position
        sprite_screen_x = int((WIDTH / 2) * (1 + trans_x / trans_y))
        # Make ammo box smaller (50% of original size)
        sprite_h = abs(int((HEIGHT / trans_y) * 0.5))
        sprite_w = sprite_h  # square sprite

        # Vertical offset (lower than enemies)
        v_shift = int((0.5 - box.height_param) * sprite_h)

        # Calculate screen coordinates
        draw_start_y = max(0, -sprite_h // 2 + HALF_H + v_shift)
        draw_end_y   = min(HEIGHT - 1, draw_start_y + sprite_h)
        draw_start_x = -sprite_w // 2 + sprite_screen_x
        draw_end_x   = draw_start_x + sprite_w

        # Clip if outside screen
        if draw_end_x < 0 or draw_start_x >= WIDTH:
            continue

        draw_start_x = max(0, draw_start_x)
        draw_end_x   = min(WIDTH - 1, draw_end_x)

        # Convert to NDC
        x0 = (2.0 * draw_start_x) / WIDTH - 1.0
        x1 = (2.0 * (draw_end_x + 1)) / WIDTH - 1.0
        y0 = 1.0 - 2.0 * (draw_start_y / HEIGHT)
        y1 = 1.0 - 2.0 * (draw_end_y   / HEIGHT)

        # Depth based on distance
        depth = clamp01(trans_y / FAR_PLANE)

        # No color tint
        r = g = b = 1.0

        # Texture coordinates (no flip needed)
        u0, v0, u1, v1 = 0.0, 0.0, 1.0, 1.0

        # Add vertices for the quad
        verts.extend([
            x0, y0, u0, v0, r, g, b, depth,
            x0, y1, u0, v1, r, g, b, depth,
            x1, y0, u1, v0, r, g, b, depth,

            x1, y0, u1, v0, r, g, b, depth,
            x0, y1, u0, v1, r, g, b, depth,
            x1, y1, u1, v1, r, g, b, depth,
        ])

    if not verts:
        return np.zeros((0, 8), dtype=np.float32)
    return np.asarray(verts, dtype=np.float32).reshape((-1, 8))


def build_crosshair_quads(size_px: int = 8, thickness_px: int = 2) -> np.ndarray:
    """To små rektangler (horisontalt/vertikalt), sentrert i skjermen."""
    verts: list[float] = []

    def rect_ndc(cx, cy, w, h):
        x0 = (2.0 * (cx - w)) / WIDTH - 1.0
        x1 = (2.0 * (cx + w)) / WIDTH - 1.0
        y0 = 1.0 - 2.0 * ((cy - h) / HEIGHT)
        y1 = 1.0 - 2.0 * ((cy + h) / HEIGHT)
        return x0, y0, x1, y1

    r = g = b = 1.0
    depth = 0.0  # helt foran

    # horisontal strek
    x0, y0, x1, y1 = rect_ndc(HALF_W, HALF_H, size_px, thickness_px//2)
    verts.extend([
        x0, y0, 0.0, 0.0, r, g, b, depth,
        x0, y1, 0.0, 1.0, r, g, b, depth,
        x1, y0, 1.0, 0.0, r, g, b, depth,

        x1, y0, 1.0, 0.0, r, g, b, depth,
        x0, y1, 0.0, 1.0, r, g, b, depth,
        x1, y1, 1.0, 1.0, r, g, b, depth,
    ])

    # vertikal strek
    x0, y0, x1, y1 = rect_ndc(HALF_W, HALF_H, thickness_px//2, size_px)
    verts.extend([
        x0, y0, 0.0, 0.0, r, g, b, depth,
        x0, y1, 0.0, 1.0, r, g, b, depth,
        x1, y0, 1.0, 0.0, r, g, b, depth,

        x1, y0, 1.0, 0.0, r, g, b, depth,
        x0, y1, 0.0, 1.0, r, g, b, depth,
        x1, y1, 1.0, 1.0, r, g, b, depth,
    ])

    return np.asarray(verts, dtype=np.float32).reshape((-1, 8))

def build_weapon_overlay(firing: bool, recoil_t: float) -> np.ndarray:
    """En enkel "pistolboks" nederst (farget quad), m/ liten recoil-bevegelse."""
    verts = []

    # Weapon box
    base_w, base_h = 200, 120
    x = HALF_W - base_w // 2
    y = HEIGHT - base_h - 10
    if firing:
        y += int(6 * math.sin(min(1.0, recoil_t) * math.pi))

    x0 = (2.0 * x) / WIDTH - 1.0
    x1 = (2.0 * (x + base_w)) / WIDTH - 1.0
    y0 = 1.0 - 2.0 * (y / HEIGHT)
    y1 = 1.0 - 2.0 * ((y + base_h) / HEIGHT)

    # lett gjennomsiktig mørk grå
    # vi bruker v_col for RGB, alpha kommer fra tekstur (1x1 hvit, a=1). For alpha: n.a. her.
    r, g, b = (0.12, 0.12, 0.12)
    depth = 0.0
    verts.extend([
        x0, y0, 0.0, 0.0, r, g, b, depth,
        x0, y1, 0.0, 1.0, r, g, b, depth,
        x1, y0, 1.0, 0.0, r, g, b, depth,

        x1, y0, 1.0, 0.0, r, g, b, depth,
        x0, y1, 0.0, 1.0, r, g, b, depth,
        x1, y1, 1.0, 1.0, r, g, b, depth,
    ])

    # Ammo counter - a full bar that changes color and shrinks as ammo depletes
    # Instead of showing just a partial bar, we'll show a full green bar that:
    # 1. Starts as full height and green when ammo is full
    # 2. Shrinks proportionally as ammo is used
    # 3. Changes color from green to yellow to red as ammo decreases
    ammo_w = 20
    ammo_h = base_h
    ammo_x = x - ammo_w - 10  # 10px gap from weapon
    ammo_y = y

    # Calculate the height of the ammo bar based on remaining ammo
    # Full height when ammo is at maximum (20)
    ammo_h_scaled = ammo_h * (player_ammo / 20)  # Assuming max ammo is 20
    ammo_y_offset = ammo_h - ammo_h_scaled

    # Convert to NDC coordinates
    ax0 = (2.0 * ammo_x) / WIDTH - 1.0
    ax1 = (2.0 * (ammo_x + ammo_w)) / WIDTH - 1.0
    ay0 = 1.0 - 2.0 * ((ammo_y + ammo_y_offset) / HEIGHT)
    ay1 = 1.0 - 2.0 * (ammo_y / HEIGHT)

    # Color gradient based on ammo percentage:
    # - Green (0,1,0) when full (>10)
    # - Yellow (1,1,0) when medium (6-10)
    # - Red (1,0,0) when low (≤5)
    if player_ammo > 10:
        ar, ag, ab = 0.0, 1.0, 0.0  # Green
    elif player_ammo > 5:
        ar, ag, ab = 1.0, 1.0, 0.0  # Yellow
    else:
        ar, ag, ab = 1.0, 0.0, 0.0  # Red

    verts.extend([
        ax0, ay0, 0.0, 0.0, ar, ag, ab, depth,
        ax0, ay1, 0.0, 1.0, ar, ag, ab, depth,
        ax1, ay0, 1.0, 0.0, ar, ag, ab, depth,

        ax1, ay0, 1.0, 0.0, ar, ag, ab, depth,
        ax0, ay1, 0.0, 1.0, ar, ag, ab, depth,
        ax1, ay1, 1.0, 1.0, ar, ag, ab, depth,
    ])

    return np.asarray(verts, dtype=np.float32).reshape((-1, 8))


def build_wave_info_display(wave_number: int, countdown: float, between_waves: bool) -> np.ndarray:
    """Build quads to display wave information in the top-right corner."""
    verts: list[float] = []
    pad = 10

    def add_quad_px(x_px, y_px, w_px, h_px, col, depth):
        r, g, b = col
        x0 = (2.0 * x_px) / WIDTH - 1.0
        x1 = (2.0 * (x_px + w_px)) / WIDTH - 1.0
        y0 = 1.0 - 2.0 * (y_px / HEIGHT)
        y1 = 1.0 - 2.0 * ((y_px + h_px) / HEIGHT)
        verts.extend([
            x0, y0, 0.0, 0.0, r, g, b, depth,
            x0, y1, 0.0, 1.0, r, g, b, depth,
            x1, y0, 1.0, 0.0, r, g, b, depth,
            x1, y0, 1.0, 0.0, r, g, b, depth,
            x0, y1, 0.0, 1.0, r, g, b, depth,
            x1, y1, 1.0, 1.0, r, g, b, depth,
        ])

    # Background panel
    panel_width = 150
    panel_height = 60
    panel_x = WIDTH - panel_width - pad
    panel_y = pad
    add_quad_px(panel_x, panel_y, panel_width, panel_height, (0.1, 0.1, 0.1), 0.0)

    # Wave number indicator - display as a series of blocks
    wave_label_width = 140
    wave_label_height = 20
    wave_label_x = panel_x + 5
    wave_label_y = panel_y + 5
    add_quad_px(wave_label_x, wave_label_y, wave_label_width, wave_label_height, (0.2, 0.2, 0.2), 0.0)

    # Display wave number as colored blocks
    block_width = 10
    block_spacing = 5
    for i in range(min(wave_number, 10)):  # Limit to 10 blocks
        block_x = wave_label_x + 5 + i * (block_width + block_spacing)
        block_y = wave_label_y + 5
        block_height = 10
        # Make blocks gradually more red as wave number increases
        intensity = 0.3 + (i / 10) * 0.7
        add_quad_px(block_x, block_y, block_width, block_height, (intensity, 0.2, 0.2), 0.0)

    # Countdown bar (only shown between waves)
    if between_waves:
        countdown_label_width = 140
        countdown_label_height = 20
        countdown_label_x = panel_x + 5
        countdown_label_y = panel_y + 30
        add_quad_px(countdown_label_x, countdown_label_y, countdown_label_width, countdown_label_height, (0.2, 0.2, 0.2), 0.0)

        # Progress bar for countdown
        max_countdown = 5.0  # Same as in WaveManager
        progress = min(1.0, countdown / max_countdown)
        bar_width = int(130 * progress)
        bar_x = countdown_label_x + 5
        bar_y = countdown_label_y + 5
        bar_height = 10
        add_quad_px(bar_x, bar_y, bar_width, bar_height, (0.2, 0.6, 0.2), 0.0)

    return np.asarray(verts, dtype=np.float32).reshape((-1, 8))


def build_minimap_quads(ammo_boxes: list['AmmoBox'] = None, enemies: list['Enemy'] = None) -> np.ndarray:
    """Liten GL-basert minimap øverst til venstre."""
    scale = 6
    mm_w = MAP_W * scale
    mm_h = MAP_H * scale
    pad = 10
    verts: list[float] = []

    # If ammo_boxes is None, use an empty list
    if ammo_boxes is None:
        ammo_boxes = []

    # If enemies is None, use an empty list
    if enemies is None:
        enemies = []

    def add_quad_px(x_px, y_px, w_px, h_px, col, depth):
        r, g, b = col
        x0 = (2.0 * x_px) / WIDTH - 1.0
        x1 = (2.0 * (x_px + w_px)) / WIDTH - 1.0
        y0 = 1.0 - 2.0 * (y_px / HEIGHT)
        y1 = 1.0 - 2.0 * ((y_px + h_px) / HEIGHT)
        verts.extend([
            x0, y0, 0.0, 0.0, r, g, b, depth,
            x0, y1, 0.0, 1.0, r, g, b, depth,
            x1, y0, 1.0, 0.0, r, g, b, depth,
            x1, y0, 1.0, 0.0, r, g, b, depth,
            x0, y1, 0.0, 1.0, r, g, b, depth,
            x1, y1, 1.0, 1.0, r, g, b, depth,
        ])

    # Bakgrunn
    add_quad_px(pad-2, pad-2, mm_w+4, mm_h+4, (0.1, 0.1, 0.1), 0.0)

    # Celler
    for y in range(MAP_H):
        for x in range(MAP_W):
            if MAP[y][x] > 0:
                col = (0.86, 0.86, 0.86)
                add_quad_px(pad + x*scale, pad + y*scale, scale-1, scale-1, col, 0.0)

    # Spiller (green)
    px = int(player_x * scale)
    py = int(player_y * scale)
    add_quad_px(pad + px - 2, pad + py - 2, 4, 4, (0.0, 1.0, 0.0), 0.0)

    # Retningsstrek (en liten rektangulær "linje")
    fx = int(px + dir_x * 8)
    fy = int(py + dir_y * 8)
    # tegn som tynn boks mellom (px,py) og (fx,fy)
    # for enkelhet: bare en liten boks på enden
    add_quad_px(pad + fx - 1, pad + fy - 1, 2, 2, (0.0, 1.0, 0.0), 0.0)

    # Draw ammo boxes on minimap
    for box in ammo_boxes:
        if box.alive:
            # Convert ammo box position to minimap coordinates
            box_x = int(box.x * scale)
            box_y = int(box.y * scale)
            # Draw a blue square for each ammo box
            add_quad_px(pad + box_x - 2, pad + box_y - 2, 4, 4, (0.0, 0.0, 1.0), 0.0)

    # Draw enemies on minimap
    for enemy in enemies:
        if enemy.alive:
            # Convert enemy position to minimap coordinates
            enemy_x = int(enemy.x * scale)
            enemy_y = int(enemy.y * scale)
            # Draw a red square for each enemy
            add_quad_px(pad + enemy_x - 2, pad + enemy_y - 2, 4, 4, (0.9, 0.1, 0.1), 0.0)

    return np.asarray(verts, dtype=np.float32).reshape((-1, 8))

# ---------- Input/fysikk ----------
def try_move(nx: float, ny: float) -> tuple[float, float]:
    if not is_wall(int(nx), int(player_y)):
        x = nx
    else:
        x = player_x
    if not is_wall(int(player_x), int(ny)):
        y = ny
    else:
        y = player_y
    return x, y

def handle_input(dt: float) -> None:
    global player_x, player_y, dir_x, dir_y, plane_x, plane_y
    keys = pygame.key.get_pressed()
    rot = 0.0
    if keys[pygame.K_LEFT] or keys[pygame.K_q]:
        rot -= ROT_SPEED * dt
    if keys[pygame.K_RIGHT] or keys[pygame.K_e]:
        rot += ROT_SPEED * dt
    if rot != 0.0:
        cosr, sinr = math.cos(rot), math.sin(rot)
        ndx = dir_x * cosr - dir_y * sinr
        ndy = dir_x * sinr + dir_y * cosr
        npx = plane_x * cosr - plane_y * sinr
        npy = plane_x * sinr + plane_y * cosr
        dir_x, dir_y, plane_x, plane_y = ndx, ndy, npx, npy

    forward = 0.0
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        forward += MOVE_SPEED * dt
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        forward -= MOVE_SPEED * dt
    if forward != 0.0:
        nx = player_x + dir_x * forward
        ny = player_y + dir_y * forward
        player_x, player_y = try_move(nx, ny)

    strafe = 0.0
    if keys[pygame.K_a]:
        strafe -= STRAFE_SPEED * dt
    if keys[pygame.K_d]:
        strafe += STRAFE_SPEED * dt
    if strafe != 0.0:
        nx = player_x + (-dir_y) * strafe
        ny = player_y + (dir_x) * strafe
        player_x, player_y = try_move(nx, ny)

# ---------- Main ----------
def find_random_valid_position() -> tuple[float, float]:
    """Find a random valid position on the floor (not inside a wall)"""
    while True:
        # Generate random position within map bounds
        x = random.uniform(1.5, MAP_W - 1.5)
        y = random.uniform(1.5, MAP_H - 1.5)

        # Check if position is valid (not inside a wall)
        if not is_wall(int(x), int(y)):
            # Make sure it's not too close to the player's starting position
            dx = x - 3.5  # player_x starting position
            dy = y - 10.5  # player_y starting position
            dist = math.hypot(dx, dy)

            # If it's at least 3 units away from player start, it's valid
            if dist > 3.0:
                return x, y

def main() -> None:
    global player_ammo
    pygame.init()

    # Initialize audio system
    init_audio()
    load_sound_effects()
    load_background_music()

    pygame.display.set_caption("Vibe Wolf (OpenGL)")

    # setup to make it work on mac as well...
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

    # Opprett GL-kontekst
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    gl.glViewport(0, 0, WIDTH, HEIGHT)

    clock = pygame.time.Clock()
    renderer = GLRenderer()

    bullets: list[Bullet] = []
    firing = False
    recoil_t = 0.0

    # Initialize empty enemies list (will be populated by wave manager)
    enemies: list[Enemy] = []

    # Initialize the wave manager
    wave_manager = WaveManager()

    # Initialize ammo boxes with one at a random position
    ammo_boxes: list[AmmoBox] = []
    x, y = find_random_valid_position()
    ammo_boxes.append(AmmoBox(x, y))

    # Timer for spawning new ammo boxes
    ammo_box_spawn_timer = 0.0
    ammo_box_spawn_interval = 20.0  # seconds between spawns

    # Mus-capture (synlig cursor + crosshair)
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(True)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:  # eller en annen knapp
                    grab = not pygame.event.get_grab()
                    pygame.event.set_grab(grab)
                    pygame.mouse.set_visible(not grab)
                    print("Mouse grab:", grab)
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    # Only shoot if player has ammo
                    if player_ammo > 0:
                        bx = player_x + dir_x * 0.4
                        by = player_y + dir_y * 0.4
                        bvx = dir_x * 10.0
                        bvy = dir_y * 10.0
                        bullets.append(Bullet(bx, by, bvx, bvy))
                        firing = True
                        recoil_t = 0.0
                        # Decrease ammo when shooting
                        player_ammo -= 1
                        # Play gunshot sound
                        play_sound("gunshot")
                    else:
                        # Play empty click sound when out of ammo
                        play_sound("empty_click")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Only shoot if player has ammo
                if player_ammo > 0:
                    bx = player_x + dir_x * 0.4
                    by = player_y + dir_y * 0.4
                    bvx = dir_x * 10.0
                    bvy = dir_y * 10.0
                    bullets.append(Bullet(bx, by, bvx, bvy))
                    firing = True
                    recoil_t = 0.0
                    # Decrease ammo when shooting
                    player_ammo -= 1
                    # Play gunshot sound
                    play_sound("gunshot")
                else:
                    # Play empty click sound when out of ammo
                    play_sound("empty_click")

        handle_input(dt)

        # Update wave manager
        wave_manager.update(dt, enemies)

        # Spawn enemies for the current wave
        wave_manager.spawn_enemies(enemies)

        # Oppdater bullets
        for b in bullets:
            b.update(dt)
            if not b.alive:
                continue
            for e in enemies:
                if not e.alive:
                    continue
                dx = e.x - b.x
                dy = e.y - b.y
                if dx * dx + dy * dy <= (e.radius * e.radius):
                    # Use take_damage method instead of directly killing the enemy
                    enemy_died = e.take_damage(1)
                    if enemy_died:
                        print(f"Enemy killed! Wave: {wave_manager.current_wave}")
                        # Play enemy death sound
                        play_sound("enemy_death")
                    else:
                        # Play bullet impact sound when hitting enemy but not killing
                        play_sound("bullet_impact")
                    b.alive = False  # kula forbrukes
                    break
        bullets = [b for b in bullets if b.alive]

        # Oppdater fiender
        for e in enemies:
            e.update(dt)

        # Update ammo boxes
        for box in ammo_boxes:
            box.update(dt)

        # Clean up picked up ammo boxes
        ammo_boxes = [box for box in ammo_boxes if box.alive]

        # Spawn new ammo box if needed
        ammo_box_spawn_timer += dt
        if ammo_box_spawn_timer >= ammo_box_spawn_interval and len(ammo_boxes) < 3:
            x, y = find_random_valid_position()
            ammo_boxes.append(AmmoBox(x, y))
            ammo_box_spawn_timer = 0.0
            print(f"New ammo box spawned at ({x:.1f}, {y:.1f})")

        # ---------- Render ----------
        gl.glViewport(0, 0, WIDTH, HEIGHT)
        gl.glClearColor(0.05, 0.07, 0.1, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Bakgrunn (himmel/gulv)
        bg = build_fullscreen_background()
        renderer.draw_arrays(bg, renderer.white_tex, use_tex=False)

        # Vegger (batch pr. tex_id)
        batches_lists = cast_and_build_wall_batches()
        for tid, verts_list in batches_lists.items():
            if tid not in renderer.textures:
                continue
            if not verts_list:
                continue
            arr = np.asarray(verts_list, dtype=np.float32).reshape((-1, 8))
            renderer.draw_arrays(arr, renderer.textures[tid], use_tex=True)

        # Sprites (kuler)
        spr = build_sprites_batch(bullets)
        if spr.size:
            renderer.draw_arrays(spr, renderer.textures[99], use_tex=True)

        # Enemies (billboards)
        enemies_batch = build_enemies_batch(enemies)
        if enemies_batch.size:
            renderer.draw_arrays(enemies_batch, renderer.textures[200], use_tex=True)

        # Ammo boxes (billboards)
        ammo_boxes_batch = build_ammo_boxes_batch(ammo_boxes)
        if ammo_boxes_batch.size:
            renderer.draw_arrays(ammo_boxes_batch, renderer.textures[201], use_tex=True)

        # Crosshair
        cross = build_crosshair_quads(8, 2)
        renderer.draw_arrays(cross, renderer.white_tex, use_tex=False)

        # Weapon overlay
        if firing:
            recoil_t += dt
            if recoil_t > 0.15:
                firing = False
        overlay = build_weapon_overlay(firing, recoil_t)
        renderer.draw_arrays(overlay, renderer.white_tex, use_tex=False)

        # Minimap
        mm = build_minimap_quads(ammo_boxes, enemies)
        renderer.draw_arrays(mm, renderer.white_tex, use_tex=False)

        # Wave information display
        wave_number, countdown, between_waves = wave_manager.get_wave_info()
        wave_info = build_wave_info_display(wave_number, countdown, between_waves)
        renderer.draw_arrays(wave_info, renderer.white_tex, use_tex=False)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fatal error:", e)
        sys.exit(1)
