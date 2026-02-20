#!/usr/bin/env python3
"""
MCP Server for prompt2image - Generate images using Gemini 3 Pro Image.

Tools:
  - generate_image: Generate an image from a text prompt
  - view_prompt: View the prompt used for an existing image
"""

import os
import base64
from datetime import datetime
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize MCP server
server = Server("prompt2image")

# Available image generation models
IMAGE_MODELS = {
    'pro': 'models/gemini-3-pro-image-preview',      # Best quality, slower
    'flash': 'models/gemini-2.5-flash-image',         # Faster, cheaper
}
DEFAULT_MODEL = 'pro'

# Output to caller's working directory
CWD = Path.cwd()
OUTPUTS_DIR = CWD / "outputs"
PROMPTS_DIR = CWD / "prompts"


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="generate_image",
            description="Generate a 4K image from a text prompt using Gemini image models. Takes 30-60 seconds. Returns the path to the generated image. Saves outputs and prompts in the caller's working directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The text prompt describing the image to generate"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional base filename (without extension or timestamp)"
                    },
                    "model": {
                        "type": "string",
                        "description": f"Model to use: 'pro' (best quality, default) or 'flash' (faster). Available: {', '.join(IMAGE_MODELS.keys())}",
                        "enum": list(IMAGE_MODELS.keys()),
                        "default": DEFAULT_MODEL
                    },
                    "aspect_ratio": {
                        "type": "string",
                        "description": "Aspect ratio: '16:9' (landscape, default), '9:16' (portrait), '1:1' (square), '4:3', '3:4'",
                        "enum": ["16:9", "9:16", "1:1", "4:3", "3:4"],
                        "default": "16:9"
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="view_prompt",
            description="View the prompt that was used to generate an existing image",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_name": {
                        "type": "string",
                        "description": "Name or partial name of the image file in outputs/"
                    }
                },
                "required": ["image_name"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "generate_image":
        result = await generate_image(
            arguments.get("prompt", ""),
            arguments.get("filename"),
            arguments.get("model", DEFAULT_MODEL),
            arguments.get("aspect_ratio", "16:9")
        )
    elif name == "view_prompt":
        result = view_prompt(arguments.get("image_name", ""))
    else:
        result = f"Unknown tool: {name}"

    return [TextContent(type="text", text=str(result))]


async def generate_image(prompt: str, filename: str = None, model: str = None, aspect_ratio: str = "16:9") -> str:
    """Generate an image from a text prompt using Gemini image models."""
    try:
        from google import genai
        from google.genai import types
        from PIL import Image
        from io import BytesIO
    except ImportError as e:
        return f"Error: Missing dependency: {e}. Run: pip install google-genai pillow"

    if "GEMINI_API_KEY" not in os.environ:
        return "Error: GEMINI_API_KEY not set. Export it or add to ~/.zsh_secrets"

    # Resolve model
    model_key = model or DEFAULT_MODEL
    image_model = IMAGE_MODELS.get(model_key)
    if not image_model:
        return f"Error: Unknown model '{model_key}'. Available: {', '.join(IMAGE_MODELS.keys())}"

    # Ensure output directories exist (in caller's CWD)
    OUTPUTS_DIR.mkdir(exist_ok=True)
    PROMPTS_DIR.mkdir(exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if filename:
        base_name = filename.replace(".png", "").replace(" ", "-")
    else:
        words = prompt.split()[:3]
        base_name = "-".join(w.lower()[:10] for w in words if w.isalnum() or w[0].isalnum())
        base_name = "".join(c for c in base_name if c.isalnum() or c == "-")
        if not base_name:
            base_name = "image"

    output_file = OUTPUTS_DIR / f"{base_name}_{timestamp}.png"
    prompt_file = PROMPTS_DIR / f"{base_name}.txt"

    # Save prompt
    prompt_file.write_text(prompt)

    # Generate image
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

        response = client.models.generate_content(
            model=image_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size="4K"
                )
            )
        )

        # Extract image
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    if hasattr(part.inline_data, "data") and part.inline_data.data:
                        image_data = part.inline_data.data
                        if not isinstance(image_data, bytes):
                            image_data = base64.b64decode(image_data)

                        img = Image.open(BytesIO(image_data))
                        img.save(output_file, format="PNG", dpi=(300, 300))

                        return (
                            f"Image generated successfully!\n"
                            f"  Path: {output_file}\n"
                            f"  Size: {img.size[0]}x{img.size[1]} pixels\n"
                            f"  Model: {image_model} ({model_key})\n"
                            f"  Aspect ratio: {aspect_ratio}\n"
                            f"  Prompt saved: {prompt_file}"
                        )

        return "Error: No image in response from Gemini"

    except Exception as e:
        return f"Error generating image: {str(e)}"


def view_prompt(image_name: str) -> str:
    """View the prompt used for an existing image."""
    # Find the image
    image_path = None

    if (OUTPUTS_DIR / image_name).exists():
        image_path = OUTPUTS_DIR / image_name
    else:
        # Search for partial match
        for f in OUTPUTS_DIR.glob("*.png"):
            if image_name.lower() in f.name.lower():
                image_path = f
                break

    if not image_path:
        images = sorted([f.name for f in OUTPUTS_DIR.glob("*.png")])[-10:] if OUTPUTS_DIR.exists() else []
        if not images:
            return f"Image not found: {image_name}\n\nNo images found in {OUTPUTS_DIR}"
        return f"Image not found: {image_name}\n\nAvailable images in {OUTPUTS_DIR}:\n" + "\n".join(f"  - {i}" for i in images)

    # Find matching prompt
    base_name = image_path.stem
    parts = base_name.split("_")
    if len(parts) >= 2:
        prompt_name = "_".join(parts[:-2])
    else:
        prompt_name = base_name

    prompt_file = PROMPTS_DIR / f"{prompt_name}.txt"

    if prompt_file.exists():
        return f"Image: {image_path.name}\nPrompt file: {prompt_file.name}\n\n{prompt_file.read_text()}"

    # Try other matches
    for pf in PROMPTS_DIR.glob("*.txt"):
        if pf.stem in base_name:
            return f"Image: {image_path.name}\nPrompt file: {pf.name}\n\n{pf.read_text()}"

    return f"No prompt found for {image_path.name}"


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
