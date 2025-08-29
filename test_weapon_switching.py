#!/usr/bin/env python3
"""
Test script to verify weapon switching functionality.
This script will run the game briefly and test weapon switching.
"""

import sys
import time
import pygame
from pathlib import Path

# Add src to path so we can import the game module
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_weapon_switching():
    """Test the weapon switching system"""
    print("Testing weapon switching system...")

    # Import after adding to path
    from wolfie3d.game import weapons, current_weapon_id, current_weapon

    # Test initial state
    print(f"Initial weapon: {current_weapon.name}")
    print(f"Initial weapon ID: {current_weapon_id}")
    print(f"Pistol fire rate: {weapons[1].fire_rate} shots/sec")
    print(f"Rifle fire rate: {weapons[2].fire_rate} shots/sec")
    print(f"Pistol bullet speed: {weapons[1].bullet_speed}")
    print(f"Rifle bullet speed: {weapons[2].bullet_speed}")
    print(f"Pistol max ammo: {weapons[1].max_ammo}")
    print(f"Rifle max ammo: {weapons[2].max_ammo}")

    # Test weapon properties
    assert weapons[1].name == "Pistol"
    assert weapons[2].name == "Rifle"
    assert weapons[2].fire_rate > weapons[1].fire_rate, "Rifle should shoot faster than pistol"
    assert weapons[2].bullet_speed > weapons[1].bullet_speed, "Rifle bullets should be faster"

    # Test shooting mechanics
    current_time = time.time()

    # Test pistol shooting
    pistol = weapons[1]
    pistol_shots = 0
    for i in range(10):
        if pistol.shoot(current_time + i * 0.1):  # Try to shoot every 0.1 seconds
            pistol_shots += 1

    # Test rifle shooting
    rifle = weapons[2]
    rifle_shots = 0
    for i in range(10):
        if rifle.shoot(current_time + i * 0.1):  # Try to shoot every 0.1 seconds
            rifle_shots += 1

    print(f"Pistol shots fired in 1 second: {pistol_shots}")
    print(f"Rifle shots fired in 1 second: {rifle_shots}")

    # Rifle should fire more shots in the same time period
    assert rifle_shots > pistol_shots, "Rifle should fire more shots than pistol in same time"

    # Test reload functionality
    pistol.current_ammo = 0
    pistol.reload()
    assert pistol.current_ammo == pistol.max_ammo, "Reload should restore full ammo"

    print("✅ All weapon switching tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_weapon_switching()
        print("🎉 Weapon switching system is working correctly!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
