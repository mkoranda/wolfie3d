# Weapon Switching System Implementation

## Overview
This document describes the weapon switching system implemented for Wolfie3D, allowing players to switch between a pistol and rifle with different characteristics.

## Features Implemented

### 1. Weapon Classes and Properties
- **Pistol**: 3 shots/sec, bullet speed 10.0, 20 max ammo, light gray color
- **Rifle**: 8 shots/sec, bullet speed 15.0, 30 max ammo, brown color

### 2. Weapon Switching Controls
- Press **1** to switch to Pistol
- Press **2** to switch to Rifle
- Console messages confirm weapon switches

### 3. Visual Feedback
- **Weapon Display**: The weapon box at the bottom of the screen changes color based on current weapon
  - Pistol: Light gray (0.8, 0.8, 0.8)
  - Rifle: Brown (0.4, 0.2, 0.0)
- **Ammo Counter**: Colored bar that scales based on current weapon's ammo capacity
  - Green: >50% ammo remaining
  - Yellow: 25-50% ammo remaining  
  - Red: <25% ammo remaining

### 4. Fire Rate Differences
- **Pistol**: Fires 3 times per second (slower, more controlled)
- **Rifle**: Fires 8 times per second (rapid fire)
- Fire rate limiting prevents shooting faster than weapon allows

### 5. Ammo Management
- Each weapon has independent ammo capacity
- Ammo pickups reload the currently equipped weapon
- Ammo display scales properly for different weapon capacities

## Technical Implementation

### Code Changes Made

1. **Added Weapon Class** (`src/wolfie3d/game.py` lines 183-210):
   ```python
   class Weapon:
       def __init__(self, name, fire_rate, bullet_speed, damage, max_ammo, color):
           # Weapon properties and state management
   ```

2. **Weapon Initialization** (lines 212-219):
   - Created pistol and rifle instances with different properties
   - Set initial weapon to pistol

3. **Input Handling Updates** (lines 1517-1524):
   - Added number key handling for weapon switching
   - Updated shooting mechanics to use current weapon properties

4. **Visual System Updates**:
   - Modified `build_weapon_overlay()` to use current weapon color and ammo
   - Updated ammo counter to scale based on weapon capacity

5. **Ammo Pickup System** (lines 410-414):
   - Changed from hardcoded player_ammo to current weapon reload

## Usage Instructions

### For Players
1. **Switch Weapons**: Press 1 for pistol, 2 for rifle
2. **Shooting**: Use SPACE or left mouse button (same as before)
3. **Ammo**: Pick up ammo boxes to reload current weapon
4. **Visual Cues**: 
   - Weapon color indicates current weapon type
   - Ammo bar color indicates remaining ammunition

### For Developers
- Weapons are stored in the `weapons` dictionary with numeric keys
- Current weapon is tracked via `current_weapon_id` and `current_weapon` variables
- Fire rate is enforced using timestamps in the `Weapon.shoot()` method
- All weapon properties are easily configurable in the weapon initialization

## Testing
A test script (`test_weapon_switching.py`) verifies:
- Weapon properties are correctly set
- Fire rate differences work as expected
- Bullet speed differences are implemented
- Reload functionality works properly
- All assertions pass confirming system integrity

## Future Enhancements
- Add weapon-specific sound effects
- Implement weapon sprites/textures instead of colored rectangles
- Add weapon damage differences
- Include weapon-specific recoil patterns
- Add more weapon types (shotgun, sniper rifle, etc.)
