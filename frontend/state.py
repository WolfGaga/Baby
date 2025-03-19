import streamlit as st

def initialize_state():
    """Initialize the session state variables"""
    
    # Initialize generation stage if not already set
    if "generation_stage" not in st.session_state:
        st.session_state.generation_stage = 0
    
    # Initialize ethnicity for prompt generation
    if "ethnicity" not in st.session_state:
        st.session_state.ethnicity = "Asian"
    
    # Initialize generation history
    if "generation_history" not in st.session_state:
        st.session_state.generation_history = []
        
    # Initialize other commonly used flags to prevent KeyError
    if "force_regenerate" not in st.session_state:
        st.session_state.force_regenerate = False
        
    if "prevent_auto_progress" not in st.session_state:
        st.session_state.prevent_auto_progress = False
        
    if "selected_enhancement" not in st.session_state:
        st.session_state.selected_enhancement = "sd_optimized"
        
    # Initialize editor state
    if "edit_image" not in st.session_state and "generated_image" in st.session_state:
        st.session_state.edit_image = st.session_state.generated_image.copy()
        st.session_state.edit_angle = 0

def update_ethnicity(ethnicity):
    """Update the ethnicity in session state"""
    st.session_state.ethnicity = ethnicity

def save_to_history(image, image_base64, stage, prompt, seed=None):
    """Save the current generation to history"""
    if "generation_history" not in st.session_state:
        st.session_state.generation_history = []
    
    st.session_state.generation_history.append({
        "stage": stage,
        "image_base64": image_base64,
        "prompt": prompt,
        "seed": seed,
        "timestamp": st.session_state.get("_timestamp", "unknown")
    })

def get_history_item(index=-1):
    """Get an item from the generation history"""
    if "generation_history" in st.session_state and st.session_state.generation_history:
        if index == -1:
            return st.session_state.generation_history[-1]
        elif 0 <= index < len(st.session_state.generation_history):
            return st.session_state.generation_history[index]
    return None

def clear_history():
    """Clear the generation history"""
    if "generation_history" in st.session_state:
        st.session_state.generation_history = []

def prepare_for_regeneration():
    """Prepare the state for regeneration of the current stage"""
    # Keep the current stage but clear the generated image
    current_stage = st.session_state.generation_stage
    
    # Set regeneration flags
    st.session_state["prevent_auto_progress"] = True
    st.session_state["is_regenerating"] = True
    st.session_state["is_regenerating_stage"] = current_stage
    
    # If there's history for the previous stage, restore it
    previous_stage = current_stage - 1
    if previous_stage >= 0:
        for item in reversed(st.session_state.generation_history):
            if item["stage"] == previous_stage:
                # Found previous stage's last result
                st.session_state.generated_image_base64 = item["image_base64"]
                break
    else:
        # If we're regenerating the first stage, remove any generated image
        if "generated_image" in st.session_state:
            del st.session_state.generated_image
        if "generated_image_base64" in st.session_state:
            del st.session_state.generated_image_base64