# Clothing Photo Enhancer

Turn raw photos of your clothing designs into **professional fashion photographs** — ready to post on Instagram, Pinterest, or your online store.

## How it works

1. **Upload** a photo of your garment (flat lay, hanger, or on a mannequin)
2. **Choose** your photography style, background, and lighting
3. **Click Generate** — Claude AI analyses the design and writes a professional photography prompt; FLUX renders the final image
4. **Download** the result and post it directly to social media

### Two generation modes

| Mode | Best for |
|---|---|
| **Transform Photo (img2img)** | Preserving the exact structure of your design while making it look professionally photographed |
| **Generate from Description (txt2img)** | Creating a polished, stylised image when the original photo is too rough |

---

## Quick start

### 1. Get API keys

| Service | What for | Free tier |
|---|---|---|
| [Anthropic](https://console.anthropic.com) | Claude vision — analyses your clothing | Yes (limited) |
| [Replicate](https://replicate.com/account/api-tokens) | FLUX image generation | Pay-per-use (~$0.04/image) |

### 2. Install dependencies

```bash
cd clothing_photo_app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
# Edit .env and paste your keys
```

### 4. Run the app

```bash
streamlit run app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

---

## Photography settings explained

### Style
- **Editorial** — high-fashion magazine look, bold composition
- **E-commerce** — clean product shot, clear garment view
- **Social Media** — lifestyle feel, Instagram-ready
- **Lookbook** — aspirational, seasonal campaign vibe

### Background
- Studio White / Studio Grey — classic clean backdrops
- Outdoor Garden — natural, soft bokeh
- City Street — urban editorial
- Minimalist Indoor — modern interior

### Lighting
- Studio Softbox — even, professional, no harsh shadows
- Natural Golden Hour — warm outdoor glow
- Dramatic Fashion — high-contrast, moody
- Soft Diffused — flattering, gentle

### Transformation Strength (img2img only)
- **0.3–0.5** → very close to your original photo
- **0.7–0.8** → balanced transformation *(recommended)*
- **0.9+** → maximum creative freedom

---

## Tips for best input photos

- Plain background (white wall, plain fabric) gives the cleanest results
- Good lighting — near a window or outside works well
- Show the full garment; avoid cropping key design details
- Higher resolution = sharper output

---

## Tech stack

- **[Streamlit](https://streamlit.io)** — web UI
- **[Claude claude-sonnet-4-6](https://anthropic.com)** — garment vision analysis & prompt writing
- **[FLUX dev / FLUX 1.1 Pro](https://replicate.com/black-forest-labs)** — professional image generation
