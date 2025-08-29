#!/usr/bin/env python3
"""Generate weapon sprite images for pistol and rifle."""

import pygame
import sys
from pathlib import Path

def create_pistol_sprite(size=(200, 120)):
    """Create a simple pistol sprite."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))  # Transparent background

    # Pistol colors
    barrel_color = (60, 60, 60)      # Dark gray barrel
    grip_color = (80, 50, 30)        # Brown grip
    trigger_color = (40, 40, 40)     # Dark trigger guard

    # Draw pistol components
    # Barrel (horizontal rectangle)
    barrel_rect = pygame.Rect(size[0]//4, size[1]//2 - 15, size[0]//2, 30)
    pygame.draw.rect(surface, barrel_color, barrel_rect)

    # Grip (vertical rectangle)
    grip_rect = pygame.Rect(size[0]//4 - 20, size[1]//2, 40, size[1]//3)
    pygame.draw.rect(surface, grip_color, grip_rect)

    # Trigger guard (small arc)
    trigger_rect = pygame.Rect(size[0]//4 - 10, size[1]//2 + 10, 20, 15)
    pygame.draw.rect(surface, trigger_color, trigger_rect)

    # Sight (small rectangle on top)
    sight_rect = pygame.Rect(size[0]//2 + size[0]//4 - 5, size[1]//2 - 20, 10, 10)
    pygame.draw.rect(surface, barrel_color, sight_rect)

    return surface

def create_rifle_sprite(size=(200, 120)):
    """Create a simple rifle sprite."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))  # Transparent background

    # Rifle colors
    barrel_color = (40, 40, 40)      # Dark gray barrel
    stock_color = (101, 67, 33)      # Brown wooden stock
    metal_color = (70, 70, 70)       # Metal parts

    # Draw rifle components
    # Long barrel (horizontal rectangle)
    barrel_rect = pygame.Rect(size[0]//6, size[1]//2 - 8, size[0]*2//3, 16)
    pygame.draw.rect(surface, barrel_color, barrel_rect)

    # Stock (larger rectangle at back)
    stock_rect = pygame.Rect(10, size[1]//2 - 20, size[0]//4, 40)
    pygame.draw.rect(surface, stock_color, stock_rect)

    # Trigger area (small rectangle)
    trigger_rect = pygame.Rect(size[0]//3, size[1]//2 + 5, 30, 25)
    pygame.draw.rect(surface, metal_color, trigger_rect)

    # Scope/sight (rectangle on top)
    scope_rect = pygame.Rect(size[0]//2, size[1]//2 - 25, 40, 12)
    pygame.draw.rect(surface, metal_color, scope_rect)

    # Muzzle (small rectangle at end)
    muzzle_rect = pygame.Rect(size[0]*5//6, size[1]//2 - 10, 15, 20)
    pygame.draw.rect(surface, barrel_color, muzzle_rect)

    return surface

def main():
    """Generate weapon sprites and save them."""
    pygame.init()

    # Create output directory
    sprites_dir = Path("assets/sprites")
    sprites_dir.mkdir(parents=True, exist_ok=True)

    # Generate pistol sprite
    pistol_surface = create_pistol_sprite()
    pistol_path = sprites_dir / "pistol.png"
    pygame.image.save(pistol_surface, str(pistol_path))
    print(f"Generated pistol sprite: {pistol_path}")

    # Generate rifle sprite
    rifle_surface = create_rifle_sprite()
    rifle_path = sprites_dir / "rifle.png"
    pygame.image.save(rifle_surface, str(rifle_path))
    print(f"Generated rifle sprite: {rifle_path}")

    pygame.quit()
    print("Weapon sprites generated successfully!")

if __name__ == "__main__":
    main()
