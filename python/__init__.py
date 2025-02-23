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


# ADD YOUR REQUIRED PACKAGES HERE!!!
required_packages = ["numpy", "scipy", "bezier", "py5"]

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