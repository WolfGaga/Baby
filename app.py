import streamlit as st
import os
from pathlib import Path
import time

# Imoprt config
from config import get_temp_dir, get_output_dir, BASE_DIR

# create directory structure
get_temp_dir()
get_output_dir()

from frontend.ui import render_sidebar, render_main_page, render_instructions
from frontend.state import initialize_state
from backend.generation import process_generation
from utils.file_manager import cleanup_temp_files

st.set_page_config(
    page_title="Ultrasound to Baby Photo Generator", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize session state
    initialize_state()
    
    # Set title
    st.title("Ultrasound to Newborn Baby Photo Generator")
    st.write("Convert ultrasound images to realistic newborn photos using Stability AI")
    
    # Render instructions
    render_instructions()
    
    # Render sidebar UI elements and get inputs
    sidebar_inputs = render_sidebar()
    
    # Render main page UI elements and get inputs
    main_inputs, generate_button = render_main_page()
    
    # Add debug information if needed
    with st.sidebar.expander("Debug Info", expanded=False):
        st.write("Button clicked:", generate_button)
        st.write("Upload file exists:", main_inputs["uploaded_file"] is not None)
        st.write("Image base64 exists:", main_inputs["image_base64"] is not None)
        st.write("Enhanced images exist:", "enhanced_images" in st.session_state)
        st.write("Selected enhancement:", st.session_state.get("selected_enhancement", "None"))
        st.write("Session state keys:", list(st.session_state.keys()))
    
    # Handle generation requests
    if generate_button:
        # Record button click time
        st.session_state["button_clicked_timestamp"] = time.time()
        
        # Validate API key
        if not sidebar_inputs["api_key"]:
            st.error("Please enter your Stability AI API key")
            return
        
        # Validate image upload
        if main_inputs["uploaded_file"] is None and "last_source_image" not in st.session_state:
            st.error("Please upload an ultrasound image")
            return
        
        # Validate preprocessing selection status
        if "enhanced_images" in st.session_state:
            if "selected_enhancement" not in st.session_state:
                st.session_state["selected_enhancement"] = "sd_optimized" if "sd_optimized" in st.session_state["enhanced_images"] else "original"
            
            # Validate that selected enhancement exists in enhanced_images
            if st.session_state["selected_enhancement"] not in st.session_state["enhanced_images"]:
                # Select first available enhancement
                st.session_state["selected_enhancement"] = list(st.session_state["enhanced_images"].keys())[0]
                st.warning(f"Selected enhancement not available. Using {st.session_state['selected_enhancement']} instead.")
        
        # Reset conflicting flags
        for flag in ["force_regenerate", "prevent_auto_progress", "is_regenerating_stage"]:
            if flag in st.session_state:
                del st.session_state[flag]
        
        # Start generation process
        with st.spinner("Processing your request..."):
            st.session_state["_generation_started"] = time.time()
            process_generation(sidebar_inputs, main_inputs)
    
    # Handle regeneration requests (separate from normal generation)
    elif st.session_state.get("force_regenerate", False):
        # Validate API key for regeneration
        if not sidebar_inputs["api_key"]:
            st.error("Please enter your Stability AI API key")
            if "force_regenerate" in st.session_state:
                del st.session_state["force_regenerate"]
            return
            
        # Check for required images based on current stage
        current_stage = st.session_state.generation_stage
        
        # For stage 2, we need the outline image from stage 1
        if current_stage == 1 and "outline_image_base64" not in st.session_state:
            st.error("No outline image found for Stage 2. Please generate Stage 1 first.")
            st.session_state.generation_stage = 0  # Reset to stage 1
            if "force_regenerate" in st.session_state:
                del st.session_state["force_regenerate"]
            return
        
        # Check for any image source
        has_image_source = (
            main_inputs["uploaded_file"] is not None or 
            "last_source_image" in st.session_state or
            "enhanced_images" in st.session_state or
            (current_stage == 1 and "outline_image_base64" in st.session_state)
        )
        
        if has_image_source:
            # Store regeneration stage explicitly to prevent stage advancement
            regenerating_stage = st.session_state.get("is_regenerating_stage", current_stage)
            
            # Ensure we stay at the same stage during regeneration
            st.session_state.generation_stage = regenerating_stage
            
            # Clear flags but maintain important state
            if "force_regenerate" in st.session_state:
                del st.session_state["force_regenerate"]
            
            # Set explicit flags for regeneration mode
            st.session_state["is_regenerating"] = True
            st.session_state["prevent_auto_progress"] = True
            
            # Process the generation with these settings
            with st.spinner(f"Regenerating Stage {regenerating_stage + 1}..."):
                process_generation(sidebar_inputs, main_inputs)
        else:
            st.error("Please upload an ultrasound image for processing")
            if "force_regenerate" in st.session_state:
                del st.session_state["force_regenerate"]
    
    # Cleanup temporary files older than 1 hour
    cleanup_temp_files("data/temp", max_age_hours=1)

if __name__ == "__main__":
    main()
