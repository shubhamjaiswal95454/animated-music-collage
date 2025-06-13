import streamlit as st
import tempfile
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import moviepy.editor as mpe
from moviepy.video.fx.all import fadein, fadeout, resize, crop, mirror_x, mirror_y, blackwhite, rotate
import random
import io

st.set_page_config(page_title="✨ Pro Video Story Creator", layout="centered")

st.title("🎞️ Pro Cinematic Photo Video Maker")

st.markdown("""
Create a **professional-looking cinematic video** from your images. Add a soundtrack, choose elegant animations, overlays, and cinematic transitions.
""")

uploaded_images = st.file_uploader("📸 Upload 2 to 9 Images", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
uploaded_audio = st.file_uploader("🎵 Upload Background Music (MP3/WAV)", type=['mp3', 'wav'])

video_duration = st.slider("⏱️ Total Video Duration", 10, 180, 60)
audio_start = st.number_input("🔊 Start Music At (seconds)", 0, 180, 0)
overlay_text = st.text_input("📝 Optional Title or Quote")

# Theme selector
selected_theme = st.selectbox("🎭 Choose a Theme", ["Romantic", "Action", "Retro", "Elegant", "Dynamic"])

def theme_to_style(theme):
    theme_styles = {
        "Romantic": [fadein, resize, mirror_x],
        "Action": [rotate, mirror_y, crop],
        "Retro": [blackwhite, fadeout, resize],
        "Elegant": [fadein, fadeout, resize],
        "Dynamic": [fadein, rotate, mirror_x, crop]
    }
    return theme_styles.get(theme, [resize])

def apply_effects(clip, effects):
    for effect in effects:
        clip = effect(clip)
    return clip

def get_animated_clip(image_file, effects, duration):
    image = Image.open(image_file).convert('RGB')
    image = image.resize((720, 480))
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    image.save(temp_file.name)
    clip = mpe.ImageClip(temp_file.name).set_duration(duration)
    clip = apply_effects(clip, effects)
    return clip

def create_text_clip(text, duration):
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
    img = Image.new("RGBA", (720, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = draw.textsize(text, font=font)
    draw.text(((720-w)/2, (120-h)/2), text, font=font, fill="white")
    temp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    img.save(temp_txt.name)
    return mpe.ImageClip(temp_txt.name).set_duration(duration).fadein(1).fadeout(1)

if st.button("🎬 Generate Video") and uploaded_images:
    total_images = len(uploaded_images)
    image_duration = video_duration / total_images
    all_clips = []

    for img in uploaded_images:
        effects = theme_to_style(selected_theme)
        animated = get_animated_clip(img, effects, image_duration)
        all_clips.append(animated)

    if overlay_text:
        text_clip = create_text_clip(overlay_text, duration=4)
        all_clips.insert(0, text_clip)

    final_video = mpe.concatenate_videoclips(all_clips, method="compose")

    if uploaded_audio:
        audio_clip = mpe.AudioFileClip(uploaded_audio.name).subclip(audio_start, audio_start + video_duration)
        final_video = final_video.set_audio(audio_clip)

    temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    final_video.write_videofile(temp_out.name, fps=24)

    st.success("✅ Video created successfully!")
    st.video(temp_out.name)
else:
    st.info("👆 Upload images and optionally audio, then click Generate Video.")
