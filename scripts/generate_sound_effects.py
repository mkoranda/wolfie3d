#!/usr/bin/env python3
"""
Generate sound effects for Wolfie3D game actions.
Creates procedural sound effects in Mac-compatible WAV format.
"""

import math
import numpy as np
import wave
from pathlib import Path


def generate_tone(frequency: float, duration: float, sample_rate: int = 44100, amplitude: float = 0.3) -> np.ndarray:
    """Generate a sine wave tone."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return amplitude * np.sin(2 * np.pi * frequency * t)


def generate_noise(duration: float, sample_rate: int = 44100, amplitude: float = 0.1) -> np.ndarray:
    """Generate white noise."""
    samples = int(sample_rate * duration)
    return amplitude * np.random.uniform(-1, 1, samples)


def apply_envelope(audio: np.ndarray, attack: float = 0.01, decay: float = 0.1, sustain: float = 0.7, release: float = 0.2) -> np.ndarray:
    """Apply ADSR envelope to audio."""
    length = len(audio)
    envelope = np.ones(length)

    # Normalize phase durations to ensure they don't exceed total length
    total_phases = attack + decay + release
    if total_phases > 1.0:
        # Scale down all phases proportionally
        scale = 1.0 / total_phases
        attack *= scale
        decay *= scale
        release *= scale

    # Calculate sample counts
    attack_samples = int(attack * length)
    decay_samples = int(decay * length)
    release_samples = int(release * length)

    # Ensure we don't exceed array bounds
    attack_samples = min(attack_samples, length)
    decay_samples = min(decay_samples, length - attack_samples)
    release_samples = min(release_samples, length)

    # Attack phase
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    # Decay phase
    if decay_samples > 0:
        decay_end = attack_samples + decay_samples
        envelope[attack_samples:decay_end] = np.linspace(1, sustain, decay_samples)

    # Release phase
    if release_samples > 0:
        release_start = length - release_samples
        envelope[release_start:] = np.linspace(envelope[release_start], 0, release_samples)

    return audio * envelope


def generate_gunshot() -> np.ndarray:
    """Generate a realistic gunshot sound effect."""
    sample_rate = 44100
    duration = 0.3

    # Initial explosion (high frequency burst)
    explosion = generate_noise(0.05, sample_rate, 0.8)
    explosion = apply_envelope(explosion, attack=0.001, decay=0.02, sustain=0.3, release=0.03)

    # Low frequency thump
    thump = generate_tone(80, 0.15, sample_rate, 0.6)
    thump = apply_envelope(thump, attack=0.001, decay=0.05, sustain=0.4, release=0.1)

    # High frequency crack
    crack = generate_tone(2000, 0.08, sample_rate, 0.4)
    crack = apply_envelope(crack, attack=0.001, decay=0.02, sustain=0.2, release=0.05)

    # Combine all elements
    max_len = max(len(explosion), len(thump), len(crack))
    gunshot = np.zeros(int(sample_rate * duration))

    # Layer the sounds
    gunshot[:len(explosion)] += explosion
    gunshot[:len(thump)] += thump
    gunshot[:len(crack)] += crack

    # Add some reverb tail
    reverb = generate_noise(0.2, sample_rate, 0.1)
    reverb = apply_envelope(reverb, attack=0.05, decay=0.1, sustain=0.3, release=0.05)
    reverb_start = int(0.1 * sample_rate)
    gunshot[reverb_start:reverb_start + len(reverb)] += reverb

    return gunshot


def generate_empty_click() -> np.ndarray:
    """Generate an empty gun click sound."""
    sample_rate = 44100
    duration = 0.1

    # Sharp metallic click
    click = generate_tone(1500, 0.02, sample_rate, 0.3)
    click = apply_envelope(click, attack=0.001, decay=0.005, sustain=0.1, release=0.015)

    # Add some mechanical noise
    noise = generate_noise(0.03, sample_rate, 0.1)
    noise = apply_envelope(noise, attack=0.001, decay=0.01, sustain=0.2, release=0.02)

    # Combine
    empty_click = np.zeros(int(sample_rate * duration))
    empty_click[:len(click)] += click
    empty_click[:len(noise)] += noise

    return empty_click


def generate_bullet_impact() -> np.ndarray:
    """Generate bullet impact/hit sound."""
    sample_rate = 44100
    duration = 0.2

    # Sharp impact
    impact = generate_noise(0.05, sample_rate, 0.5)
    impact = apply_envelope(impact, attack=0.001, decay=0.02, sustain=0.2, release=0.03)

    # Metallic ring
    ring = generate_tone(800, 0.1, sample_rate, 0.3)
    ring = apply_envelope(ring, attack=0.01, decay=0.03, sustain=0.4, release=0.06)

    # Combine
    bullet_impact = np.zeros(int(sample_rate * duration))
    bullet_impact[:len(impact)] += impact
    bullet_impact[:len(ring)] += ring

    return bullet_impact


def generate_enemy_death() -> np.ndarray:
    """Generate enemy death sound."""
    sample_rate = 44100
    duration = 0.8

    # Descending tone (death cry)
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freq_sweep = 400 * np.exp(-3 * t)  # Exponential decay from 400Hz
    death_cry = 0.4 * np.sin(2 * np.pi * freq_sweep * t)
    death_cry = apply_envelope(death_cry, attack=0.1, decay=0.2, sustain=0.3, release=0.3)

    # Add some distortion/growl
    growl = generate_noise(0.5, sample_rate, 0.2)
    growl = apply_envelope(growl, attack=0.05, decay=0.1, sustain=0.4, release=0.35)

    # Combine
    enemy_death = np.zeros(int(sample_rate * duration))
    enemy_death[:len(death_cry)] += death_cry
    enemy_death[:len(growl)] += growl

    return enemy_death


def generate_ammo_pickup() -> np.ndarray:
    """Generate ammo pickup sound."""
    sample_rate = 44100
    duration = 0.4

    # Rising chime (positive feedback)
    chime1 = generate_tone(440, 0.15, sample_rate, 0.3)  # A4
    chime2 = generate_tone(554, 0.15, sample_rate, 0.25)  # C#5
    chime3 = generate_tone(659, 0.2, sample_rate, 0.2)   # E5

    # Apply envelopes
    chime1 = apply_envelope(chime1, attack=0.01, decay=0.05, sustain=0.6, release=0.09)
    chime2 = apply_envelope(chime2, attack=0.01, decay=0.05, sustain=0.6, release=0.09)
    chime3 = apply_envelope(chime3, attack=0.01, decay=0.05, sustain=0.6, release=0.14)

    # Combine with slight delays
    ammo_pickup = np.zeros(int(sample_rate * duration))
    ammo_pickup[:len(chime1)] += chime1

    delay2 = int(0.08 * sample_rate)
    ammo_pickup[delay2:delay2 + len(chime2)] += chime2

    delay3 = int(0.15 * sample_rate)
    ammo_pickup[delay3:delay3 + len(chime3)] += chime3

    return ammo_pickup


def generate_footstep() -> np.ndarray:
    """Generate footstep sound."""
    sample_rate = 44100
    duration = 0.15

    # Low frequency thud
    thud = generate_tone(60, 0.08, sample_rate, 0.4)
    thud = apply_envelope(thud, attack=0.001, decay=0.02, sustain=0.3, release=0.05)

    # High frequency scrape/scuff
    scrape = generate_noise(0.06, sample_rate, 0.2)
    scrape = apply_envelope(scrape, attack=0.005, decay=0.02, sustain=0.2, release=0.035)

    # Combine
    footstep = np.zeros(int(sample_rate * duration))
    footstep[:len(thud)] += thud
    footstep[:len(scrape)] += scrape

    return footstep


def generate_wave_start() -> np.ndarray:
    """Generate wave start notification sound."""
    sample_rate = 44100
    duration = 1.0

    # Dramatic rising tone
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freq_sweep = 200 + 300 * t / duration  # Rise from 200Hz to 500Hz
    wave_start = 0.3 * np.sin(2 * np.pi * freq_sweep * t)

    # Add harmonics for richness
    wave_start += 0.15 * np.sin(2 * np.pi * freq_sweep * 2 * t)
    wave_start += 0.1 * np.sin(2 * np.pi * freq_sweep * 3 * t)

    wave_start = apply_envelope(wave_start, attack=0.1, decay=0.2, sustain=0.6, release=0.1)

    return wave_start


def generate_wave_complete() -> np.ndarray:
    """Generate wave complete notification sound."""
    sample_rate = 44100
    duration = 0.8

    # Victory chord progression
    chord1 = generate_tone(523, 0.3, sample_rate, 0.2)  # C5
    chord1 += generate_tone(659, 0.3, sample_rate, 0.15)  # E5
    chord1 += generate_tone(784, 0.3, sample_rate, 0.1)   # G5

    chord2 = generate_tone(523, 0.5, sample_rate, 0.25)  # C5
    chord2 += generate_tone(659, 0.5, sample_rate, 0.2)   # E5
    chord2 += generate_tone(784, 0.5, sample_rate, 0.15)  # G5
    chord2 += generate_tone(1047, 0.5, sample_rate, 0.1)  # C6

    # Apply envelopes
    chord1 = apply_envelope(chord1, attack=0.05, decay=0.1, sustain=0.6, release=0.15)
    chord2 = apply_envelope(chord2, attack=0.05, decay=0.15, sustain=0.5, release=0.3)

    # Combine
    wave_complete = np.zeros(int(sample_rate * duration))
    wave_complete[:len(chord1)] += chord1

    delay = int(0.3 * sample_rate)
    wave_complete[delay:delay + len(chord2)] += chord2

    return wave_complete


def save_wav(audio: np.ndarray, filename: str, sample_rate: int = 44100):
    """Save audio as WAV file."""
    # Normalize to prevent clipping
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.8  # Leave some headroom

    # Convert to 16-bit integers
    audio_int = (audio * 32767).astype(np.int16)

    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int.tobytes())


def main():
    """Generate all sound effects."""
    assets_sounds = Path("assets/sounds")
    assets_sounds.mkdir(exist_ok=True)

    print("🔊 Generating sound effects for Wolfie3D...")

    # Generate all sound effects
    sound_effects = {
        "gunshot.wav": generate_gunshot(),
        "empty_click.wav": generate_empty_click(),
        "bullet_impact.wav": generate_bullet_impact(),
        "enemy_death.wav": generate_enemy_death(),
        "ammo_pickup.wav": generate_ammo_pickup(),
        "footstep.wav": generate_footstep(),
        "wave_start.wav": generate_wave_start(),
        "wave_complete.wav": generate_wave_complete(),
    }

    for filename, audio in sound_effects.items():
        output_file = assets_sounds / filename
        print(f"Generating {filename}...")
        save_wav(audio, str(output_file))

    print("✅ All sound effects generated successfully!")
    print(f"📁 Saved to: {assets_sounds}")
    print("🎮 Ready to integrate into the game!")
    print("\nGenerated sound effects:")
    for filename in sound_effects.keys():
        print(f"  • {filename}")


if __name__ == "__main__":
    main()
