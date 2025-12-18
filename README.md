# AI Image Generator with Gemini

Generate high-quality images from text prompts using Google's Gemini 3 Pro Image model.

## Features

- Generate 4K images (16:9 aspect ratio) from text prompts
- Automatic timestamped filenames
- Web gallery to showcase generated images
- View generation prompts for each image
- Automatic deployment to GitHub Pages

## Repository Structure

```
.
├── generate_poster.py      # Main script to generate images from prompts
├── generate_gallery.py     # Script to build the HTML gallery
├── prompts/                # Text files containing generation prompts
├── outputs/                # Generated images (PNG format)
└── docs/                   # Gallery website (auto-deployed to GitHub Pages)
```

## Setup

1. **Get a Gemini API Key**
   - Visit https://aistudio.google.com/apikey
   - Create a new API key

2. **Set Environment Variable**
   ```bash
   export GEMINI_API_KEY='your-api-key-here'
   ```

3. **Install Dependencies**
   ```bash
   pip install google-genai pillow
   ```

## Usage

### Generate an Image

```bash
python generate_poster.py prompts/your-prompt.txt
```

This will:
- Read the prompt from the text file
- Generate a 4K image using Gemini 3 Pro Image
- Save it as `your-prompt_YYYYMMDD_HHMMSS.png` in the `outputs/` folder

### Generate Gallery

```bash
python generate_gallery.py
```

This scans the `prompts/` and `outputs/` directories and generates an HTML gallery at `docs/index.html`.

## Gallery Website

The gallery is automatically deployed to GitHub Pages when you push to the main branch.

View your gallery at: `https://[your-username].github.io/[repo-name]/`

### Features:
- Responsive grid layout
- Click images to view full size
- View generation prompts
- Download images
- Mobile-friendly design

## Creating New Images

1. Create a new `.txt` file in the `prompts/` directory with your prompt
2. Run: `python generate_poster.py prompts/your-prompt.txt`
3. Run: `python generate_gallery.py` to update the gallery
4. Commit and push to deploy

## GitHub Actions

The repository includes a GitHub Actions workflow that:
- Automatically regenerates the gallery
- Deploys to GitHub Pages
- Runs on every push to main/master

### Enable GitHub Pages

1. Go to your repository Settings
2. Navigate to Pages
3. Under "Build and deployment":
   - Source: GitHub Actions
4. The site will be deployed automatically

## Examples

Example prompts are included:
- `overall-lab.txt` - Complex multi-section infographic
- `sustainability_lab_prompt.txt` - Research lab visualization
- `join-us.txt` - Recruitment poster

## Notes

- Each generation takes 30-60 seconds
- Images are saved in PNG format with 300 DPI
- Timestamps prevent filename collisions
- The gallery automatically matches prompts to images

## License

MIT
