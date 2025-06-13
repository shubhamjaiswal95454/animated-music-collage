import streamlit as st
import tempfile
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import moviepy.editor as mpe
from moviepy.video.fx.all import fadein, resize
import random
import io

st.set_page_config(page_title="🎞️ Ultimate Animated Collage Studio", layout="centered")

st.title("🌟 Ultimate Animated Photo Music Collage Maker")

st.markdown("""
Upload 2 to 9 images and your favorite song. Choose a layout and animation style.
Create a cinematic collage with music, motion, and magic ✨!
""")

uploaded_images = st.file_uploader("📸 Upload 2 to 9 images", accept_multiple_files=True, type=['jpg','jpeg','png'])
uploaded_audio = st.file_uploader("🎵 Upload a music file (mp3/wav)", type=['mp3','wav'])

duration = st.slider("🎬 Video Length (seconds)", min_value=10, max_value=300, value=60)
audio_start = st.number_input("🔊 Audio Start Time (seconds)", min_value=0, max_value=300, value=0)
overlay_text = st.text_input("📝 Add a title or message on your collage video:")

collage_style = st.selectbox("🎨 Choose collage layout", ["Auto Grid", "Horizontal Strip", "Vertical Strip", "Classic Collage"])
animation_style = st.selectbox("✨ Animation style for photos", ["Random Per Photo", "Fade In", "Zoom In", "Slide Left", "No Animation"])

def make_auto_grid(images, size=480):
    n = len(images)
    cols = int(np.ceil(np.sqrt(n)))
    rows = int(np.ceil(n / cols))
    grid_img = Image.new("RGB", (cols*size, rows*size), color=(20,20,20))
    for idx, img in enumerate(images):
        r = idx // cols
        c = idx % cols
        img_resized = img.resize((size, size))
        grid_img.paste(img_resized, (c*size, r*size))
    return grid_img

def make_classic_collage(images, size=480):
    n = len(images)
    canvas = Image.new("RGB", (size*2, size*2), color=(20,20,20))
    rotations = [-15, 10, 20, -10, 8, -13, 6, -5, 0]
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
        return fadein(img_clip.set_duration(d_img), duration=d_anim)
    if style == "Zoom In":
        return img_clip.set_duration(d_img).resize(lambda t: 1 + 0.07 * t)
    if style == "Slide Left":
        return img_clip.set_duration(d_img).set_position(lambda t: (int(100 * (1 - t)), 'center'))
    if style == "Random Per Photo":
        styles = ["Fade In", "Zoom In", "Slide Left", "No Animation"]
        random_style = random.choice(styles)
        return get_transition(img_clip, random_style, idx, total, d_img, d_anim)
    return img_clip.set_duration(d_img)

if st.button("🚀 Create My Collage Video"):
    if not (2 <= len(uploaded_images) <= 9):
        st.error("Please upload between 2 and 9 images!")
    elif not uploaded_audio:
        st.error("Please upload a music file!")
    else:
        with st.spinner("✨ Creating your animated collage..."):
            images = [Image.open(img).convert("RGB") for img in uploaded_images]
            preview_size = 480

            if collage_style == "Auto Grid":
                collage = make_auto_grid(images, size=preview_size)
            elif collage_style == "Horizontal Strip":
                collage = Image.new("RGB", (preview_size*len(images), preview_size), (20,20,20))
                for i,img in enumerate(images):
                    collage.paste(img.resize((preview_size, preview_size)), (i*preview_size, 0))
            elif collage_style == "Vertical Strip":
                collage = Image.new("RGB", (preview_size, preview_size*len(images)), (20,20,20))
                for i,img in enumerate(images):
                    collage.paste(img.resize((preview_size, preview_size)), (0, i*preview_size))
            else:
                collage = make_classic_collage(images, size=preview_size)

            d_img = duration / len(images)
            d_anim = min(1.5, d_img)

            clips = []
            for idx, img in enumerate(images):
                img_clip = mpe.ImageClip(np.array(img.resize((preview_size, preview_size))))
                anim_clip = get_transition(img_clip, animation_style, idx, len(images), d_img, d_anim)
                clips.append(anim_clip)

            video_clip = mpe.concatenate_videoclips(clips, method="compose").set_duration(duration)
            bg_clip = mpe.ImageClip(np.array(collage)).set_duration(duration)
            video_with_bg = mpe.CompositeVideoClip([bg_clip, video_clip.set_position("center")])

            if overlay_text.strip():
                txt_img = Image.new("RGBA", video_with_bg.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(txt_img)
                try:
                    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 50)
                except:
                    font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), overlay_text, font=font)
                text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                position = ((txt_img.width - text_width) // 2, 40)
                draw.text(position, overlay_text, font=font, fill="white")
                txt_np = np.array(txt_img)
                text_clip = mpe.ImageClip(txt_np, ismask=False).set_duration(duration)
                text_clip = text_clip.set_position(("center", "top")).crossfadein(2).fadeout(2)
                video_with_bg = mpe.CompositeVideoClip([video_with_bg, text_clip])

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
                tmp_audio.write(uploaded_audio.read())
                tmp_audio.flush()
                audio_clip = mpe.AudioFileClip(tmp_audio.name)

            if audio_clip.duration > duration + audio_start:
                audio_clip = audio_clip.subclip(audio_start, audio_start+duration)
            elif audio_clip.duration > audio_start:
                audio_clip = audio_clip.subclip(audio_start)

            video_final = video_with_bg.set_audio(audio_clip).set_duration(duration)

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                video_final.write_videofile(temp_file.name, fps=24, codec="libx264", audio_codec="aac")
                temp_filename = temp_file.name

            st.video(temp_filename)
            with open(temp_filename, 'rb') as fp:
                st.download_button(
                    label="⬇️ Download Your Stylish Collage Video",
                    data=fp,
                    file_name="animated_collage_video.mp4",
                    mime="video/mp4"
                )

            st.success("Your cinematic collage is ready! 🎉")
            st.markdown(
                "<div style='color:#ff4d4f; font-size:16px;'>⚠️ Generated video may have stylistic randomness due to AI enhancements.</div>",
                unsafe_allow_html=True
            )
