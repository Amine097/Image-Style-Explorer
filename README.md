# Image-Style-Explorer

A Streamlit web app that lets you upload an image, apply visual styles, and manage multiple “discussions” similar to ChatGPT. Each discussion contains its own image, style, and slider settings.

## Features

- Apply visual styles to any image:
  - None
  - Black & White
  - Sketch
  - Cartoon
  - Blur
  - Painting
- Fast vs High-quality processing modes.
- ChatGPT-like discussion system:
  - Each upload creates a new discussion.
  - Discussions are renamed to the uploaded image filename.
  - Each discussion stores its own style and settings.
  - Only one blank discussion can exist at a time.
- Upload button disappears after uploading an image.
- No interference between discussions (each is fully isolated).
- Before/After comparison.
- Download styled image with automatic filename:
  `originalname_style.png`.

## Installation

```bash
git clone <your-repo-url>
cd Image-Style-Explorer
pip install -r requirements.txt
```

## Run the App
```bash
streamlit run app.py
```

### Project Structure

Image-Style-Explorer/
│
├── app.py
├── README.md
└── styles/
    ├── __init__.py
    ├── basic_filters.py
    └── artistic.py

## Usage
Launch the app.

Choose Fast or High Quality mode in the sidebar.

Create a new discussion and upload an image.

Choose a style and adjust sliders.

Compare the Before/After preview.

Download the styled result.

Switch between discussions anytime.