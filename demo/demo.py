import streamlit as st
import numpy as np
import librosa
import matplotlib.pyplot as plt
from moviepy.editor import VideoClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.io.bindings import mplfig_to_npimage
import tempfile
import os

# ImageMagickのパスを設定
os.environ["IMAGEMAGICK_BINARY"] = "/usr/local/bin/convert"  # 例。適切なパスに変更してください。

# サイドバーに音声ファイルをアップロードする項目を設定し、アップロードを促す
#st.sidebar.title('Input Items')
st.sidebar.subheader("楽曲をアップロードしてください")
uploaded_file = st.sidebar.file_uploader("MP3ファイルを選択してください", type="mp3")

# サイドバーに曲名を入力する項目を設定し、入力を促す
st.sidebar.subheader("曲名を入力してください")
song_name = st.sidebar.text_input("曲名", "")

st.sidebar.subheader("アーティスト名を入力してください")
artist_name = st.sidebar.text_input("アーティスト名", "")

def analyze_audio(file_path):
    y, sr = librosa.load(file_path, sr=None)  # sr=Noneで元のサンプリングレートを使用
    rms = librosa.feature.rms(y=y)[0]
    rms_normalized = (rms - np.min(rms)) / (np.max(rms) - np.min(rms))
    return y, sr, rms_normalized

def get_background_color(intensity):
    if intensity < 0.1:
        return (0, 255, 150)
    else:
        red = int(255 * (intensity - 0.1) / 0.9)
        green = int(255 * (1 - (intensity - 0.1) / 0.9))
        return (red, green, 150)
def make_frame(t, y, sr, rms_normalized, fps, duration):
    fig, ax = plt.subplots(figsize=(10, 6))
    
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
    
    if st.sidebar.button('作成'):
        st.header(f'{song_name}')
        st.text(f' {artist_name}')
        with st.spinner('動画を作成中...'):
            video = VideoClip(lambda t: make_frame(t, y, sr, rms_normalized, fps, duration), duration=duration)
            audio = AudioFileClip(audio_path).subclip(0, duration)
            video = video.set_audio(audio).set_duration(duration)
            output_path = 'waves.mp4'
            video.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac')

            # 相対パスの指定
            #font_path = os.path.join("fonts", "JKG-M_3.ttf")

            # 表示させるテキストの色のrgb値をそれぞれ設定
            text_color = 'rgb(254, 249, 245)'

            # 曲名とアーティスト名をテキストとして追加
            # テキストクリップの生成
            text_clip1 = TextClip(f"{song_name}", fontsize=60, color=f'{text_color}', font="../font/Koruri-Light.ttf")
            text_clip2 = TextClip(f"{artist_name}", fontsize=40, color=f'{text_color}', font="../font/Koruri-Light.ttf")

            # ビデオの高さを取得して、中央に寄せる位置を計算
            video_height = 600  # 600pの動画を想定
            text1_height = text_clip1.size[1]
            text2_height = text_clip2.size[1]
            gap = 10  # テキストクリップ間のスペース

            # 中央に寄せるための位置計算
            position1 = ('center', (video_height - text1_height - text2_height - gap) // 2)
            position2 = ('center', (video_height + text1_height + gap) // 2)

            # 位置の設定
            text_clip1 = text_clip1.set_position(position1).set_duration(duration)
            text_clip2 = text_clip2.set_position(position2).set_duration(duration)

            final_video = CompositeVideoClip([video, text_clip1, text_clip2])
            final_output_path = 'fanal_waves.mp4'
            final_video.write_videofile(final_output_path, fps=fps, codec='libx264', audio_codec='aac')

        # 動画を表示
        with open(final_output_path, 'rb') as video_file:
            video_bytes = video_file.read()
            st.video(video_bytes)
        
        # 一時ファイルをクリーンアップ
        os.remove(audio_path)
        os.remove(output_path)
        os.remove(final_output_path)
else:
    st.sidebar.warning('楽曲ファイルをアップロードしてください。')

# 曲名とアーティスト名が入力されていない場合、警告を表示
if song_name == "":
    st.sidebar.warning('曲名を入力してください。')
if artist_name == "":
    st.sidebar.warning('アーティスト名を入力してください。')