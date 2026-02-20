#!/usr/bin/env python3
"""
Generic poster/illustration generator using Gemini 3 Pro Image.
Takes a text file with the prompt and generates an image.
Automatically saves versioned copies with timestamps.
"""

import os
import sys
import argparse
from datetime import datetime
from google import genai
from PIL import Image
from io import BytesIO
import base64
import shutil

# Initialize Gemini client
if 'GEMINI_API_KEY' not in os.environ:
    raise ValueError(
        "GEMINI_API_KEY not found in environment.\n"
        "Set it with: export GEMINI_API_KEY='your-key'\n"
        "Get your key at: https://aistudio.google.com/apikey"
    )

client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

# Available image generation models (best first)
IMAGE_MODELS = {
    'pro': 'models/gemini-3-pro-image-preview',      # Best quality, slower
    'flash': 'models/gemini-2.5-flash-image',         # Faster, cheaper
}
DEFAULT_MODEL = 'pro'

# Paper sizes (width x height in mm)
PAPER_SIZES = {
    'A0': (841, 1189),
    'A1': (594, 841),
    'A2': (420, 594),
    'A3': (297, 420),
    'A4': (210, 297),
}

# Gemini supported aspect ratios
GEMINI_ASPECT_RATIOS = ['1:1', '3:4', '4:3', '9:16', '16:9']

def get_closest_aspect_ratio(width, height):
    """Find the closest supported Gemini aspect ratio for given dimensions."""
    target_ratio = width / height

    ratios_map = {
        '1:1': 1.0,
        '3:4': 0.75,
        '4:3': 1.333,
        '9:16': 0.5625,
        '16:9': 1.778,
    }

    closest = min(ratios_map.items(), key=lambda x: abs(x[1] - target_ratio))
    return closest[0]

