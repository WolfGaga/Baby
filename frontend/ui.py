import streamlit as st
from PIL import Image
import io
import base64
import os
import time  # Make sure time is imported
from utils.file_manager import save_image_to_file
from backend.image_editor import rotate_image, crop_image, image_to_base64
from config import (
    ETHNICITY_OPTIONS, ETHNICITY_PROMPTS, PROMPT_TEMPLATES,
    UI_TEXT, ERROR_MESSAGES, SUCCESS_MESSAGES, DEFAULT_SETTINGS,
    ENHANCEMENT_DISPLAY_NAMES, SKIN_TONE_OPTIONS
)

def render_instructions():
    """Render the instructions expander"""
    with st.expander("Instructions"):
        st.markdown(UI_TEXT["instructions"])

def render_sidebar():
    """Render the sidebar UI elements and return the inputs"""
    steps = DEFAULT_SETTINGS["steps"]
    guidance_scale = DEFAULT_SETTINGS["guidance_scale"]
    strength = DEFAULT_SETTINGS["strength"]
    control_strength = DEFAULT_SETTINGS["control_strength"]
    contrast = DEFAULT_SETTINGS["contrast"]
    brightness = DEFAULT_SETTINGS["brightness"]
    skin_tone = None
    
    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input("Stability AI API Key", type="password")
        st.info("Enter your API key from https://platform.stability.ai/account/keys")
        
        # Add a help button for the API key
        with st.expander("Help with API key"):
            st.markdown(UI_TEXT["api_key_help"])
        
        st.subheader("Baby Features")
        ethnicity = st.selectbox(
            "Ethnicity",
            ETHNICITY_OPTIONS,
            index=0
        )
        
        # Show skin tone selector only for stage 2
        if st.session_state.generation_stage == 2:
            # Get previous skin tone value to check for changes
            previous_skin_tone = st.session_state.get("skin_tone", "Medium")
            
            skin_tone = st.selectbox(
                "Adjust Skin Tone",
                SKIN_TONE_OPTIONS,
                index=SKIN_TONE_OPTIONS.index(previous_skin_tone) if previous_skin_tone in SKIN_TONE_OPTIONS else 2  # Default to Medium
            )
            
            # Update session state immediately when skin tone changes
            if skin_tone != previous_skin_tone:
                st.session_state.skin_tone = skin_tone
                # Force rerun to update prompt text areas with new skin tone
                st.rerun()
        
        st.subheader("Generation Settings")
        
        # Show current generation stage
        if st.session_state.generation_stage == 0:
            st.info("Stage: Initial outline generation")
            steps = st.slider("Steps", min_value=20, max_value=50, value=DEFAULT_SETTINGS["steps"])
            guidance_scale = st.slider("CFG Scale", min_value=1.0, max_value=10.0, value=DEFAULT_SETTINGS["guidance_scale"], step=0.1)
            strength = st.slider("Strength", min_value=0.3, max_value=0.9, value=DEFAULT_SETTINGS["strength"], step=0.05)
        elif st.session_state.generation_stage == 1:
            st.info("Stage: Final image generation")
            control_strength = st.slider("Control Strength", min_value=0.1, max_value=1.0, value=DEFAULT_SETTINGS["control_strength"], step=0.05)
            st.info("Control strength determines how closely the final image will follow the structure of the outline.")
            strength = 0
            steps = 0
            guidance_scale = 0
        elif st.session_state.generation_stage == 2:
            st.info("Stage: Skin tone adjustment")
            # For skin tone adjustment, use maximum control strength to maintain features
            control_strength = 1.0
            st.info("Using maximum control strength to preserve baby features while adjusting skin tone.")
            strength = 0
            steps = 0
            guidance_scale = 0
        
        # Advanced settings
        with st.expander("Advanced settings"):
            manual_stage = st.radio(
                "Manual stage selection", 
                ["Auto-progress", "Initial outline", "Final image", "Skin tone adjustment"],
                horizontal=True
            )
            
            if manual_stage == "Initial outline":
                st.session_state.generation_stage = 0
            elif manual_stage == "Final image":
                st.session_state.generation_stage = 1
            elif manual_stage == "Skin tone adjustment":
                st.session_state.generation_stage = 2
            
            # Reset button
            if st.button("Reset generation pipeline"):
                st.session_state.generation_stage = 0
                if "generated_image" in st.session_state:
                    del st.session_state.generated_image
                if "generated_image_base64" in st.session_state:
                    del st.session_state.generated_image_base64
                if "outline_image" in st.session_state:
                    del st.session_state.outline_image
                if "outline_image_base64" in st.session_state:
                    del st.session_state.outline_image_base64
                if "final_image" in st.session_state:
                    del st.session_state.final_image
                if "final_image_base64" in st.session_state:
                    del st.session_state.final_image_base64
                if "image_path" in st.session_state:
                    del st.session_state.image_path
                st.rerun()
        
        st.subheader("Preprocessing Settings")
        enhance_ultrasound = st.checkbox("Apply Advanced Enhancement", value=True)
        st.info("Uses multi-stage enhancement with face detection and contrast optimization")
        
        # Show these sliders only if advanced enhancement is not used
        if not enhance_ultrasound:
            contrast = st.slider("Simple Contrast", min_value=1.0, max_value=2.0, value=DEFAULT_SETTINGS["contrast"], step=0.1)
            brightness = st.slider("Simple Brightness", min_value=1.0, max_value=2.0, value=DEFAULT_SETTINGS["brightness"], step=0.1)
        else:
            contrast = DEFAULT_SETTINGS["contrast"]
            brightness = DEFAULT_SETTINGS["brightness"]
    
    return {
        "api_key": api_key,
        "ethnicity": ethnicity,
        "skin_tone": skin_tone,
        "steps": steps,
        "guidance_scale": guidance_scale,
        "strength": strength,
        "control_strength": control_strength,  
        "manual_stage": manual_stage,
        "enhance_ultrasound": enhance_ultrasound,
        "contrast": contrast,
        "brightness": brightness
    }

