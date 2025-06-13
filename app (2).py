import streamlit as st
import tempfile
from PIL import Image
import numpy as np
import moviepy.editor as mpe

from moviepy.video.fx.all import zoom_in, fadein, resize
import random
import io

st.set_page_config(page_title="Ultimate Animated Photo Music Collage", layout="centered")

st.title("🎬 Ultimate Animated Photo Music Collage Maker")

st.write("""
Upload 2 to 9 images and a song, pick your favorite collage style and animation.
Get a video with music and beautiful transitions!
""")

uploaded_images = st.file_uploader("Upload 2 to 9 images", accept_multiple_files=True, type=['jpg','jpeg','png'])
uploaded_audio = st.file_uploader("Upload an audio file (mp3/wav)", type=['mp3','wav'])

duration = st.slider("Video Length (seconds, max 300)", min_value=10, max_value=300, value=60)
audio_start = st.number_input("Audio Start (seconds)", min_value=0, max_value=300, value=0)
overlay_text = st.text_input("Optional: Add overlay text/title for your collage video:")

collage_style = st.selectbox(
    "Choose collage layout",
    ["Auto Grid", "Horizontal Strip", "Vertical Strip", "Classic Collage"]
)

animation_style = st.selectbox(
    "Animation for photos",
    ["Random Per Photo", "Fade In", "Zoom In", "Slide Left", "No Animation"]
)

def make_auto_grid(images, size=480):
    n = len(images)
    # determine grid size (square or as close as possible)
    cols = int(np.ceil(np.sqrt(n)))
    rows = int(np.ceil(n / cols))
    grid_img = Image.new("RGB", (cols*size, rows*size), color=(30,30,30))
    for idx, img in enumerate(images):
        r = idx // cols
        c = idx % cols
        img_resized = img.resize((size, size))
        grid_img.paste(img_resized, (c*size, r*size))
    return grid_img

def make_classic_collage(images, size=480):
    # Puts images at angles/corners over a canvas, for "collage" feeling
    n = len(images)
    canvas = Image.new("RGB", (size*2, size*2), color=(30,30,30))
    rotations = [-12, 7, 15, -7, 5, -10, 8, -4, 0]
    centers = [(size//2, size//2), (size*3//2, size//2), (size//2, size*3//2), (size*3//2, size*3//2)]
    for i, img in enumerate(images):
        angle = rotations[i % len(rotations)]
        img_t = img.resize((int(size*1.1), int(size*1.1))).rotate(angle, expand=True)
        center = (random.randint(0, size*2-img_t.width), random.randint(0, size*2-img_t.height))
        canvas.paste(img_t, center, mask=img_t.convert("RGBA"))
    return canvas

def get_transition(img_clip, style, idx, total, d_img, d_anim):
    if style == "No Animation":
        return img_clip.set_duration(d_img)
    if style == "Fade In":
        return img_clip.crossfadein(1).set_duration(d_img)
    if style == "Zoom In":
        return img_clip.set_duration(d_img).fx(mpe.vfx.zoomIn, 1.13)
    if style == "Slide Left":
        w, h = img_clip.size
        move_clip = img_clip.set_duration(d_img).fx(mpe.vfx.slide_in, 1, 'left')
        return move_clip
    if style == "Random Per Photo":
        styles = ["Fade In", "Zoom In", "Slide Left", "No Animation"]
        random_style = random.choice(styles)
        return get_transition(img_clip, random_style, idx, total, d_img, d_anim)
    # default
    return img_clip.set_duration(d_img)

if st.button("Create Collage Video"):
    if not (2 <= len(uploaded_images) <= 9):
        st.error("Upload between 2 and 9 images!")
    elif not uploaded_audio:
        st.error("Upload an audio file!")
    else:
        with st.spinner("Processing video... (can take a few minutes for long videos)"):
            # Step 1: Load/prepare images
            images = [Image.open(img).convert("RGB") for img in uploaded_images]
            preview_size = 480

            # Step 2: Make background collage image
            if collage_style == "Auto Grid":
                collage = make_auto_grid(images, size=preview_size)
            elif collage_style == "Horizontal Strip":
                collage = Image.new("RGB", (preview_size*len(images), preview_size), (30,30,30))
                for i,img in enumerate(images):
                    collage.paste(img.resize((preview_size, preview_size)), (i*preview_size, 0))
            elif collage_style == "Vertical Strip":
                collage = Image.new("RGB", (preview_size, preview_size*len(images)), (30,30,30))
                for i,img in enumerate(images):
                    collage.paste(img.resize((preview_size, preview_size)), (0, i*preview_size))
            else:
                collage = make_classic_collage(images, size=preview_size)

            # Step 3: Make video transitions for each image
            d_img = duration / len(images)
            d_anim = min(1.2, d_img)   # duration of animation per img

            clips = []
            for idx, img in enumerate(images):
                img_clip = mpe.ImageClip(np.array(img.resize((preview_size, preview_size))))
                anim_clip = get_transition(img_clip, animation_style, idx, len(images), d_img, d_anim)
                clips.append(anim_clip)

            video_clip = mpe.concatenate_videoclips(clips, method="compose").set_duration(duration)
            
            # Step 4: Overlay collage background and (optional) overlay text
            bg_clip = mpe.ImageClip(np.array(collage)).set_duration(duration)
            video_with_bg = mpe.CompositeVideoClip([bg_clip, video_clip.set_position("center")])
            if overlay_text.strip():
                txt_clip = mpe.TextClip(
                    overlay_text, fontsize=48, color='white', font='Arial-Bold', method='label', align='center')
                txt_clip = txt_clip.set_position(("center", 30)).set_duration(duration).crossfadein(2).fadeout(2)
                video_with_bg = mpe.CompositeVideoClip([video_with_bg, txt_clip])

            # Step 5: Add/crop audio
            audio_clip = mpe.AudioFileClip(uploaded_audio.name)
            if audio_clip.duration > duration+audio_start:
                audio_clip = audio_clip.subclip(audio_start, audio_start+duration)
            elif audio_clip.duration > audio_start:
                audio_clip = audio_clip.subclip(audio_start)
            video_final = video_with_bg.set_audio(audio_clip).set_duration(duration)

            # Step 6: Export video (to temp file)
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                video_final.write_videofile(temp_file.name, fps=24, codec="libx264", audio_codec="aac")
                temp_filename = temp_file.name
            
            st.video(temp_filename)
            with open(temp_filename, 'rb') as fp:
                st.download_button(
                    label="⬇️ Download Video Collage",
                    data=fp,
                    file_name="collage_video.mp4",
                    mime="video/mp4"
                )
            st.success("Done! Enjoy your professional collage video! 🎉")
            st.markdown(
                "<div style='color:red; font-size:16px;'>⚠️ This is an AI-created collage animation; results may be artistically and musically unpredictable.</div>",
                unsafe_allow_html=True
            )
