#!/usr/bin/env python3
"""
Generate original background music for Wolfie3D.
Creates atmospheric, procedural music suitable for a 3D shooter.
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


def apply_envelope(audio: np.ndarray, attack: float = 0.1, decay: float = 0.1, sustain: float = 0.7, release: float = 0.2) -> np.ndarray:
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


def generate_bass_drone(duration: float, base_freq: float = 55.0) -> np.ndarray:
    """Generate a deep bass drone with harmonics."""
    sample_rate = 44100

    # Fundamental frequency
    bass = generate_tone(base_freq, duration, sample_rate, 0.4)

    # Add harmonics for richness
    bass += generate_tone(base_freq * 2, duration, sample_rate, 0.2)
    bass += generate_tone(base_freq * 3, duration, sample_rate, 0.1)

    # Add some low-frequency modulation
    mod_freq = 0.3
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    modulation = 1 + 0.1 * np.sin(2 * np.pi * mod_freq * t)
    bass *= modulation

    return apply_envelope(bass, attack=2.0, decay=1.0, sustain=0.8, release=2.0)


def generate_ambient_pad(duration: float) -> np.ndarray:
    """Generate ambient pad sounds with multiple layers."""
    sample_rate = 44100

    # Multiple sine waves at different frequencies for richness
    frequencies = [220, 330, 440, 660]  # A3, E4, A4, E5
    pad = np.zeros(int(sample_rate * duration))

    for i, freq in enumerate(frequencies):
        # Slight detuning for chorus effect
        detune = 1 + (i - 1.5) * 0.002
        tone = generate_tone(freq * detune, duration, sample_rate, 0.15)

        # Phase offset for each layer
        phase_offset = i * math.pi / 4
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone *= np.sin(2 * np.pi * 0.1 * t + phase_offset) * 0.5 + 0.5

        pad += tone

    return apply_envelope(pad, attack=3.0, decay=2.0, sustain=0.6, release=3.0)


def generate_atmospheric_texture(duration: float) -> np.ndarray:
    """Generate atmospheric texture with filtered noise."""
    sample_rate = 44100

    # Start with noise
    noise = generate_noise(duration, sample_rate, 0.3)

    # Apply low-pass filtering effect by averaging with neighbors
    filtered = np.convolve(noise, np.ones(100)/100, mode='same')

    # Add some tonal elements
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Very low frequency oscillations
    texture = filtered * (0.5 + 0.3 * np.sin(2 * np.pi * 0.05 * t))
    texture += 0.1 * np.sin(2 * np.pi * 0.02 * t)  # Ultra-low rumble

    return apply_envelope(texture, attack=4.0, decay=2.0, sustain=0.4, release=4.0)


def mix_tracks(*tracks) -> np.ndarray:
    """Mix multiple audio tracks together."""
    if not tracks:
        return np.array([])

    # Find the longest track
    max_length = max(len(track) for track in tracks)

    # Pad shorter tracks with zeros
    padded_tracks = []
    for track in tracks:
        if len(track) < max_length:
            padding = np.zeros(max_length - len(track))
            padded_track = np.concatenate([track, padding])
        else:
            padded_track = track
        padded_tracks.append(padded_track)

    # Sum all tracks
    mixed = sum(padded_tracks)

    # Normalize to prevent clipping
    max_val = np.max(np.abs(mixed))
    if max_val > 0:
        mixed = mixed / max_val * 0.8  # Leave some headroom

    return mixed


def save_wav(audio: np.ndarray, filename: str, sample_rate: int = 44100):
    """Save audio as WAV file."""
    # Convert to 16-bit integers
    audio_int = (audio * 32767).astype(np.int16)

    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int.tobytes())


def generate_background_music():
    """Generate the main background music track."""
    duration = 120.0  # 2 minutes, will loop

    print("Generating bass drone...")
    bass = generate_bass_drone(duration, 55.0)  # A1

    print("Generating ambient pad...")
    pad = generate_ambient_pad(duration)

    print("Generating atmospheric texture...")
    atmosphere = generate_atmospheric_texture(duration)

    print("Mixing tracks...")
    music = mix_tracks(bass, pad, atmosphere)

    return music


def main():
    """Generate all music tracks."""
    assets_sounds = Path("assets/sounds")
    assets_sounds.mkdir(exist_ok=True)

    print("🎵 Generating original background music for Wolfie3D...")

    # Generate main background track
    bg_music = generate_background_music()
    output_file = assets_sounds / "background_music.wav"

    print(f"Saving to {output_file}...")
    save_wav(bg_music, str(output_file))

    print("✅ Background music generated successfully!")
    print(f"📁 Saved to: {output_file}")
    print(f"⏱️  Duration: 2 minutes (designed to loop)")
    print("🎮 Ready to integrate into the game!")


if __name__ == "__main__":
    main()
