#!/usr/bin/env python3
"""
Generate gallery HTML from images and prompts in the repository.
"""

import os
import json
from pathlib import Path
from datetime import datetime

def extract_date_from_filename(filename):
    """Extract date from filename with format: name_YYYYMMDD_HHMMSS.png"""
    try:
        # Split by underscore and look for timestamp pattern
        parts = filename.replace('.png', '').split('_')
        if len(parts) >= 2:
            # Last two parts should be date and time
            date_str = parts[-2]
            if len(date_str) == 8 and date_str.isdigit():
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return f"{year}-{month}-{day}"
    except:
        pass
    return datetime.now().strftime("%Y-%m-%d")

def find_matching_prompt(image_name, prompts):
    """Find the matching prompt file for an image."""
    # Remove timestamp and extension from image name
    base_name = image_name.replace('.png', '')
    # Remove timestamp pattern (YYYYMMDD_HHMMSS)
    parts = base_name.split('_')
    if len(parts) >= 2:
        # Try removing last two parts (date and time)
        name_without_timestamp = '_'.join(parts[:-2])
        for prompt in prompts:
            if prompt.replace('.txt', '') == name_without_timestamp:
                return prompt

    # Fallback: try exact match
    for prompt in prompts:
        if prompt.replace('.txt', '') in base_name:
            return prompt

    return None

def generate_title(filename):
    """Generate a human-readable title from filename."""
    # Remove extension and timestamp
    base = filename.replace('.png', '')
    parts = base.split('_')
    # Remove timestamp parts
    if len(parts) >= 2:
        title_parts = parts[:-2]
    else:
        title_parts = parts

    # Convert to title case
    title = ' '.join(title_parts).replace('_', ' ').title()
    return title

def generate_gallery():
    """Generate the gallery data and HTML."""

    outputs_dir = Path('outputs')
    prompts_dir = Path('prompts')

    # Get all images and prompts
    images = sorted([f.name for f in outputs_dir.glob('*.png')], reverse=True)
    prompts = [f.name for f in prompts_dir.glob('*.txt')]

    # Build image data
    gallery_data = []
    for img in images:
        prompt_file = find_matching_prompt(img, prompts)
        if prompt_file:
            gallery_data.append({
                'filename': img,
                'promptFile': prompt_file,
                'title': generate_title(img),
                'date': extract_date_from_filename(img)
            })

    # Generate HTML
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Generated Images Gallery</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            color: white;
            margin-bottom: 3rem;
        }

        h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
        }

        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
        }

        .card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
        }

        .card-image {
            width: 100%;
            height: 300px;
            object-fit: cover;
            cursor: pointer;
        }

        .card-content {
            padding: 1.5rem;
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #333;
        }

        .card-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            font-size: 0.875rem;
            color: #666;
        }

        .btn {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s ease;
            border: none;
            cursor: pointer;
            font-size: 0.875rem;
        }

        .btn:hover {
            background: #5568d3;
        }

        .btn-group {
            display: flex;
            gap: 0.5rem;
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            overflow: auto;
        }

        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-content {
            max-width: 90%;
            max-height: 90%;
            margin: auto;
        }

        .modal-image {
            width: 100%;
            height: auto;
        }

        .close {
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            z-index: 1001;
        }

        .close:hover {
            color: #ccc;
        }

        .prompt-modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            overflow: auto;
        }

        .prompt-modal.active {
            display: block;
        }

        .prompt-content {
            background: white;
            margin: 5% auto;
            padding: 2rem;
            width: 80%;
            max-width: 800px;
            border-radius: 12px;
            max-height: 80vh;
            overflow-y: auto;
        }

        .prompt-text {
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            color: #333;
        }

        @media (max-width: 768px) {
            .gallery {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AI Generated Images Gallery</h1>
            <p class="subtitle">Generated with Gemini 3 Pro Image</p>
        </header>

        <div class="gallery" id="gallery">
            <!-- Cards will be inserted here by JavaScript -->
        </div>
    </div>

    <!-- Image Modal -->
    <div id="imageModal" class="modal">
        <span class="close" onclick="closeImageModal()">&times;</span>
        <div class="modal-content">
            <img id="modalImage" class="modal-image" src="" alt="">
        </div>
    </div>

    <!-- Prompt Modal -->
    <div id="promptModal" class="prompt-modal">
        <span class="close" onclick="closePromptModal()">&times;</span>
        <div class="prompt-content">
            <h2 style="margin-bottom: 1rem;">Generation Prompt</h2>
            <pre class="prompt-text" id="promptText"></pre>
        </div>
    </div>

    <script>
        // Image and prompt data
        const images = IMAGE_DATA_PLACEHOLDER;

        // Generate gallery cards
        function generateGallery() {
            const gallery = document.getElementById('gallery');

            images.forEach(img => {
                const card = document.createElement('div');
                card.className = 'card';

                card.innerHTML = `
                    <img src="outputs/${img.filename}" alt="${img.title}" class="card-image" onclick="openImageModal('outputs/${img.filename}')">
                    <div class="card-content">
                        <h3 class="card-title">${img.title}</h3>
                        <div class="card-meta">
                            <span>Generated: ${img.date}</span>
                        </div>
                        <div class="btn-group">
                            <button class="btn" onclick="viewPrompt('${img.promptFile}')">View Prompt</button>
                            <a href="outputs/${img.filename}" download class="btn">Download</a>
                        </div>
                    </div>
                `;

                gallery.appendChild(card);
            });
        }

        // Image modal functions
        function openImageModal(src) {
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            modal.classList.add('active');
            modalImg.src = src;
        }

        function closeImageModal() {
            document.getElementById('imageModal').classList.remove('active');
        }

        // Prompt modal functions
        async function viewPrompt(promptFile) {
            const modal = document.getElementById('promptModal');
            const promptText = document.getElementById('promptText');

            try {
                const response = await fetch(`prompts/${promptFile}`);
                const text = await response.text();
                promptText.textContent = text;
                modal.classList.add('active');
            } catch (error) {
                promptText.textContent = 'Error loading prompt file.';
                modal.classList.add('active');
            }
        }

        function closePromptModal() {
            document.getElementById('promptModal').classList.remove('active');
        }

        // Close modals on click outside
        window.onclick = function(event) {
            const imageModal = document.getElementById('imageModal');
            const promptModal = document.getElementById('promptModal');

            if (event.target === imageModal) {
                closeImageModal();
            }
            if (event.target === promptModal) {
                closePromptModal();
            }
        }

        // Initialize gallery on page load
        generateGallery();
    </script>
</body>
</html>"""

    # Replace placeholder with actual data
    html_content = html_template.replace(
        'IMAGE_DATA_PLACEHOLDER',
        json.dumps(gallery_data, indent=12)
    )

    # Write HTML file
    output_path = Path('docs/index.html')
    output_path.write_text(html_content)

    print(f"✓ Gallery generated successfully!")
    print(f"✓ Found {len(gallery_data)} images")
    print(f"✓ Output: {output_path}")

    return gallery_data

if __name__ == "__main__":
    generate_gallery()
