import os
import shutil
import time
from PIL import Image
from pathlib import Path
from datetime import datetime, timedelta
from config import get_output_dir, get_temp_dir, BASE_DIR

def save_image_to_file(image, filename, directory=None, format="PNG"):
    """
    Save an image to a file
    
    Args:
        image (PIL.Image): Image to save
        filename (str): Filename (without extension)
        directory (str): Directory to save to
        format (str): Image format
        
    Returns:
        str: Path to the saved image
    """
    # Use default output directory if none provided
    if directory is None:
        directory = get_output_dir()
    else:
        # Make directory path relative to project base
        directory = BASE_DIR / directory
        
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Generate a unique filename
    unique_filename = generate_unique_filename(filename, directory, f".{format.lower()}")
    filepath = os.path.join(directory, unique_filename)
    
    # Save the image
    image.save(filepath, format=format)
    
    return filepath

def generate_unique_filename(base_filename, directory, extension=".png"):
    """
    Generate a unique filename by adding a suffix if the file already exists
    
    Args:
        base_filename (str): Base filename
        directory (str): Directory to check for existing files
        extension (str): File extension
        
    Returns:
        str: Unique filename
    """
    # Remove any extension from base_filename if it exists
    base_filename = os.path.splitext(base_filename)[0]
    
    # Start with the base filename
    filename = f"{base_filename}{extension}"
    filepath = os.path.join(directory, filename)
    
    # If the file exists, add a suffix
    counter = 1
    while os.path.exists(filepath):
        filename = f"{base_filename}_{counter}{extension}"
        filepath = os.path.join(directory, filename)
        counter += 1
    
    return filename

def cleanup_temp_files(directory=None, max_age_hours=1):
    """
    Clean up temporary files older than max_age_hours
    
    Args:
        directory (str): Directory containing temporary files
        max_age_hours (int): Maximum age of files in hours
    """
    # Use default temp directory if none provided
    if directory is None:
        directory = get_temp_dir()
    else:
        # Make directory path relative to project base
        directory = BASE_DIR / directory
    
    # Skip if directory doesn't exist
    if not os.path.exists(directory):
        return
    
    # Calculate cutoff time
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    
    # Iterate through files in the directory
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Skip directories
        if os.path.isdir(filepath):
            continue
        
        # Check file modification time
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        if file_mod_time < cutoff_time:
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error deleting temporary file {filepath}: {str(e)}")

def create_directory_structure():
    """Create the directory structure for the application"""
    
    # List of directories to create
    directories = [
        "data/temp",
        "data/outputs",
        "frontend",
        "backend",
        "utils"
    ]
    
    # Create each directory if it doesn't exist
    for directory in directories:
        os.makedirs(BASE_DIR / directory, exist_ok=True)
    
    # Create __init__.py files in each module directory
    for directory in ["frontend", "backend", "utils"]:
        init_file = BASE_DIR / directory / "__init__.py"
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Module initialization file\n")

def get_all_generated_images(directory=None):
    """
    Get all generated images in the directory
    
    Args:
        directory (str): Directory to scan for images
        
    Returns:
        list: List of image paths sorted by modification time (newest first)
    """
    # Use default output directory if none provided
    if directory is None:
        directory = get_output_dir()
    else:
        # Make directory path relative to project base
        directory = BASE_DIR / directory
    
    # Skip if directory doesn't exist
    if not os.path.exists(directory):
        return []
    
    # Get all image files
    image_extensions = [".png", ".jpg", ".jpeg", ".webp"]
    image_files = []
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Skip directories
        if os.path.isdir(filepath):
            continue
        
        # Check if it's an image file
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            image_files.append(filepath)
    
    # Sort by modification time (newest first)
    return sorted(image_files, key=lambda x: os.path.getmtime(x), reverse=True)