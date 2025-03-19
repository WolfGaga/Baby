from PIL import Image
import numpy as np
import io
import base64

def rotate_image(image, angle):
    """
    Rotate an image by the specified angle
    
    Args:
        image (PIL.Image): Image to rotate
        angle (float): Angle in degrees
        
    Returns:
        PIL.Image: Rotated image
    """
    # Use PIL's rotate method with resample for better quality
    return image.rotate(angle, resample=Image.BICUBIC, expand=True)

def crop_image(image, box):
    """
    Crop an image to the specified box
    
    Args:
        image (PIL.Image): Image to crop
        box (tuple): Crop box (left, upper, right, lower)
        
    Returns:
        PIL.Image: Cropped image
    """
    return image.crop(box)

def image_to_base64(image):
    """
    Convert a PIL Image to base64 string
    
    Args:
        image (PIL.Image): Image to convert
        
    Returns:
        str: Base64 encoded string
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_to_image(base64_str):
    """
    Convert a base64 string to PIL Image
    
    Args:
        base64_str (str): Base64 encoded string
        
    Returns:
        PIL.Image: Converted image
    """
    image_bytes = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(image_bytes))
