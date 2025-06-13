import streamlit as st
import tempfile
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import moviepy.editor as mpe
from moviepy.video.fx.all import fadein, resize
import random
import io

st.set_page_config(page_title="🎞️ Ultimate Animated Story Studio", layout="centered")

st.title("🎬 Cinematic Photo Story Creator")

st.markdown("""
Upload 2 to 9 images and your favorite song. Choose effects and make an emotional, cinematic video story from your photos!
""")

uploaded_images = st.file_uploader("📸 Upload 2 to 9 images", accept_multiple_files=True, type=['jpg','jpeg','png'])
uploaded_audio = st.file_uploader("🎵 Upload background music (mp3/wav)", type=['mp3','wav'])

duration = st.slider("⏱️ Video Length (seconds)", min_value=10, max_value=300, value=60)
audio_start = st.number_input("🔊 Start Music At (seconds)", min_value=0, max_value=300, value=0)
overlay_text = st.text_input("📝 Title or quote to show in your video:")

animation_style = st.selectbox("🎞️ Photo Animation Style", ["Zoom & Pan (Ken Burns)", "Fade In", "Slide Right", "No Animation"])

def apply_ken_burns(img, d_img):
    return (mpe.ImageClip(np.array(img))
            .resize(lambda t: 1.1 + 0.03 * t)
            .set_position(lambda t: ('center', int(20*t)))
            .set_duration(d_img))

def get_transition(img, style, d_img):
    clip = mpe.ImageClip(np.array(img)).set_duration(d_img)
    if style == "Fade In":
        return fadein(clip, duration=min(1.5, d_img))
    elif style == "Slide Right":
        return clip.set_position(lambda t: (int(-100 * (1 - t)), 'center'))
    elif style == "Zoom & Pan (Ken Burns)":
        return apply_ken_burns(img, d_img)
    else:
        return clip

if st.button("🚀 Create My Cinematic Video"):
    if not (2 <= len(uploaded_images) <= 9):
        st.error("Please upload between 2 and 9 images!")
    elif not uploaded_audio:
        st.error("Please upload a music file!")
    else:
        with st.spinner("🎥 Rendering your cinematic story..."):
            images = [Image.open(img).convert("RGB").resize((720, 480)) for img in uploaded_images]
            d_img = duration / len(images)
            clips = [get_transition(img, animation_style, d_img) for img in images]

            final_clip = mpe.concatenate_videoclips(clips, method="compose").set_duration(duration)

            if overlay_text.strip():
                txt_img = Image.new("RGBA", final_clip.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(txt_img)
                try:
                    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
                except:
                    font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), overlay_text, font=font)
                text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                position = ((txt_img.width - text_width) // 2, 30)
                draw.text(position, overlay_text, font=font, fill="white")
                txt_np = np.array(txt_img)
                text_clip = mpe.ImageClip(txt_np).set_duration(duration).fadein(1).fadeout(1)
                final_clip = mpe.CompositeVideoClip([final_clip, text_clip])

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
                tmp_audio.write(uploaded_audio.read())
                tmp_audio.flush()
                audio_clip = mpe.AudioFileClip(tmp_audio.name)

            if audio_clip.duration > duration + audio_start:
                audio_clip = audio_clip.subclip(audio_start, audio_start + duration)
            elif audio_clip.duration > audio_start:
                audio_clip = audio_clip.subclip(audio_start)

            final_video = final_clip.set_audio(audio_clip).set_duration(duration)

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                final_video.write_videofile(temp_file.name, fps=24, codec="libx264", audio_codec="aac")
                temp_filename = temp_file.name

            st.video(temp_filename)
            with open(temp_filename, 'rb') as fp:
                st.download_button(
                    label="⬇️ Download Cinematic Video",
                    data=fp,
                    file_name="cinematic_story.mp4",
                    mime="video/mp4"
                )

            st.success("Your cinematic story is ready! ✨")
