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

# セッションステートに楽曲リストを保持する
if 'song_list' not in st.session_state:
    st.session_state.song_list = []

# 音声を解析してRMS（Root Mean Square）を計算する関数
def analyze_audio(file_path):
    y, sr = librosa.load(file_path, sr=None)  # sr=Noneで元のサンプリングレートを使用
    rms = librosa.feature.rms(y=y)[0]
    rms_normalized = (rms - np.min(rms)) / (np.max(rms) - np.min(rms))
    return y, sr, rms_normalized

# 背景色を音の強度に基づいて決定する関数
def get_background_color(intensity):
    if intensity < 0.1:
        return (0, 255, 150)
    else:
        red = int(255 * (intensity - 0.1) / 0.9)
        green = int(255 * (1 - (intensity - 0.1) / 0.9))
        return (red, green, 150)

# 動画のフレームを作成する関数
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

# サイドバーに音声ファイルをアップロードする項目を設定し、アップロードを促す
st.sidebar.subheader("楽曲をアップロードしてください")
uploaded_file = st.sidebar.file_uploader("MP3ファイルを選択してください", type="mp3")

# サイドバーに曲名を入力する項目を設定し、入力を促す
st.sidebar.subheader("曲名を入力してください")
song_name = st.sidebar.text_input("曲名", "")

st.sidebar.subheader("アーティスト名を入力してください")
artist_name = st.sidebar.text_input("アーティスト名", "")

# 曲をリストに追加するボタン
if st.sidebar.button('楽曲をリストに追加'):
    if uploaded_file is not None and song_name and artist_name:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(uploaded_file.read())
            st.session_state.song_list.append({"name": song_name, "artist": artist_name, "path": tmp_file.name})
        st.sidebar.success(f'「{song_name}」がリストに追加されました。')
    else:
        st.sidebar.warning('すべての項目を入力し、楽曲をアップロードしてください。')

# 曲を選択するドロップダウン
if st.session_state.song_list:
    st.sidebar.subheader("生成する楽曲を選択してください")
    selected_index = st.sidebar.selectbox("楽曲を選択", range(len(st.session_state.song_list)),
                                          format_func=lambda i: f"{st.session_state.song_list[i]['name']} - {st.session_state.song_list[i]['artist']}")

    if selected_index is not None:
        selected_song = st.session_state.song_list[selected_index]

        # 選択した楽曲を基に動画を作成
        if st.sidebar.button('作成'):
            song_name = selected_song['name']
            artist_name = selected_song['artist']
            audio_path = selected_song['path']
            
            y, sr, rms_normalized = analyze_audio(audio_path)
            fps = 24
            duration = len(y) / sr
            
            st.header(f'{song_name}')
            st.text(f' {artist_name}')
            with st.spinner('動画を作成中...'):
                video = VideoClip(lambda t: make_frame(t, y, sr, rms_normalized, fps, duration), duration=duration)
                audio = AudioFileClip(audio_path).subclip(0, duration)
                video = video.set_audio(audio).set_duration(duration)
                output_path = 'waves.mp4'
                video.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac')

                text_color = 'rgb(254, 249, 245)'
                text_clip1 = TextClip(f"{song_name}", fontsize=60, color=f'{text_color}', font="../font/Koruri-Light.ttf")
                text_clip2 = TextClip(f"{artist_name}", fontsize=40, color=f'{text_color}', font="../font/Koruri-Light.ttf")

                video_height = 600  # 600pの動画を想定
                text1_height = text_clip1.size[1]
                text2_height = text_clip2.size[1]
                gap = 10  # テキストクリップ間のスペース

                position1 = ('center', (video_height - text1_height - text2_height - gap) // 2)
                position2 = ('center', (video_height + text1_height + gap) // 2)

                text_clip1 = text_clip1.set_position(position1).set_duration(duration)
                text_clip2 = text_clip2.set_position(position2).set_duration(duration)

                final_video = CompositeVideoClip([video, text_clip1, text_clip2])
                final_output_path = 'final_waves.mp4'
                final_video.write_videofile(final_output_path, fps=fps, codec='libx264', audio_codec='aac')

            with open(final_output_path, 'rb') as video_file:
                video_bytes = video_file.read()
                st.video(video_bytes)

            os.remove(audio_path)
            os.remove(output_path)
            os.remove(final_output_path)

        # 選択した楽曲をリストから削除するボタン
        if st.sidebar.button('削除'):
            del st.session_state.song_list[selected_index]
            st.sidebar.success(f"「{song_name}」がリストから削除されました。")
else:
    st.sidebar.warning('楽曲がリストに追加されていません。')

# 曲名とアーティスト名が入力されていない場合、警告を表示
if song_name == "":
    st.sidebar.warning('曲名を入力してください。')
if artist_name == "":
    st.sidebar.warning('アーティスト名を入力してください。')