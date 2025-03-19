# Ultrasound to Baby Photo Generator

This application uses Stability AI's image generation models to convert ultrasound images into realistic newborn baby photos through a two-stage process.

## Features

- Simple two-stage generation pipeline
- First stage captures basic structure from the ultrasound
- Second stage uses Stability AI's structure control technology to create photorealistic images
- Support for various ethnicity features
- Built-in image enhancement to improve ultrasound image quality
- Advanced settings for fine-tuning the generation process

## Project Structure

```
Baby_AI/
│
├── app.py              # Main Streamlit application entry point
│
├── frontend/
│   ├── __init__.py
│   ├── ui.py           # UI components and layout
│   └── state.py        # State management functions
│
├── backend/
│   ├── __init__.py
│   ├── api.py          # API interaction functions
│   ├── image_utils.py  # Image processing utilities
│   └── generation.py   # Generation pipeline logic
│
├── utils/
│   ├── __init__.py
│   └── file_manager.py # File saving and loading utilities
│
└── data/
    ├── temp/           # Temporary files
    └── outputs/        # Saved output images
```

## How It Works

The application uses a simplified two-stage approach:

1. **Initial Outline Stage**: Generates a basic structural outline from the ultrasound
2. **Final Image Stage**: Uses Stability AI's structure control to generate a realistic baby photo based on the outline

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/Baby_AI.git
cd Baby_AI
```

2. Install required packages:
```bash
pip install streamlit pillow requests
```

3. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Enter your Stability AI API key in the sidebar
2. Upload your ultrasound image
3. Select the baby's ethnicity features
4. Click "Generate Baby Photo" button
5. The app will guide you through the 2-stage process
6. Save or download the final image

## API Key

You need a valid Stability AI API key to use this application. Visit the [Stability AI website](https://stability.ai/) to apply for an API key.

## Technical Details

- Initial stage: Uses Stable Diffusion 3.5 image-to-image generation
- Final stage: Uses Stability AI's structure control endpoint
- API endpoints: 
  - https://api.stability.ai/v2beta/stable-image/generate/sd3
  - https://api.stability.ai/v2beta/stable-image/control/structure

## Tips

- Higher quality ultrasound images yield better results
- For best results, use 3D/4D ultrasound images
- Ensure the ultrasound clearly shows the baby's face
- You can adjust the control strength to determine how closely the final image follows the structure
