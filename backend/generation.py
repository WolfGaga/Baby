import streamlit as st
import base64
from PIL import Image
import io
import os
import time

from backend.api import generate_baby_image, generate_with_control_structure, check_api_key
from backend.image_utils import enhance_ultrasound_image, save_temp_image
from frontend.state import save_to_history, update_ethnicity
from utils.file_manager import save_image_to_file
from config import (
    ETHNICITY_PROMPTS, PROMPT_TEMPLATES, ERROR_MESSAGES, 
    SUCCESS_MESSAGES, get_output_dir
)

def process_generation(sidebar_inputs, main_inputs):
    """
    Process the generation request
    
    Args:
        sidebar_inputs (dict): Inputs from the sidebar
        main_inputs (dict): Inputs from the main page
    """
    api_key = sidebar_inputs["api_key"]
    ethnicity = sidebar_inputs["ethnicity"]
    skin_tone = sidebar_inputs.get("skin_tone")
    control_strength = sidebar_inputs.get("control_strength", 0.85)
    steps = sidebar_inputs.get("steps", 35)
    guidance_scale = sidebar_inputs.get("guidance_scale", 8.5)
    strength = sidebar_inputs.get("strength", 0.65)
    manual_stage = sidebar_inputs["manual_stage"]
    enhance_ultrasound = sidebar_inputs["enhance_ultrasound"]
    contrast = sidebar_inputs["contrast"]
    brightness = sidebar_inputs["brightness"]
    
    uploaded_file = main_inputs["uploaded_file"]
    image_base64 = main_inputs["image_base64"]
    positive_prompt = main_inputs["positive_prompt"]
    negative_prompt = main_inputs["negative_prompt"]
    
    # Update ethnicity in session state
    update_ethnicity(ethnicity)
    
    # Always use the latest ethnicity and update prompts when regenerating
    if st.session_state.generation_stage >= 1 and st.session_state.get("is_regenerating", False):
        # Update prompt with the current ethnicity if it's a default prompt
        ethnicity_prompt = ETHNICITY_PROMPTS[ethnicity]
        if st.session_state.generation_stage == 1:
            positive_prompt = PROMPT_TEMPLATES["stage_1_positive"].format(ethnicity_prompt=ethnicity_prompt)
            st.info(f"Updated prompt with {ethnicity} ethnicity features")
        elif st.session_state.generation_stage == 2 and skin_tone:
            previous_skin_tone = st.session_state.get("previous_skin_tone", "Medium")
            positive_prompt = PROMPT_TEMPLATES["stage_2_positive"].format(skin_tone=skin_tone, ethnicity=ethnicity)
            
            # Show a message specific to skin tone change
            if previous_skin_tone != skin_tone:
                st.info(f"Adjusting skin tone from {previous_skin_tone} to {skin_tone}")
            else:
                st.info(f"Regenerating with {skin_tone} skin tone")
            
            # Save current skin tone for next comparison
            st.session_state["previous_skin_tone"] = skin_tone
    
    # Validate inputs
    if not api_key:
        st.error(ERROR_MESSAGES["no_api_key"])
        return
    
    # Set status to inform user
    status = st.empty()
    status.info("Starting generation process...")
    
    try:
        # Simple API key check
        if not check_api_key(api_key):
            st.error(ERROR_MESSAGES["invalid_api_key"])
            st.info("You can get your API key from https://platform.stability.ai/account/keys")
            return
        
        # Handle based on stage with better user feedback
        if st.session_state.generation_stage == 0:
            status.info("Stage 1: Generating initial baby head photo...")
            
            # Check for input image or pre-enhanced image
            if not (uploaded_file or "enhanced_images" in st.session_state):
                st.error(ERROR_MESSAGES["no_image"])
                return
                
            # If we have enhanced images, use the selected one
            if "enhanced_images" in st.session_state:
                # Get selected enhancement type
                selected_enhancement = st.session_state.get("selected_enhancement", "sd_optimized")
                
                if selected_enhancement in st.session_state["enhanced_images"]:
                    processed_image_base64 = st.session_state["enhanced_images"][selected_enhancement]
                    
                    # Show more prominent message about which preprocessing version is used
                    enhanced_label = selected_enhancement.replace("_", " ").title()
                    if st.session_state.get("is_regenerating", False):
                        st.info(f"♻️ Regenerating using {enhanced_label} preprocessing version")
                    else:
                        st.success(f"✅ Using {enhanced_label} preprocessing version")
                else:
                    # Fallback if selected enhancement is not available
                    if "sd_optimized" in st.session_state["enhanced_images"]:
                        processed_image_base64 = st.session_state["enhanced_images"]["sd_optimized"]
                        st.info("Selected enhancement not available, using SD Optimized instead")
                    else:
                        # Final fallback to original
                        processed_image_base64 = image_base64
                        st.warning("Enhanced versions not available, using original image")
            else:
                # Use original image if no enhancement was done
                processed_image_base64 = image_base64
            
            # Store the source image for potential future regeneration
            if processed_image_base64:
                st.session_state["last_source_image"] = processed_image_base64
            
            # Decode the image for the API
            source_image_bytes = base64.b64decode(processed_image_base64)
            
            # Generate the outline image with progress indicator
            progress_bar = st.progress(0)
            for i in range(5):
                progress_bar.progress((i+1) * 20)
                if i < 4:  # Don't sleep on last iteration
                    time.sleep(0.5)
            
            generated_image, generated_image_base64, seed = generate_baby_image(
                api_key, 
                source_image_bytes, 
                positive_prompt, 
                negative_prompt,
                steps,
                guidance_scale,
                strength
            )
            progress_bar.empty()
            
        elif st.session_state.generation_stage == 1:
            status.info("Stage 2: Generating final image using structure control...")
            
            # Check for outline image
            if "outline_image_base64" not in st.session_state:
                st.error(ERROR_MESSAGES["no_outline"])
                return
            
            # Get outline image
            outline_image_base64 = st.session_state.outline_image_base64
            outline_image_bytes = base64.b64decode(outline_image_base64)
            
            # Display debug information
            st.write(f"Generating final image using outline as structure control...")
            
            # Generate the final image with progress indicator
            progress_bar = st.progress(0)
            for i in range(5):
                progress_bar.progress((i+1) * 20)
                if i < 4:  # Don't sleep on last iteration
                    time.sleep(0.5)
                    
            generated_image, generated_image_base64 = generate_with_control_structure(
                api_key,
                outline_image_bytes,
                positive_prompt,
                negative_prompt,
                control_strength
            )
            progress_bar.empty()
            
            # Check if generation was successful
            if generated_image is None:
                st.error(ERROR_MESSAGES["generation_failed"])
                return
                
            seed = None  # Control structure doesn't return a seed
        
        elif st.session_state.generation_stage == 2:
            status.info("Stage 3: Adjusting skin tone while preserving features...")
            
            # Check for final image
            if "final_image_base64" not in st.session_state:
                st.error("No final image found. Please generate a final image first.")
                return
            
            # Get final image for structure control
            final_image_base64 = st.session_state.final_image_base64
            final_image_bytes = base64.b64decode(final_image_base64)
            
            # Display debug information
            st.write(f"Adjusting skin tone to {skin_tone} while preserving features...")
            
            # Generate the skin tone adjusted image with progress indicator
            progress_bar = st.progress(0)
            for i in range(5):
                progress_bar.progress((i+1) * 20)
                if i < 4:  # Don't sleep on last iteration
                    time.sleep(0.5)
                    
            # Always use control_strength of 1.0 for skin tone adjustment
            generated_image, generated_image_base64 = generate_with_control_structure(
                api_key,
                final_image_bytes,
                positive_prompt,
                negative_prompt,
                1.0  # Maximum control strength to preserve features
            )
            progress_bar.empty()
            
            # Check if generation was successful
            if generated_image is None:
                st.error(ERROR_MESSAGES["generation_failed"])
                return
                
            seed = None  # Control structure doesn't return a seed
        
        # Save results if image generated successfully
        if generated_image:
            status.success(SUCCESS_MESSAGES["stage_completed"].format(stage=st.session_state.generation_stage + 1))
            
            # Directly set session state variables without deleting first
            st.session_state.generated_image = generated_image 
            st.session_state.generated_image_base64 = generated_image_base64
            st.session_state.generation_completed = True
            
            # Debug output to verify stage and image
            st.write(f"Generation successful for stage {st.session_state.generation_stage + 1}/3")
            
            # Save to history
            save_to_history(
                generated_image,
                generated_image_base64,
                st.session_state.generation_stage,
                positive_prompt,
                seed
            )
            
            # Save image to disk
            stage_label = ["outline", "final", "skin_adjusted"][st.session_state.generation_stage]
            output_dir = get_output_dir()
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = int(time.time())
            output_filename = f"baby_{stage_label}_{timestamp}.png"
            output_path = os.path.join(output_dir, output_filename)
            
            # Save to disk
            generated_image.save(output_path)
            st.session_state.image_path = output_path
            
            # FIXED: Completely disable auto-progress
            # Only continue to next stage when the user clicks "Continue to Final Image"
            # Removed auto-progress logic that was causing automatic stage advancement
            
            # If this is stage 1, save outline image for potential later use
            if st.session_state.generation_stage == 0:
                st.session_state.outline_image = generated_image
                st.session_state.outline_image_base64 = generated_image_base64
            
            # If this is stage 1, save final image for potential later use in skin tone adjustment
            if st.session_state.generation_stage == 1:
                st.session_state.final_image = generated_image
                st.session_state.final_image_base64 = generated_image_base64
            
            # Clear regeneration flags to prevent automatic stage advancement
            for flag in ["force_regenerate", "prevent_auto_progress", 
                         "regenerate_clicked", "new_generation", 
                         "is_regenerating", "is_regenerating_stage"]:
                if flag in st.session_state:
                    del st.session_state[flag]
            
            st.rerun()
        else:
            status.error(ERROR_MESSAGES["generation_failed"])
    
    except Exception as e:
        status.error(f"An error occurred: {str(e)}")
        st.error(f"Generation error: {str(e)}")
        
        # Show detailed debug info
        with st.expander("Debug Information", expanded=True):
            st.write("Error details:", str(e))
            st.write("Stage:", st.session_state.generation_stage)
            st.write("Check your API key and network connection")
            import traceback
            st.code(traceback.format_exc())
