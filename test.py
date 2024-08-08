import numpy as np
import librosa
import matplotlib.pyplot as plt
from moviepy.editor import VideoClip, AudioFileClip
from moviepy.video.io.bindings import mplfig_to_npimage

def analyze_audio(file_path):   #file_pathを引数に取り、y, sr, rms_normalizedを返す関数
    y, sr = librosa.load(file_path)   #file_pathの音声ファイルを読み込み、y, srに代入(yは波形データ、srはサンプリングレート)
    rms = librosa.feature.rms(y=y)[0]   #yのRMS(Root Mean Square)を計算し、rmsに代入
    rms_normalized = (rms - np.min(rms)) / (np.max(rms) - np.min(rms))  #rmsの正規化

    return y, sr, rms_normalized

def get_background_color(intensity):    #intensityを引数に取り、背景色を返す関数
    if intensity < 0.1:    #intensityが0.1未満の場合
        return (0, 0, 255) 
    
    else:
        red = int(255 * (intensity - 0.1) / 0.9)
        green = int(255 * (1 - (intensity - 0.1) / 0.9))
        return (red, green, 0)#

def make_frame(t, y, sr, rms_normalized, fps):  #t, y, sr, rms_normalized, fpsを引数に取り、frameを返す関数
    fig, ax = plt.subplots(figsize=(10, 2)) #fig, axを作成, 動画のサイズは(10, 2)

    start = int(t * sr)
    end = int((t + 1 / fps) * sr)
    ax.plot(y[start:end])   #ここで波形データをプロット(endの値を変えると波形データの表示範囲が変わる)

    ax.axis('off')  #軸を非表示

    intensity_index = int(t * len(rms_normalized) / duration)
    intensity_index = min(intensity_index, len(rms_normalized) - 1)
    color = get_background_color(rms_normalized[intensity_index])
    fig.patch.set_facecolor(np.array(color) / 255)
    frame = mplfig_to_npimage(fig)
    plt.close(fig)
    return frame

audio_path = ''   #ここに曲ファイル
y, sr, rms_normalized = analyze_audio(audio_path)
fps = 24
duration = len(y) / sr

video = VideoClip(lambda t: make_frame(t, y, sr, rms_normalized, fps), duration=duration)
audio = AudioFileClip(audio_path).subclip(0, duration)
video = video.set_audio(audio)
output_path = 'waves.mp4'
video.write_videofile(output_path, fps=fps)
