"""Regenerate every SVG in assets/.

    pip install -r scripts/requirements.txt
    python scripts/build.py
"""
import hero
import raycaster
import terminal
import titles

if __name__ == "__main__":
    print("building assets/")
    hero.build()
    terminal.build()
    raycaster.build()
    titles.build()
