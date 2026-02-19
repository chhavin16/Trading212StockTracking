"""
Clothing Photo Enhancer
Transform your clothing designs into professional fashion photographs
using Claude AI vision analysis and FLUX image generation.
"""

import os
import io
import base64

import streamlit as st
import anthropic
import replicate
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Clothing Photo Enhancer",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.4rem;
            font-weight: 800;
            text-align: center;
            padding: 1.2rem 0 0.4rem;
            color: #1a1a2e;
            letter-spacing: -0.5px;
        }
        .sub-header {
            text-align: center;
            color: #555;
            font-size: 1.05rem;
            margin-bottom: 1.5rem;
        }
        .tip-box {
            background: #f0f4ff;
            border-left: 4px solid #4361ee;
            padding: 0.7rem 1rem;
            border-radius: 0 6px 6px 0;
            font-size: 0.88rem;
            color: #333;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STYLE_MAP = {
    "Editorial": "high-fashion editorial magazine shoot, avant-garde composition, striking visual impact",
    "E-commerce": "clean professional e-commerce product photograph, white or neutral background, sharp details",
    "Social Media": "engaging Instagram lifestyle fashion post, aspirational yet approachable",
    "Lookbook": "aspirational seasonal fashion lookbook campaign, cohesive visual storytelling",
}

BACKGROUND_MAP = {
    "Studio White": "clean white seamless studio backdrop",
    "Studio Grey": "professional grey seamless studio background",
    "Outdoor Garden": "lush garden setting with soft natural bokeh, green tones",
    "City Street": "stylish urban street environment with subtle city life in background",
    "Minimalist Indoor": "modern minimalist interior, warm neutral tones, architectural lines",
}

