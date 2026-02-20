# prompt2image

Generate images from text prompts using Google's Gemini image models. Works as a CLI tool or as an MCP server for Claude Code.

## Setup

```bash
pip install google-genai pillow mcp
export GEMINI_API_KEY='your-key'  # Get one at https://aistudio.google.com/apikey
```

## Models

| Key | Model | Notes |
|-----|-------|-------|
| `pro` | `gemini-3-pro-image-preview` | Best quality (default) |
| `flash` | `gemini-2.5-flash-image` | Faster, cheaper |

## CLI Usage

```bash
# Basic (reads prompt from file, saves image next to it)
python generate_poster.py examples/neural_network_diagram.txt

# Choose model and orientation
python generate_poster.py examples/climate_data_infographic.txt -m flash -o landscape

# Portrait, specific paper size
python generate_poster.py my_prompt.txt -o portrait -s A1
```

Options:
- `-m, --model` — `pro` (default) or `flash`
- `-o, --orientation` — `landscape` (default), `portrait`, or `square`
- `-s, --size` — Paper size (`A0`–`A4`), auto-selects closest aspect ratio

Output images are saved alongside the prompt file with a timestamp.

## MCP Server (Claude Code)

Add to your Claude Code MCP config (`~/.claude.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "prompt2image": {
      "command": "python",
      "args": ["/path/to/prompt2image/mcp_server.py"]
    }
  }
}
```

Then in Claude Code, the `generate_image` tool is available with parameters:
- `prompt` — The text prompt
- `filename` — Optional base filename
- `model` — `pro` or `flash`
- `aspect_ratio` — `16:9`, `9:16`, `1:1`, `4:3`, `3:4`

Images and prompts are saved in `outputs/` and `prompts/` in your current working directory.

## Examples

See [`examples/`](examples/) for sample prompts at different complexity levels.

## License

MIT
