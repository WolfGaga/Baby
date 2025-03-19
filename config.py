import os
from pathlib import Path

# Base paths and directories
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = BASE_DIR / "data" / "temp"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

# File paths should be created at runtime
def get_temp_dir():
    """Get the temporary directory path and ensure it exists"""
    temp_dir = BASE_DIR / "data" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir

def get_output_dir():
    """Get the output directory path and ensure it exists"""
    output_dir = BASE_DIR / "data" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

# API endpoints
API_ENDPOINTS = {
    "generate": "https://api.stability.ai/v2beta/stable-image/generate/sd3",
    "control_structure": "https://api.stability.ai/v2beta/stable-image/control/structure",
    "list_engines": "https://api.stability.ai/v1/engines/list"
}

# Default generation settings
DEFAULT_SETTINGS = {
    "steps": 35,
    "guidance_scale": 8.5,
    "strength": 0.65,
    "control_strength": 0.85,
    "contrast": 1.3,
    "brightness": 1.2
}

# Image enhancement settings
ENHANCEMENT_SETTINGS = {
    "contrast": 1.5,
    "brightness": 1.2,
    "clahe_clip_limit": 2.0,
    "clahe_grid_size": (8, 8),
    "denoise_h": 7,
    "denoise_template_window_size": 5,
    "denoise_search_window_size": 21
}

# Ethnicity options and prompts
ETHNICITY_OPTIONS = [
    "Asian", "Caucasian", "African", "Latino", "Middle Eastern", "South Asian", "Mixed"
]

ETHNICITY_PROMPTS = {
    "Asian": "Asian baby features, ",
    "Caucasian": "Caucasian baby features, ",
    "African": "African baby features, ",
    "Latino": "Latino baby features, ",
    "Middle Eastern": "Middle Eastern baby features, ",
    "South Asian": "South Asian baby features, ",
    "Mixed": ""
}

# Prompt templates
PROMPT_TEMPLATES = {
    "stage_0_positive": "Photo of a sleeping newborn baby head based on the image. Head only, no body, matching the exact facial orientation as input image. Detailed face structure with prominent facial features.",
    "stage_1_positive": "Portrait of a sleeping beautiful newborn baby with {ethnicity_prompt}NO HAT, natural hair, clearly visible hairline, wrapped in soft blanket, swaddled tightly with only face visible, white background. matching the exact facial orientation as input image.",
    "stage_0_negative": "Open eyes, Ugly, Weird Mouth, Crooked Mouth, twisted limbs, bad skin, wrinkles, uneven face, open mouth, lowers, bad anatomy, bad hands, missing fingers, extra digits, cropped, worst quality, low quality, mutant",
    "stage_1_negative": "different facial orientation, hat, cap, beanie, head covering, head wrap, headwear, Multiple eyebrows, Asymmetrical eyes, Open eyes, visible limbs, hands, arms, fingers, feet, legs, exposed body parts, ugly, weird mouth, cropped, bad anatomy, deformities, blurry, low quality, unrealistic skin texture, uneven face"
}

# UI text
UI_TEXT = {
    "api_key_help": """
    ## How to get your API key
    
    1. Go to [Stability AI platform](https://platform.stability.ai/)
    2. Create an account or log in
    3. Navigate to Account → API Keys
    4. Create a new API key if you don't have one
    5. Copy and paste the key here
    
    Make sure you have sufficient credits for image generation.
    """,
    "instructions": """
    ### How to use:
    1. Enter your Stability AI API key in the sidebar
    2. Upload your ultrasound image
    3. Select baby ethnicity features
    4. Click "Generate Baby Photo" button
    5. The app will guide you through a 2-stage process:
       - **Stage 1:** Initial outline - Captures basic structure from ultrasound
       - **Stage 2:** Final image - Creates photorealistic baby photo using structure control

    ### Two-stage Process:
    The application uses a simplified approach to transform your ultrasound into a realistic photo:
    
    1. **Initial outline stage:** Focuses on capturing the basic shape and contours of the baby's face from the ultrasound
    2. **Final image stage:** Uses advanced structure control to generate a realistic baby photo based on the outline
    
    Each stage builds upon the previous one, preserving the uniqueness of your baby's features from the ultrasound.
    """
}

# Error messages
ERROR_MESSAGES = {
    "no_api_key": "Please enter your Stability AI API key",
    "invalid_api_key": "Please enter a valid Stability AI API key",
    "no_image": "Please upload an ultrasound image",
    "no_outline": "No outline image found. Please generate an outline first.",
    "generation_failed": "Generation failed. Please try again.",
    "enhancement_failed": "Image enhancement failed: {error}",
    "connection_error": "Connection error: {error}"
}

# Success messages
SUCCESS_MESSAGES = {
    "stage_completed": "Stage {stage}/2 completed successfully!",
    "image_saved": "Image saved to: {path}",
    "using_enhancement": "✅ Using {enhancement} preprocessing version",
    "regenerating": "♻️ Regenerating using {enhancement} preprocessing version"
}

# Display names for enhancement options
ENHANCEMENT_DISPLAY_NAMES = {
    "sd_optimized": "SD Optimized",
    "normalized": "Normalized",
    "face_roi": "Face ROI",
    "original": "Original Image"
}