LIGHTING_MAP = {
    "Studio Softbox": "professional studio softbox lighting, evenly lit, no harsh shadows",
    "Natural Golden Hour": "warm golden hour natural sunlight, soft outdoor glow",
    "Dramatic Fashion": "dramatic high-contrast fashion lighting, moody and editorial",
    "Soft Diffused": "soft diffused flattering light, gentle shadows, skin-friendly tones",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_anthropic_client() -> anthropic.Anthropic | None:
    api_key = st.session_state.get("anthropic_key") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def get_image_media_type(uploaded_file) -> str:
    mapping = {
        "image/jpeg": "image/jpeg",
        "image/png": "image/png",
        "image/webp": "image/webp",
        "image/gif": "image/gif",
    }
    return mapping.get(uploaded_file.type, "image/jpeg")


def analyze_and_prompt(
    image_bytes: bytes,
    media_type: str,
    client: anthropic.Anthropic,
    style: str,
    background: str,
    lighting: str,
) -> tuple[str, str]:
    """
    Use Claude vision to analyze the uploaded clothing item and
    return (analysis_text, image_generation_prompt).
    """
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    instruction = f"""You are a professional fashion photographer and creative director.

Analyze the clothing item in this image, then write a detailed image generation prompt
for a professional fashion photograph with these settings:
- Photography style: {STYLE_MAP.get(style, style)}
- Background: {BACKGROUND_MAP.get(background, background)}
- Lighting: {LIGHTING_MAP.get(lighting, lighting)}

Your response MUST follow this exact format with no extra text before or after:

ANALYSIS:
<2–4 sentences describing the clothing: type, colors, pattern, fabric, style category, and key design details>

PROMPT:
<A 4–6 sentence photorealistic image generation prompt that faithfully describes the exact clothing item above,
includes a fitting model, the specified background and lighting, professional photography terms
(shallow depth of field, 85mm lens, etc.), and quality descriptors like
"photorealistic", "4K ultra-detailed", "professional fashion photography">"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": instruction},
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()

    analysis, prompt = "", raw  # safe defaults
    if "ANALYSIS:" in raw and "PROMPT:" in raw:
        parts = raw.split("PROMPT:", 1)
        analysis = parts[0].replace("ANALYSIS:", "").strip()
        prompt = parts[1].strip()

    return analysis, prompt


def _download_url(url: str) -> bytes:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content


def generate_img2img(image_bytes: bytes, prompt: str, strength: float) -> bytes | None:
    """
    Transform the uploaded photo into a professional fashion photograph
    using FLUX dev img2img on Replicate.
    """
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    output = replicate.run(
        "black-forest-labs/flux-dev",
        input={
            "image": data_url,
            "prompt": prompt,
            "strength": strength,
            "num_inference_steps": 28,
            "guidance": 3.5,
            "output_format": "jpg",
            "output_quality": 95,
        },
    )

    result = list(output)[0] if hasattr(output, "__iter__") else output
    if isinstance(result, str) and result.startswith("http"):
        return _download_url(result)
    if hasattr(result, "read"):
        return result.read()
    return None


def generate_txt2img(prompt: str) -> bytes | None:
    """
    Generate a professional fashion photograph from text using
    FLUX 1.1 Pro on Replicate.
    """
    output = replicate.run(
        "black-forest-labs/flux-1.1-pro",
        input={
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "num_outputs": 1,
            "output_format": "jpg",
            "output_quality": 95,
        },
    )

    result = list(output)[0] if hasattr(output, "__iter__") else output
    if isinstance(result, str) and result.startswith("http"):
        return _download_url(result)
    if hasattr(result, "read"):
        return result.read()
    return None


# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------

def main():
    st.markdown('<div class="main-header">👗 Clothing Photo Enhancer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Turn your clothing designs into professional fashion photographs — ready for social media.</div>',
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------ Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        with st.expander("🔑 API Keys", expanded=not os.getenv("ANTHROPIC_API_KEY")):
            anthropic_key = st.text_input(
                "Anthropic API Key",
                value=os.getenv("ANTHROPIC_API_KEY", ""),
                type="password",
                help="Get yours at https://console.anthropic.com",
            )
            if anthropic_key:
                st.session_state["anthropic_key"] = anthropic_key

            replicate_token = st.text_input(
                "Replicate API Token",
                value=os.getenv("REPLICATE_API_TOKEN", ""),
                type="password",
                help="Get yours at https://replicate.com/account/api-tokens",
            )
            if replicate_token:
                os.environ["REPLICATE_API_TOKEN"] = replicate_token

        st.divider()
        st.header("📸 Photography Settings")

        style = st.selectbox(
            "Photography Style",
            list(STYLE_MAP.keys()),
            help="Determines the overall visual feel of the output photo.",
        )
        background = st.selectbox(
            "Background",
            list(BACKGROUND_MAP.keys()),
            help="The environment or backdrop for the photograph.",
        )
        lighting = st.selectbox(
            "Lighting",
            list(LIGHTING_MAP.keys()),
            help="The lighting setup used in the photograph.",
        )

        st.divider()
        st.header("🎛️ Generation Mode")

        mode = st.radio(
            "Mode",
            ["Transform Photo (img2img)", "Generate from Description (txt2img)"],
            help=(
                "**Transform**: keeps your clothing design structure while making it look professional.\n\n"
                "**Generate**: creates a fully new image purely from the AI description."
            ),
        )

        strength = 0.75
        if mode.startswith("Transform"):
            strength = st.slider(
                "Transformation Strength",
                min_value=0.30,
                max_value=0.95,
                value=0.75,
                step=0.05,
                help="Lower → stays closer to your original photo. Higher → more creative freedom.",
            )

        st.divider()
        st.markdown(
            '<div class="tip-box">💡 <b>Tips for best results</b><br>'
            "• Use a well-lit photo of the garment flat or on a hanger.<br>"
            "• Avoid busy backgrounds — a plain wall works best.<br>"
            "• Higher resolution inputs produce sharper outputs.</div>",
            unsafe_allow_html=True,
        )

    # ---------------------------------------------------------------- Main cols
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.subheader("📤 Upload Your Clothing Photo")
        uploaded = st.file_uploader(
            "Drag & drop or click to browse",
            type=["jpg", "jpeg", "png", "webp"],
            help="A clear, well-lit photo gives the best results.",
        )
        if uploaded:
            img = Image.open(uploaded)
            st.image(img, caption="Original Design", use_column_width=True)
            st.caption(f"{img.size[0]} × {img.size[1]} px · {uploaded.type}")

    with col_right:
        st.subheader("✨ Professional Result")
        result_slot = st.empty()
        result_slot.info("Upload a photo and click **Generate** to see your professional photograph here.")

    # -------------------------------------------------------- Generate button
    if uploaded:
        st.divider()
        btn_col, hint_col = st.columns([1, 3])
        with btn_col:
            go = st.button("🚀 Generate Professional Photo", type="primary", use_container_width=True)
        with hint_col:
            st.caption(
                "Claude AI will analyse your garment and FLUX will render the professional photograph. "
                "This typically takes 20–40 seconds."
            )

        if go:
            client = get_anthropic_client()
            if not client:
                st.error("❌ Anthropic API key is missing. Add it in the sidebar.")
                st.stop()
            if not os.getenv("REPLICATE_API_TOKEN"):
                st.error("❌ Replicate API token is missing. Add it in the sidebar.")
                st.stop()

            uploaded.seek(0)
            raw_bytes = uploaded.read()
            media_type = get_image_media_type(uploaded)

            # Step 1 — Claude analysis
            with st.status("🔍 Analysing clothing with Claude AI …", expanded=True) as status:
                try:
                    analysis, gen_prompt = analyze_and_prompt(
                        raw_bytes, media_type, client, style, background, lighting
                    )
                    st.write("✅ Garment analysed.")
                    with st.expander("📋 View analysis & prompt", expanded=False):
                        st.markdown("**Garment Analysis**")
                        st.write(analysis)
                        st.markdown("**Generated Photography Prompt**")
                        st.code(gen_prompt, language=None)
                    status.update(label="✅ Analysis complete!", state="complete")
                except Exception as exc:
                    status.update(label="❌ Analysis failed", state="error")
                    st.error(f"Claude analysis error: {exc}")
                    st.stop()

            # Step 2 — Image generation
            with st.status("🎨 Generating professional photograph …", expanded=True) as status:
                try:
                    if mode.startswith("Transform"):
                        result_bytes = generate_img2img(raw_bytes, gen_prompt, strength)
                    else:
                        result_bytes = generate_txt2img(gen_prompt)

                    if result_bytes:
                        status.update(label="✅ Photo generated!", state="complete")
                        result_img = Image.open(io.BytesIO(result_bytes))
                        with col_right:
                            result_slot.image(
                                result_img,
                                caption="Professional Fashion Photo",
                                use_column_width=True,
                            )

                        st.success("🎉 Your professional photo is ready to download!")
                        dl1, dl2 = st.columns(2)
                        with dl1:
                            st.download_button(
                                "⬇️ Download Photo",
                                data=result_bytes,
                                file_name=f"professional_{uploaded.name.rsplit('.', 1)[0]}.jpg",
                                mime="image/jpeg",
                                type="primary",
                                use_container_width=True,
                            )
                        with dl2:
                            st.download_button(
                                "📄 Download Prompt",
                                data=gen_prompt,
                                file_name="fashion_prompt.txt",
                                mime="text/plain",
                                use_container_width=True,
                            )
                    else:
                        status.update(label="❌ Generation returned no output", state="error")
                        st.error("Image generation failed — please try again or switch modes.")
                except Exception as exc:
                    status.update(label="❌ Generation failed", state="error")
                    st.error(f"Generation error: {exc}")
                    st.exception(exc)

    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align:center;color:#aaa;font-size:0.8rem;'>"
        "Powered by <b>Claude (Anthropic)</b> for vision analysis "
        "and <b>FLUX (Replicate)</b> for image generation"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
