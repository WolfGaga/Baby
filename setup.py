import os
import shutil
from pathlib import Path

def setup_directory_structure():
    """Set up the proper directory structure for the application"""
    base_dir = Path('.')
    
    # Create directory structure
    for directory in ['frontend', 'backend', 'utils', 'data/temp', 'data/outputs']:
        (base_dir / directory).mkdir(parents=True, exist_ok=True)
    
    # File mapping: original -> new
    file_mapping = {
        'utils-file-manager.py': 'utils/file_manager.py',
        'frontend-ui.py': 'frontend/ui.py',
        'frontend-state.py': 'frontend/state.py',
        'backend-api.py': 'backend/api.py',
        'backend-image-utils.py': 'backend/image_utils.py',
        'backend-generation.py': 'backend/generation.py'
    }
    
    # Create __init__.py files
    for directory in ['frontend', 'backend', 'utils']:
        with open(f'{directory}/__init__.py', 'w') as f:
            f.write('# Module initialization file\n')
    
    # Copy file contents to new locations
    for original, new in file_mapping.items():
        if os.path.exists(original):
            # Read content from original file
            with open(original, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Write content to new file
            with open(new, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Moved content from {original} to {new}")
    
    print("\nDirectory structure set up successfully.")
    print("You can now delete the original files and run the application with:")
    print("streamlit run app.py")

if __name__ == "__main__":
    setup_directory_structure()
