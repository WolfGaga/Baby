from PIL import Image, ImageEnhance
import io
import base64
import streamlit as st
import os
from pathlib import Path
import time
import cv2
import numpy as np
from config import get_temp_dir, ENHANCEMENT_SETTINGS

def enhance_ultrasound_image(image_base64, contrast_value=None, brightness_value=None):
    """
    Efficiently enhance ultrasound images
    
    Args:
        image_base64 (str): Base64 encoded image
        contrast_value (float): Contrast value (for simple enhancement mode)
        brightness_value (float): Brightness value (for simple enhancement mode)
        
    Returns:
        dict: Dictionary of Base64 string of enhanced images
    """
    try:
        # Use values from config if not provided
        contrast_value = contrast_value or ENHANCEMENT_SETTINGS["contrast"]
        brightness_value = brightness_value or ENHANCEMENT_SETTINGS["brightness"]
        
        # Convert Base64 to image
        image_bytes = base64.b64decode(image_base64)
        
        # Create temporary directory for processing
        temp_dir = get_temp_dir()
        temp_input = temp_dir / f"input_{int(time.time())}.png"
        temp_output_dir = temp_dir / f"enhanced_{int(time.time())}"
        os.makedirs(temp_output_dir, exist_ok=True)
        
        # Save input image to temporary file
        with open(temp_input, "wb") as f:
            f.write(image_bytes)
        
        # Read image
        img = cv2.imread(str(temp_input))
        if img is None:
            raise ValueError(f"Could not read image")
        
        # Convert to grayscale
        if len(img.shape) == 3:
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray_img = img
            
        # Save original image
        original_path = os.path.join(temp_output_dir, "original.jpg")
        cv2.imwrite(original_path, gray_img)
        
        # Enhancement step 1: Apply CLAHE contrast enhancement
        clahe = cv2.createCLAHE(
            clipLimit=ENHANCEMENT_SETTINGS["clahe_clip_limit"], 
            tileGridSize=ENHANCEMENT_SETTINGS["clahe_grid_size"]
        )
        enhanced_img = clahe.apply(gray_img)
        
        # Enhancement step 2: Denoise processing
        denoised_img = cv2.fastNlMeansDenoising(
            enhanced_img, 
            None, 
            ENHANCEMENT_SETTINGS["denoise_h"], 
            ENHANCEMENT_SETTINGS["denoise_template_window_size"], 
            ENHANCEMENT_SETTINGS["denoise_search_window_size"]
        )
        
        # Scan image center area, extract ROI
        height, width = denoised_img.shape
        center_x, center_y = width // 2, height // 2
        
        # Attempt face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(denoised_img, 1.05, 2, minSize=(int(width*0.3), int(height*0.3)))
        
        if len(faces) > 0:
            # Get the largest detected area
            max_area = 0
            max_face = None
            for (x, y, w, h) in faces:
                if w*h > max_area:
                    max_area = w*h
                    max_face = (x, y, w, h)
            
            x, y, w, h = max_face
            
            # Expand detection area by 20% to include more facial features
            expand_factor = 0.2
            new_w = int(w * (1 + expand_factor))
            new_h = int(h * (1 + expand_factor))
            new_x = max(0, x - int(w * expand_factor/2))
            new_y = max(0, y - int(h * expand_factor/2))
            
            # Make sure we don't exceed image boundaries
            new_w = min(new_w, width - new_x)
            new_h = min(new_h, height - new_y)
            
            # Update coordinates
            x, y, w, h = new_x, new_y, new_w, new_h
        else:
            # If no face detected, use a larger ROI from the center of the image
            face_size = min(width, height) * 0.8
            x = int(center_x - face_size // 2)
            y = int(center_y - face_size // 2)
            w = int(face_size)
            h = int(face_size)
            
            # Ensure coordinates are within image bounds
            x = max(0, x)
            y = max(0, y)
            w = min(w, width - x)
            h = min(h, height - y)
        
        # Extract ROI area
        face_roi = denoised_img[y:y+h, x:x+w]
        face_roi_path = os.path.join(temp_output_dir, "face_roi.jpg")
        cv2.imwrite(face_roi_path, face_roi)
        
        # Apply normalization to ensure good contrast range
        normalized = cv2.normalize(face_roi, None, 50, 230, cv2.NORM_MINMAX)
        normalized_path = os.path.join(temp_output_dir, "normalized.jpg")
        cv2.imwrite(normalized_path, normalized)
        
        # Create SD optimized version (mild sharpening)
        sharpen_kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])
        sd_optimized = cv2.filter2D(normalized, -1, sharpen_kernel)
        sd_optimized_path = os.path.join(temp_output_dir, "sd_optimized.jpg")
        cv2.imwrite(sd_optimized_path, sd_optimized)
        
        # Convert results to base64
        enhanced_images = {}
        result_files = {
            "original": original_path,
            "face_roi": face_roi_path, 
            "normalized": normalized_path,
            "sd_optimized": sd_optimized_path
        }
        
        for key, file_path in result_files.items():
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    img_data = f.read()
                    enhanced_images[key] = base64.b64encode(img_data).decode('utf-8')
        
        # Set SD optimized version as final enhanced image
        enhanced_images["final_enhanced"] = enhanced_images["sd_optimized"]
            
        return enhanced_images
        
    except Exception as e:
        st.warning(f"Advanced enhancement failed: {str(e)}, using simple enhancement instead.")
        # Fall back to simple enhancement if any errors occur
        return simple_enhance_ultrasound_image(image_base64, contrast_value, brightness_value)

def simple_enhance_ultrasound_image(image_base64, contrast_value=None, brightness_value=None):
    """Simple brightness and contrast enhancement"""
    # Use values from config if not provided
    contrast_value = contrast_value or ENHANCEMENT_SETTINGS["contrast"]
    brightness_value = brightness_value or ENHANCEMENT_SETTINGS["brightness"]
    
    # Convert base64 to image
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_bytes))
    
    # Apply contrast
    contrast_enhancer = ImageEnhance.Contrast(image)
    image = contrast_enhancer.enhance(contrast_value)
    
    # Apply brightness
    brightness_enhancer = ImageEnhance.Brightness(image)
    image = brightness_enhancer.enhance(brightness_value)
    
    # Convert back to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    enhanced_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    # Return dictionary for consistency
    return {
        "original": image_base64,
        "enhanced": enhanced_base64,
        "sd_optimized": enhanced_base64,
        "final_enhanced": enhanced_base64
    }

def save_temp_image(image, prefix="temp"):
    """Save image to temporary directory"""
    temp_dir = get_temp_dir()
    
    timestamp = int(time.time())
    filename = f"{prefix}_{timestamp}.png"
    filepath = temp_dir / filename
    
    image.save(filepath)
    
    return str(filepath)