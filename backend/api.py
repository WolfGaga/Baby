import requests
import streamlit as st
from PIL import Image
import io
import base64
import time
import json
from config import API_ENDPOINTS, ERROR_MESSAGES

def generate_baby_image(api_key, image_data, positive_prompt, negative_prompt, steps=None, guidance_scale=None, strength=None):
    """
    Use Stability AI API to generate a baby photo from an ultrasound image
    
    Args:
        api_key (str): Stability AI API key
        image_data (bytes): Image data as bytes
        positive_prompt (str): Positive prompt for generation
        negative_prompt (str): Negative prompt for generation
        steps (int): Number of steps for generation
        guidance_scale (float): CFG scale for generation
        strength (float): Image strength (lower values preserve more details)
        
    Returns:
        tuple: (PIL.Image, str, str) - (generated image, base64 string, seed)
    """
    # Import here to avoid circular imports
    from config import DEFAULT_SETTINGS
    
    # Use the correct endpoint for SD3 image-to-image generation
    url = API_ENDPOINTS["generate"]
    
    # Use default values from config if not provided
    steps = steps or DEFAULT_SETTINGS["steps"]
    guidance_scale = guidance_scale or DEFAULT_SETTINGS["guidance_scale"]
    strength = strength or DEFAULT_SETTINGS["strength"]
    
    headers = {
        "Accept": "image/*",  # Request the image directly
        "Authorization": f"Bearer {api_key}"
    }
    
    # Open and resize the image if needed
    img = Image.open(io.BytesIO(image_data))
    
    # Resize if larger than 1024x1024 (API preference)
    if img.width > 1024 or img.height > 1024:
        img.thumbnail((1024, 1024))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Create multipart/form-data
    files = {
        "image": ("image.png", img_byte_arr, "image/png")
    }
    
    # Form data as per the API documentation
    form_data = {
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "mode": "image-to-image",  # Required for image-to-image
        "model": "sd3.5-large",    # Using SD3.5 Large model
        "strength": str(strength),
        "cfg_scale": str(guidance_scale),
        "output_format": "png"
    }
    
    # Add debug info to session state
    st.session_state["debug_request"] = {
        "url": url,
        "headers": {k: (v if k != "Authorization" else "Bearer ***API_KEY_HIDDEN***") for k, v in headers.items()},
        "form_data": form_data
    }
    
    try:
        with st.spinner("Generating... may take 10-30 seconds"):
            # Make the API request
            response = requests.post(
                url, 
                headers=headers,
                files=files,
                data=form_data,
                timeout=60  # 60 second timeout
            )
            
            # Store response info for debugging
            st.session_state["debug_response"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content) if response.content else 0
            }
            
            if response.status_code == 200:
                # The API returns the image directly as binary data
                image_bytes = response.content
                generated_image = Image.open(io.BytesIO(image_bytes))
                
                # We need to convert the binary data to base64 for storage
                buffered = io.BytesIO()
                generated_image.save(buffered, format="PNG")
                generated_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                # Get seed from headers
                seed = response.headers.get("seed", "0")
                
                return generated_image, generated_image_base64, seed
            else:
                with st.expander("API Error Details", expanded=True):
                    st.error(f"API Error: {response.status_code}")
                    st.write("Response headers:", dict(response.headers))
                    try:
                        st.write("Response body:", response.json())
                    except:
                        st.write("Response text:", response.text[:500])
                    
                    if response.status_code == 401:
                        st.error("Authentication error - Your API key is invalid or expired")
                        st.info("Get a new key at https://platform.stability.ai/account/keys")
                    elif response.status_code == 403:
                        st.error("Authorization error - Your account may not have sufficient credits")
                
                return None, None, None
                
    except Exception as e:
        st.error(ERROR_MESSAGES["connection_error"].format(error=str(e)))
        with st.expander("Error Details", expanded=True):
            import traceback
            st.code(traceback.format_exc())
        return None, None, None

def generate_with_control_structure(api_key, image_data, positive_prompt, negative_prompt=None, control_strength=None):
    """
    Use Stability AI's structure control API to generate a baby photo
    
    Args:
        api_key (str): Stability AI API key
        image_data (bytes): Image data as bytes (outline image to use as structure)
        positive_prompt (str): Positive prompt for generation
        negative_prompt (str): Negative prompt for generation
        control_strength (float): How much influence the structure has (0-1)
        
    Returns:
        tuple: (PIL.Image, str) - (generated image, base64 string)
    """
    # Import here to avoid circular imports
    from config import DEFAULT_SETTINGS
    
    # Use the correct structure control endpoint
    url = API_ENDPOINTS["control_structure"]
    
    # Use default value from config if not provided
    control_strength = control_strength or DEFAULT_SETTINGS["control_strength"]
    
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Open and prepare the image
    img = Image.open(io.BytesIO(image_data))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Create multipart/form-data
    files = {
        "image": ("image.png", img_byte_arr, "image/png")
    }
    
    # Prepare form data according to API documentation
    form_data = {
        "prompt": positive_prompt,
        "control_strength": str(control_strength),
        "output_format": "png"
    }
    
    # Add negative prompt if provided
    if negative_prompt:
        form_data["negative_prompt"] = negative_prompt
    
    # Add debug info
    st.session_state["debug_request"] = {
        "url": url,
        "headers": {k: (v if k != "Authorization" else "Bearer ***API_KEY_HIDDEN***") for k, v in headers.items()},
        "form_data": form_data
    }
    
    try:
        with st.spinner("Generating final image using structure control..."):
            response = requests.post(
                url, 
                headers=headers,
                files=files,
                data=form_data,
                timeout=90  # Longer timeout for structure control
            )
            
            # Store response info for debugging
            st.session_state["debug_response"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content) if response.content else 0
            }
            
            if response.status_code == 200:
                # The API returns the image directly as binary data
                image_bytes = response.content
                generated_image = Image.open(io.BytesIO(image_bytes))
                
                # Convert to base64 for storage
                buffered = io.BytesIO()
                generated_image.save(buffered, format="PNG")
                generated_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                # Get seed from headers if available
                seed = response.headers.get("seed", "0")
                
                return generated_image, generated_image_base64
            else:
                with st.expander("API Error Details", expanded=True):
                    st.error(f"API Error: {response.status_code}")
                    st.write("Response headers:", dict(response.headers))
                    try:
                        st.write("Response body:", response.json())
                    except:
                        st.write("Response text:", response.text[:500])
                    
                    if response.status_code == 401:
                        st.error("Authentication error - Your API key is invalid or expired")
                        st.info("Get a new key at https://platform.stability.ai/account/keys")
                    elif response.status_code == 403:
                        st.error("Authorization error - Your account may not have sufficient credits")
                
                return None, None
                
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        with st.expander("Error Details", expanded=True):
            import traceback
            st.code(traceback.format_exc())
        return None, None

def check_api_key(api_key):
    """
    Check if the API key is valid by making a simple request to list engines
    
    Args:
        api_key (str): Stability AI API key
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Basic format check
    if not api_key or len(api_key.strip()) < 20:
        return False
    
    # Test the API key by making a simple request to list engines
    url = API_ENDPOINTS["list_engines"]
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # Store response for debugging
        st.session_state["api_key_check"] = {
            "status_code": response.status_code,
            "response": response.text[:100] + ("..." if len(response.text) > 100 else "")
        }
        
        # If we get a 200 response, the key is valid
        return response.status_code == 200
        
    except Exception as e:
        st.session_state["api_key_check_error"] = str(e)
        return False