import streamlit as st
import numpy as np
import librosa
import matplotlib.pyplot as plt
from moviepy.editor import VideoClip, AudioFileClip
from moviepy.video.io.bindings import mplfig_to_npimage
import tempfile
import os

# サイドバーに音声ファイルをアップロードする項目を設定し、アップロードを促す
st.sidebar.title('Menu')
st.sidebar.write("楽曲をアップロードしてください")
uploaded_file = st.sidebar.file_uploader("Choose an MP3 file", type="mp3")

def analyze_audio(file_path):
    y, sr = librosa.load(file_path, sr=None)  # sr=Noneで元のサンプリングレートを使用
    rms = librosa.feature.rms(y=y)[0]
    rms_normalized = (rms - np.min(rms)) / (np.max(rms) - np.min(rms))
    return y, sr, rms_normalized

def get_background_color(intensity):
    if intensity < 0.1:
        return (0, 0, 255)
    else:
        red = int(255 * (intensity - 0.1) / 0.9)
        green = int(255 * (1 - (intensity - 0.1) / 0.9))
        return (red, green, 0)

def make_frame(t, y, sr, rms_normalized, fps, duration):
    fig, ax = plt.subplots(figsize=(10, 7))
    
    start = int(t * sr)
    end = int((t + 1 / fps) * sr)
    ax.plot(y[start:end])
    
    ax.axis('off')
    
    intensity_index = int(t * len(rms_normalized) / duration)
    intensity_index = min(intensity_index, len(rms_normalized) - 1)
    color = get_background_color(rms_normalized[intensity_index])
    fig.patch.set_facecolor(np.array(color) / 255)
    
    frame = mplfig_to_npimage(fig)
    plt.close(fig)
    return frame

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(uploaded_file.read())
        audio_path = tmp_file.name

    y, sr, rms_normalized = analyze_audio(audio_path)
    fps = 24
    duration = len(y) / sr
    
    if st.sidebar.button('Generate'):
        with st.spinner('Generating video...'):
            video = VideoClip(lambda t: make_frame(t, y, sr, rms_normalized, fps, duration), duration=duration)
            audio = AudioFileClip(audio_path).subclip(0, duration)
            video = video.set_audio(audio).set_duration(duration)
            output_path = 'waves.mp4'
            video.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac')
        
        st.success('Video generated successfully!')
        with open(output_path, 'rb') as video_file:
            video_bytes = video_file.read()
            st.video(video_bytes)
        
        # Clean up temporary files
        os.remove(audio_path)
        os.remove(output_path)
else:
    st.sidebar.warning('Please upload an audio file.')
