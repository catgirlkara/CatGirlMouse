import sys
import subprocess
import os
import bpy
import pkgutil

# Get the path to the Python interpreter used by Blender
python_path = sys.executable

# Determine the script directory
script_directory = os.path.dirname(bpy.data.filepath)

# Create a folder for packages
packages_directory = os.path.join(script_directory, "packages")
os.makedirs(packages_directory, exist_ok=True)

# Print the path
print("Blender's Python path:", python_path)

# Ensure pip is installed
subprocess.run([python_path, "-m", "ensurepip"])


# Check if the required packages are installed
required_packages = ["numpy", "scipy"]

installed_packages = {pkg.name for pkg in pkgutil.iter_modules()}

for package in required_packages:
    if package not in installed_packages:
        # Install the required package in the created folder
        subprocess.run([python_path, "-m", "pip", "install", "--target=" + packages_directory, package])
        print(f"Installing {package}...")
    else:
        print(f"{package} is already installed")


print(f"Environment should be good to go?")


# Add the folder to the Python import path
sys.path.append(packages_directory)

# Import the installed packages

import numpy as np
# import librosa
# from pydub import AudioSegment
# import simpleaudio as sa

# (Add the rest of your script here, including the custom nodes and operators)
# def create_sine_wave(frequency=440, duration=1, amplitude=5000, sample_rate=44100):
#     t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
#     wave = amplitude * np.sin(2 * np.pi * frequency * t)
#     return wave

# def play_sound(wave, sample_rate=44100):
#     audio = sa.WaveObject(wave, 1, 2, sample_rate)
#     play_obj = audio.play()
#     play_obj.wait_done()

# if __name__ == "__main__":
#     wave = create_sine_wave()
#     play_sound(wave)