def generate_from_prompt_file(prompt_file, output_file=None, orientation='landscape', paper_size=None, model=None):
    """
    Generate an image from a prompt text file.

    Args:
        prompt_file: Path to text file containing the prompt
        output_file: Output image filename (auto-generated if None)
        orientation: 'landscape' or 'portrait' (default: 'landscape')
        paper_size: Paper size like 'A0', 'A1', etc. (overrides orientation)
        model: Model key ('pro' or 'flash') or None for default

    Returns:
        Path to generated image or None if failed
    """
    model_key = model or DEFAULT_MODEL
    image_model = IMAGE_MODELS.get(model_key)
    if not image_model:
        print(f"Error: Unknown model '{model_key}'. Available: {', '.join(IMAGE_MODELS.keys())}")
        return None

    # Read prompt from file
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
    except FileNotFoundError:
        print(f"Error: Prompt file '{prompt_file}' not found")
        return None
    except Exception as e:
        print(f"Error reading prompt file: {str(e)}")
        return None

    # Auto-generate output filename in the same directory as the prompt file
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(prompt_file))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_dir = os.path.dirname(os.path.abspath(prompt_file))
        output_file = os.path.join(prompt_dir, f"{base_name}_{timestamp}.png")

    # Determine aspect ratio
    if paper_size:
        if paper_size.upper() not in PAPER_SIZES:
            print(f"Error: Unknown paper size '{paper_size}'")
            print(f"Supported sizes: {', '.join(PAPER_SIZES.keys())}")
            return None

        width, height = PAPER_SIZES[paper_size.upper()]
        if orientation == 'landscape':
            width, height = height, width  # Swap for landscape

        aspect_ratio = get_closest_aspect_ratio(width, height)
        size_info = f"{paper_size.upper()} {orientation} ({width}×{height}mm → {aspect_ratio})"
    else:
        # Simple orientation-based aspect ratio
        if orientation == 'portrait':
            aspect_ratio = '9:16'
        elif orientation == 'square':
            aspect_ratio = '1:1'
        else:
            aspect_ratio = '16:9'
        size_info = f"{orientation} ({aspect_ratio})"

    print(f"Generating image from prompt: {prompt_file}")
    print(f"Output file: {output_file}")
    print(f"Using model: {image_model} ({model_key})")
    print(f"Size: {size_info}")
    print("\nThis may take 30-60 seconds...\n")

    try:
        # Generate image using Gemini 3 Pro Image with 4K and specified aspect ratio
        from google.genai import types

        response = client.models.generate_content(
            model=image_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size="4K"  # Must be uppercase K
                )
            )
        )

        print("Response received, processing image...")

        # Extract and save the generated image
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    if hasattr(part.inline_data, 'data') and part.inline_data.data is not None:
                        # Handle both raw bytes and base64-encoded data from Gemini API
                        raw_data = part.inline_data.data

                        if isinstance(raw_data, bytes):
                            # Check if it's raw image data (JPEG starts with 0xFF 0xD8, PNG with 0x89 PNG)
                            if raw_data[:2] == b'\xff\xd8' or raw_data[:4] == b'\x89PNG':
                                # It's already raw image bytes
                                image_data = raw_data
                            else:
                                # Try to decode as base64
                                try:
                                    image_data = base64.b64decode(raw_data)
                                except Exception:
                                    # If base64 decode fails, assume it's raw bytes
                                    image_data = raw_data
                        else:
                            # It's a string, decode from base64
                            image_data = base64.b64decode(raw_data)

                        print(f"Image received: {len(image_data)} bytes ({part.inline_data.mime_type})")

                        # Create BytesIO and ensure it's at the start
                        image_buffer = BytesIO(image_data)
                        image_buffer.seek(0)

                        # Try to open the image
                        try:
                            generated_img = Image.open(image_buffer)
                            generated_img.load()  # Force load to catch any errors early
                        except Exception as img_error:
                            print(f"PIL Error: {img_error}")
                            # Try saving raw bytes to debug
                            debug_file = os.path.join(os.path.dirname(output_file), "debug_image_raw.jpg")
                            with open(debug_file, 'wb') as f:
                                f.write(image_data)
                            print(f"Saved raw image data to {debug_file} for debugging")
                            raise

                        # Save the image
                        generated_img.save(output_file, format='PNG', dpi=(300, 300))

                        print(f"✓ Image generated successfully!")
                        print(f"✓ Saved to: {output_file}")
                        print(f"✓ Image size: {generated_img.size[0]} x {generated_img.size[1]} pixels")

                        # Display image info
                        print(f"\nImage details:")
                        print(f"  Format: {generated_img.format}")
                        print(f"  Mode: {generated_img.mode}")
                        print(f"  Size: {generated_img.size}")

                        return output_file

        print("Error: No image was generated in the response")
        return None

    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate posters/illustrations using Gemini 3 Pro Image',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s prompts/gdmi.txt
  %(prog)s prompts/gdmi.txt --orientation portrait
  %(prog)s prompts/gdmi.txt -o landscape
  %(prog)s prompts/gdmi.txt output.png --orientation portrait
        """
    )

    parser.add_argument('prompt_file', help='Path to text file containing the prompt')
    parser.add_argument('output_file', nargs='?', default=None,
                       help='Output image filename (auto-generated if not specified)')
    parser.add_argument('-o', '--orientation', choices=['landscape', 'portrait', 'square'],
                       default='portrait',
                       help='Image orientation (default: portrait). Use "square" for 1:1 aspect ratio.')
    parser.add_argument('-s', '--size', '--paper-size', dest='paper_size',
                       choices=['A0', 'A1', 'A2', 'A3', 'A4'],
                       help='Paper size (A0, A1, A2, A3, A4). Auto-selects closest aspect ratio.')
    parser.add_argument('-m', '--model', choices=list(IMAGE_MODELS.keys()),
                       default=DEFAULT_MODEL,
                       help=f'Model to use (default: {DEFAULT_MODEL}). Options: ' +
                            ', '.join(f'{k}={v}' for k, v in IMAGE_MODELS.items()))

    args = parser.parse_args()

    result = generate_from_prompt_file(args.prompt_file, args.output_file, args.orientation, args.paper_size, args.model)

    if result:
        print(f"\n{'='*60}")
        print("SUCCESS! Your image is ready.")
        print(f"{'='*60}")
        print(f"\nFile: {result}")
        print("\nYou can now:")
        print("  1. Open the image to review")
        print("  2. Print it for presentations/conferences")
        print("  3. Share it on social media")
        print("  4. Include it in your publications")
    else:
        print("\n" + "="*60)
        print("FAILED: Could not generate image")
        print("="*60)
        print("\nPlease check:")
        print("  1. GEMINI_API_KEY is set correctly")
        print("  2. You have API quota available")
        print("  3. The model supports image generation")
        print("  4. The prompt file exists and is readable")
        sys.exit(1)