def render_main_page():
    """Render the main page UI elements and return the inputs and generate button"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Input")
        uploaded_file = st.file_uploader("Upload ultrasound image", type=["jpg", "jpeg", "png"])
        
        image_base64 = None
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded ultrasound image")
            
            # Convert to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # Automatically enhance image when uploaded
            if "enhanced_images" not in st.session_state or st.session_state.get("current_image_hash") != hash(image_base64):
                with st.spinner("Preprocessing ultrasound image..."):
                    # Save the hash of current image to avoid re-enhancing on page refresh
                    st.session_state["current_image_hash"] = hash(image_base64)
                    # Process the enhancement in the backend
                    try:
                        from backend.image_utils import enhance_ultrasound_image
                        enhanced_images = enhance_ultrasound_image(
                            image_base64,
                            contrast_value=1.3,
                            brightness_value=1.2
                        )
                        st.session_state["enhanced_images"] = enhanced_images
                        
                        # Default to sd_optimized or another good choice
                        if "sd_optimized" in enhanced_images:
                            st.session_state["selected_enhancement"] = "sd_optimized"
                        elif enhanced_images:
                            # Pick the first available enhancement
                            st.session_state["selected_enhancement"] = list(enhanced_images.keys())[0]
                        else:
                            # Fallback to original
                            st.session_state["selected_enhancement"] = "original"
                    except Exception as e:
                        st.error(f"Image enhancement failed: {str(e)}")
                        # Set enhanced_images with at least the original
                        st.session_state["enhanced_images"] = {"original": image_base64}
                        st.session_state["selected_enhancement"] = "original"
            
            # Show enhanced image preview and selection after upload
            if "enhanced_images" in st.session_state:
                st.write("### Select preprocessing version")
                
                # Create tabs for the different enhancement stages
                tab1, tab2 = st.tabs(["Quick Selection", "All Versions"])
                
                with tab1:
                    # Show 3 main options for quick selection
                    option_cols = st.columns(3)
                    
                    with option_cols[0]:
                        if "sd_optimized" in st.session_state["enhanced_images"]:
                            img_data = base64.b64decode(st.session_state["enhanced_images"]["sd_optimized"])
                            img = Image.open(io.BytesIO(img_data))
                            st.image(img, caption="SD Optimized")
                            if st.button("Use SD Optimized", key="select_sd_optimized_main"):
                                st.session_state["selected_enhancement"] = "sd_optimized"
                                st.success("Selected: SD Optimized")
                    
                    with option_cols[1]:
                        if "normalized" in st.session_state["enhanced_images"]:
                            img_data = base64.b64decode(st.session_state["enhanced_images"]["normalized"])
                            img = Image.open(io.BytesIO(img_data))
                            st.image(img, caption="Normalized")
                            if st.button("Use Normalized", key="select_normalized_main"):
                                st.session_state["selected_enhancement"] = "normalized"
                                st.success("Selected: Normalized")
                    
                    with option_cols[2]:
                        if "face_roi" in st.session_state["enhanced_images"]:
                            img_data = base64.b64decode(st.session_state["enhanced_images"]["face_roi"])
                            img = Image.open(io.BytesIO(img_data))
                            st.image(img, caption="Face ROI")
                            if st.button("Use Face ROI", key="select_face_roi_main"):
                                st.session_state["selected_enhancement"] = "face_roi"
                                st.success("Selected: Face ROI")
                
                with tab2:
                    # Show all available versions in a grid
                    st.write("All available enhancement versions:")
                    
                    # Display all available versions in a grid
                    all_cols = st.columns(3)
                    all_options = ["original", "face_roi", "normalized", "sd_optimized"]
                    
                    # English version names
                    option_names = {
                        "original": "Original Image",
                        "face_roi": "Face ROI",
                        "normalized": "Normalized",
                        "sd_optimized": "SD Optimized"
                    }
                    
                    # Display all versions
                    for i, opt in enumerate(all_options):
                        if opt in st.session_state["enhanced_images"]:
                            with all_cols[i % 3]:
                                img_data = base64.b64decode(st.session_state["enhanced_images"][opt])
                                img = Image.open(io.BytesIO(img_data))
                                display_name = option_names.get(opt, opt)
                                st.image(img, caption=display_name)
                                if st.button(f"Use {display_name}", key=f"select_{opt}_tab2"):
                                    st.session_state["selected_enhancement"] = opt
                                    st.success(f"Selected: {display_name}")
                
                # Show currently selected enhancement
                selected = st.session_state.get("selected_enhancement", "sd_optimized")
                
                # English display names - simplified to only include actual options
                display_names = ENHANCEMENT_DISPLAY_NAMES
                
                # Use the display names
                display_name = display_names.get(selected, selected.replace("_", " "))
                st.info(f"Currently selected version: {display_name}")
        
        # Generate ethnicity-specific prompts
        ethnicity = st.session_state.get("ethnicity", "Asian")
        ethnicity_prompt = ETHNICITY_PROMPTS[ethnicity]
        
        # Set stage-specific prompts with improved orientation guidance
        stage = st.session_state.generation_stage
        if stage == 0:
            default_positive = PROMPT_TEMPLATES["stage_0_positive"]
            default_negative = PROMPT_TEMPLATES["stage_0_negative"]
        elif stage == 1:
            default_positive = PROMPT_TEMPLATES["stage_1_positive"].format(ethnicity_prompt=ethnicity_prompt)
            default_negative = PROMPT_TEMPLATES["stage_1_negative"]
        elif stage == 2:
            # Always get the most current skin tone from session state
            skin_tone = st.session_state.get("skin_tone", "Medium")
            default_positive = PROMPT_TEMPLATES["stage_2_positive"].format(skin_tone=skin_tone, ethnicity=ethnicity)
            default_negative = PROMPT_TEMPLATES["stage_2_negative"]
        
        positive_prompt = st.text_area(
            "Positive prompt", 
            value=default_positive
        )
        
        negative_prompt = st.text_area(
            "Negative prompt", 
            value=default_negative
        )
        
        # Make generate button more prominent and simplify handling
        st.write("")
        st.write("Select a preprocessing version, then click the button below to generate the baby photo:")
        generate_button = st.button("Generate Baby Photo", type="primary")
    
    with col2:
        st.header("Output")
        if "generated_image" in st.session_state:
            # Display current stage
            stage_names = ["Initial Outline", "Final Image", "Skin Tone Adjusted"]
            st.caption(f"Stage {st.session_state.generation_stage+1}/3: {stage_names[st.session_state.generation_stage]}")
            
            # Add image editing tools
            with st.expander("Image Editor", expanded=False):
                # Get a copy of the current image for editing
                if "edit_image" not in st.session_state and "generated_image" in st.session_state:
                    st.session_state.edit_image = st.session_state.generated_image.copy()
                    st.session_state.edit_angle = 0
                    st.session_state.crop_coords = None
                    st.session_state.edit_image_base64 = st.session_state.get("generated_image_base64", "")
                elif "generated_image" not in st.session_state:
                    st.warning("No image available for editing.")
                    return
                
                # Rotation control
                col_rot1, col_rot2 = st.columns([3, 1])
                with col_rot1:
                    rotation_angle = st.slider("Rotation angle", -180, 180, st.session_state.edit_angle, 5)
                with col_rot2:
                    if st.button("Apply Rotation"):
                        # Apply rotation to the edit image
                        st.session_state.edit_image = rotate_image(st.session_state.generated_image, rotation_angle)
                        st.session_state.edit_angle = rotation_angle
                        # Update base64 string
                        st.session_state.edit_image_base64 = image_to_base64(st.session_state.edit_image)
                
                # Cropping controls
                st.write("Cropping (enter pixel coordinates):")
                col_crop1, col_crop2 = st.columns(2)
                with col_crop1:
                    img_width, img_height = st.session_state.edit_image.size
                    left = st.number_input("Left", 0, img_width-1, 0)
                    upper = st.number_input("Top", 0, img_height-1, 0)
                with col_crop2:
                    right = st.number_input("Right", left+1, img_width, img_width)
                    lower = st.number_input("Bottom", upper+1, img_height, img_height)
                
                if st.button("Apply Crop"):
                    crop_box = (left, upper, right, lower)
                    # Apply crop to the edit image
                    st.session_state.edit_image = crop_image(st.session_state.edit_image, crop_box)
                    # Update base64 string
                    st.session_state.edit_image_base64 = image_to_base64(st.session_state.edit_image)
                    # Reset crop coordinates for next operation
                    st.session_state.crop_coords = None
                
                # Reset button
                if st.button("Reset to Original"):
                    st.session_state.edit_image = st.session_state.generated_image.copy()
                    st.session_state.edit_angle = 0
                    st.session_state.crop_coords = None
                    st.session_state.edit_image_base64 = st.session_state.generated_image_base64
                
                # Show preview of edited image
                st.write("Edit Preview:")
                st.image(st.session_state.edit_image, caption="Edited Image")
                
                # Apply changes button
                if st.button("Use Edited Image", type="primary"):
                    if "edit_image" in st.session_state:
                        # Replace the generated image with the edited version
                        st.session_state.generated_image = st.session_state.edit_image
                        st.session_state.generated_image_base64 = image_to_base64(st.session_state.edit_image)
                        st.success("Image updated with edits!")
                        st.rerun()
            
            # Display image (using edited version if available and applied)
            display_image = st.session_state.generated_image
            st.image(display_image, caption="Generated Baby Photo")
            
            # Only show comparison in stage 2 or 3
            if st.session_state.generation_stage == 1 and "outline_image" in st.session_state:
                with st.expander("Compare with Outline", expanded=True):
                    cols = st.columns(2)
                    with cols[0]:
                        st.image(st.session_state.outline_image, caption="Stage 1: Outline")
                    with cols[1]:
                        st.image(st.session_state.generated_image, caption="Stage 2: Final Image")
            elif st.session_state.generation_stage == 2 and "final_image" in st.session_state:
                with st.expander("Compare with Previous Stage", expanded=True):
                    cols = st.columns(2)
                    with cols[0]:
                        st.image(st.session_state.final_image, caption="Stage 2: Final Image")
                    with cols[1]:
                        st.image(st.session_state.generated_image, caption="Stage 3: Skin Tone Adjusted")
            
            # Display save path if available
            if "image_path" in st.session_state:
                st.success(f"Image saved to: {st.session_state.image_path}")
            
            # Download button
            if "generated_image_base64" in st.session_state:
                buffered = io.BytesIO()
                st.session_state.generated_image.save(buffered, format="PNG")
                st.download_button(
                    label="Download Generated Photo",
                    data=buffered.getvalue(),
                    file_name=f"baby_stage_{st.session_state.generation_stage+1}.png",
                    mime="image/png"
                )
            
            # Save button
            col_save1, col_save2 = st.columns(2)
            with col_save1:
                save_filename = st.text_input("Filename", value=f"baby_stage_{st.session_state.generation_stage+1}")
            
            with col_save2:
                if st.button("Save to Disk"):
                    if "generated_image" in st.session_state:
                        image_path = save_image_to_file(
                            st.session_state.generated_image,
                            filename=save_filename,
                            directory="data/outputs"
                        )
                        st.session_state.image_path = image_path
                        st.success(f"Image saved to: {image_path}")
                        st.rerun()
            
            # Action buttons
            st.write("---")
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                # Regenerate button
                st.write("Regenerate with:")
                
                # Only show preprocessing options in stage 1
                if st.session_state.generation_stage == 0 and "enhanced_images" in st.session_state:
                    regen_options = ["current settings"]
                    
                    # Add available enhancement options
                    for option in ["sd_optimized", "normalized", "face_roi", "original"]:
                        if option in st.session_state["enhanced_images"]:
                            display_name = option.replace("_", " ").title()
                            regen_options.append(display_name)
                    
                    # Create selection box
                    regen_selection = st.selectbox(
                        "Preprocessing version:",
                        regen_options,
                        index=0,
                        key="regen_preprocessing_selection"
                    )
                    
                    # Map display names back to option keys
                    option_map = {
                        "Sd Optimized": "sd_optimized",
                        "Normalized": "normalized",
                        "Face Roi": "face_roi",
                        "Original": "original"
                    }
                elif st.session_state.generation_stage == 1:
                    # For Stage 2, show that ethnicity will be updated
                    st.info("Regeneration will use the latest ethnicity selection from the sidebar")
                elif st.session_state.generation_stage == 2:
                    # For skin tone adjustment stage
                    st.info("Regeneration will use the currently selected skin tone from the sidebar")
                
                regenerate_clicked = st.button(
                    "Regenerate This Stage", 
                    type="secondary", 
                    key=f"regenerate_button_{st.session_state.generation_stage}"
                )
                
                if regenerate_clicked:
                    # Clear any conflicting flags first
                    for flag in ["advancing_to_next_stage", "new_generation"]:
                        if flag in st.session_state:
                            del st.session_state[flag]
                    
                    # Apply preprocessing selection if not using current settings
                    if (st.session_state.generation_stage == 0 and 
                        "enhanced_images" in st.session_state and
                        regen_selection != "current settings"):
                        
                        # Convert display name back to option key
                        selected_key = option_map.get(regen_selection, regen_selection.lower())
                        
                        # Update selected enhancement if it exists
                        if selected_key in st.session_state["enhanced_images"]:
                            st.session_state["selected_enhancement"] = selected_key
                            st.success(f"Changed preprocessing to: {regen_selection}")
                            
                    # Set explicit flags for regeneration
                    st.session_state["force_regenerate"] = True
                    st.session_state["prevent_auto_progress"] = True
                    st.session_state["is_regenerating_stage"] = st.session_state.generation_stage
                    st.rerun()
            
            with col_action2:
                # Continue button - Only show if we're at stage 1 or 2
                if st.session_state.generation_stage < 2:
                    next_stage_name = "Final Image" if st.session_state.generation_stage == 0 else "Skin Tone Adjustment"
                    continue_clicked = st.button(
                        f"Continue to {next_stage_name}", 
                        type="primary", 
                        key=f"continue_button_{st.session_state.generation_stage}"
                    )
                    
                    if continue_clicked:
                        # Clear any conflicting flags first
                        for flag in ["is_regenerating_stage", "prevent_auto_progress", "new_generation"]:
                            if flag in st.session_state:
                                del st.session_state[flag]
                                
                        # Save the current stage image for later use
                        if "generated_image" in st.session_state:
                            if st.session_state.generation_stage == 0:
                                st.session_state.outline_image = st.session_state.generated_image
                                if "generated_image_base64" in st.session_state:
                                    st.session_state.outline_image_base64 = st.session_state.generated_image_base64
                            elif st.session_state.generation_stage == 1:
                                st.session_state.final_image = st.session_state.generated_image
                                if "generated_image_base64" in st.session_state:
                                    st.session_state.final_image_base64 = st.session_state.generated_image_base64
                        
                        # EXPLICIT STAGE ADVANCEMENT: Only advance when user clicks continue
                        st.session_state.generation_stage += 1
                        
                        # Set proper flags for stage advancement
                        st.session_state["force_regenerate"] = True
                        st.session_state["advancing_to_next_stage"] = True
                        st.rerun()
                else:
                    st.success("All stages completed! You can download the image or save it to disk.")
            
            # Add a Generate New Baby button with prominent styling
            st.write("---")
            new_baby_col1, new_baby_col2 = st.columns([2, 1])
            with new_baby_col1:
                st.write("Start over with a new generation:")
            with new_baby_col2:
                if st.button("Generate New Baby", type="primary", key="new_baby_button"):
                    # Reset the generation process but keep the uploaded image
                    st.session_state.generation_stage = 0
                    
                    # Clear generated images
                    for key in ["generated_image", "generated_image_base64", "outline_image", 
                               "outline_image_base64", "image_path", "edit_image", 
                               "edit_image_base64", "edit_angle", "crop_coords"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Clear all flags but set force_regenerate and new_generation
                    for key in list(st.session_state.keys()):
                        if key.startswith("is_") or key.startswith("force_") or key.startswith("prevent_"):
                            del st.session_state[key]
                            
                    # Set flag to force regenerate with the current image
                    st.session_state["force_regenerate"] = True
                    st.session_state["new_generation"] = True
                    
                    st.rerun()
    
    # Always show debug info to help diagnose issues
    with st.expander("Debug Information"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("Session state keys:", list(st.session_state.keys()))
            st.write("Generation stage:", st.session_state.get("generation_stage", "Not set"))
            st.write("Last button clicked:", st.session_state.get("last_button_clicked", "None"))
        with col2:
            st.write("Force regenerate flag:", st.session_state.get("force_regenerate", False))
            st.write("Last action:", st.session_state.get("_last_action", "None"))
            st.write("Generation attempts:", st.session_state.get("_generation_timestamp", 0))
            
        # Add a button to force clear session state
        if st.button("Clear Session State", key="debug_clear"):
            for key in list(st.session_state.keys()):
                if key != "generation_stage":
                    del st.session_state[key]
            st.session_state.generation_stage = 0
            st.rerun()

    return {
        "uploaded_file": uploaded_file,
        "image_base64": image_base64,
        "positive_prompt": positive_prompt,
        "negative_prompt": negative_prompt
    }, generate_button
