import streamlit as st
import tempfile
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import moviepy.editor as mpe
from moviepy.video.fx.all import fadein, resize
import random
import io

st.set_page_config(page_title="✨ Pro Video Story Creator", layout="centered")

st.title("🎞️ Pro Cinematic Photo Video Maker")

st.markdown("""
Create a **professional-looking cinematic video** from your images. Add a soundtrack, choose elegant animations, and overlay text.
""")

uploaded_images = st.file_uploader("📸 Upload 2 to 9 Images", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
uploaded_audio = st.file_uploader("🎵 Upload Background Music (MP3/WAV)", type=['mp3', 'wav'])

video_duration = st.slider("⏱️ Total Video Duration", 10, 180, 60)
audio_start = st.number_input("🔊 Start Music At (seconds)", 0, 180, 0)
overlay_text = st.text_input("📝 Optional Title or Quote")

animation_style = st.selectbox("🎬 Image Transition Style", [
    "Ken Burns (Zoom & Pan)", "Elegant Fade In", "Smooth Slide", "Cinematic Static"
])


def ken_burns_effect(img, d_img):
    return (mpe.ImageClip(np.array(img))
            .resize(lambda t: 1.1 + 0.02 * t)
            .set_position(lambda t: ('center', int(30*t)))
            .set_duration(d_img))


def get_animated_clip(img, style, d_img):
    clip = mpe.ImageClip(np.array(img)).set_duration(d_img)
    if style == "Elegant Fade In":
        return fadein(clip.set_start(0), duration=min(1.5, d_img))
    elif style == "Smooth Slide":
        return clip.set_position(lambda t: (int(-80 * (1 - t)), 'center'))
    elif style == "Ken Burns (Zoom & Pan)":
        return ken_burns_effect(img, d_img)
    else:
        return clip


if st.button("🎬 Generate My Video"):
    if not (2 <= len(uploaded_images) <= 9):
        st.error("Please upload between 2 to 9 images.")
    elif not uploaded_audio:
        st.error("Please upload a background music track.")
    else:
        with st.spinner("🎞️ Rendering your stylish video..."):
            images = [Image.open(img).convert("RGB").resize((720, 480)) for img in uploaded_images]
            d_img = video_duration / len(images)
            clips = [get_animated_clip(img, animation_style, d_img) for img in images]
            base_video = mpe.concatenate_videoclips(clips, method="compose").set_duration(video_duration)

            if overlay_text.strip():
                txt_img = Image.new("RGBA", base_video.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(txt_img)
                try:
                    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 56)
                except:
                    font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), overlay_text, font=font)
                text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                position = ((txt_img.width - text_width) // 2, 30)
                draw.text(position, overlay_text, font=font, fill="white")
                txt_np = np.array(txt_img)
                text_clip = mpe.ImageClip(txt_np).set_duration(video_duration).fadein(1).fadeout(1)
                base_video = mpe.CompositeVideoClip([base_video, text_clip])

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
                tmp_audio.write(uploaded_audio.read())
                tmp_audio.flush()
                audio_clip = mpe.AudioFileClip(tmp_audio.name)

            if audio_clip.duration > video_duration + audio_start:
                audio_clip = audio_clip.subclip(audio_start, audio_start + video_duration)
            elif audio_clip.duration > audio_start:
                audio_clip = audio_clip.subclip(audio_start)

            final_video = base_video.set_audio(audio_clip).set_duration(video_duration)

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                final_video.write_videofile(temp_file.name, fps=24, codec="libx264", audio_codec="aac")
                temp_filename = temp_file.name

            st.video(temp_filename)
            with open(temp_filename, 'rb') as fp:
                st.download_button("⬇️ Download Your Pro Video", fp, file_name="styled_video.mp4", mime="video/mp4")

            st.success("✅ Your cinematic video is ready!")
