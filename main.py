import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter
import random

def butter_bandpass(lowcut, highcut, fs, order=6):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs):
    b, a = butter_bandpass(lowcut, highcut, fs)
    return lfilter(b, a, data)

def apply_volume_envelope(data, envelope):
    return data * envelope

def gen_random_volume_envelope(duration_samples, segment_ranges, min_db, max_db):
    envelope = np.zeros(duration_samples)
    pos = 0
    last_amp = random.uniform(min_db, max_db)
    while pos < duration_samples:
        seg_len = random.randint(*segment_ranges)
        seg_len = min(seg_len, duration_samples - pos)
        next_amp = random.uniform(min_db, max_db)
        segment_env = np.linspace(last_amp, next_amp, seg_len)
        envelope[pos:pos + seg_len] = segment_env
        pos += seg_len
        last_amp = next_amp
    envelope_lin = 10**(envelope / 20)
    return envelope_lin

def prepare_noise_audio(noise, target_length):
    """
    准备噪声音频，使用tile方式重复以达到目标长度
    """
    if len(noise) >= target_length:
        return noise[:target_length]
    else:
        # 计算需要重复的次数
        repeat_times = int(np.ceil(target_length / len(noise)))
        extended_noise = np.tile(noise, repeat_times)
        return extended_noise[:target_length]

def insert_random_radar(main, radar, density=0.05, fs=44100):
    """
    在主音频中随机插入雷达干扰声
    """
    main_copy = main.copy()
    times = int(len(main) / fs * density)
    for _ in range(times):
        if len(radar) < len(main):
            start_pos = random.randint(0, len(main) - len(radar))
            main_copy[start_pos:start_pos + len(radar)] += radar
    return main_copy

def mix_with_noise(main, noise, snr_db=-10):
    """
    按照指定信噪比混合主音频和噪声
    """
    # 确保噪声长度匹配
    noise_prepared = prepare_noise_audio(noise, len(main))
    
    # 计算RMS
    main_rms = np.sqrt(np.mean(main**2))
    noise_rms = np.sqrt(np.mean(noise_prepared**2))
    
    # 根据SNR调整噪声音量
    if noise_rms > 0:  # 避免除零
        desired_noise_rms = main_rms / (10**(snr_db / 20))
        noise_scaled = noise_prepared * (desired_noise_rms / noise_rms)
    else:
        noise_scaled = noise_prepared
    
    return main + noise_scaled

def create_noise_only_segment(duration_samples, noise, lowcut, highcut, fs):
    """
    创建只有噪声的音频段（用于前后留白）
    """
    # 准备足够长度的噪声
    noise_segment = prepare_noise_audio(noise, duration_samples)
    # 对噪声应用带通滤波
    filtered_noise_segment = bandpass_filter(noise_segment, lowcut, highcut, fs)
    return filtered_noise_segment

def process_ssb(
    input_file,
    output_file,
    noise_file,
    radar_file,
    lowcut=300,
    highcut=2700,
    seg_min=44100 * 2,  # 2 seconds
    seg_max=44100 * 10,  # 10 seconds
    min_db=-12,
    max_db=0,
    radar_density=0.05,
    snr_db=-10,
    pre_silence=44100 * 3,  # 3 seconds
    post_silence=44100 * 3   # 3 seconds
):
    print("开始处理SSB音频...")
    
    # 1. 读入所有音频文件
    print("1. 读取音频文件...")
    audio, fs = sf.read(input_file)
    if audio.ndim == 2:  # 如果是双声道，转换为单声道
        audio = audio.mean(axis=1)
    
    noise, noise_fs = sf.read(noise_file)
    if noise.ndim == 2:  # 确保噪声为单声道
        noise = noise.mean(axis=1)
    # 如果采样率不一致，这里可以添加重采样代码
    
    radar, radar_fs = sf.read(radar_file)
    if radar.ndim == 2:  # 确保雷达音为单声道
        radar = radar.mean(axis=1)
    # 如果采样率不一致，这里可以添加重采样代码
    
    # 2. 对所有音频应用相同的带通滤波
    print("2. 应用带通滤波...")
    filtered_audio = bandpass_filter(audio, lowcut, highcut, fs)
    filtered_noise = bandpass_filter(noise, lowcut, highcut, fs)
    filtered_radar = bandpass_filter(radar, lowcut, highcut, fs)
    
    # 3. 应用音量包络到主音频
    print("3. 应用音量包络...")
    envelope = gen_random_volume_envelope(len(filtered_audio), (seg_min, seg_max), min_db, max_db)
    processed_audio = apply_volume_envelope(filtered_audio, envelope)
    
    # 4. 加入雷达干扰
    print("4. 添加雷达干扰...")
    processed_audio = insert_random_radar(processed_audio, filtered_radar, radar_density, fs)
    
    # 5. 混合背景噪声
    print("5. 混合背景噪声...")
    processed_audio = mix_with_noise(processed_audio, filtered_noise, snr_db)
    
    # 6. 添加前后噪声段（而不是静音）
    print("6. 添加前后噪声段...")
    pre_noise_audio = create_noise_only_segment(pre_silence, filtered_noise, lowcut, highcut, fs)
    post_noise_audio = create_noise_only_segment(post_silence, filtered_noise, lowcut, highcut, fs)
    
    final_audio = np.concatenate((pre_noise_audio, processed_audio, post_noise_audio))
    
    # 7. 防止音频削波（可选）
    max_amplitude = np.max(np.abs(final_audio))
    if max_amplitude > 0.95:
        print(f"   检测到可能的削波，将音量降低到 {0.95/max_amplitude:.2f}")
        final_audio = final_audio * (0.95 / max_amplitude)
    
    # 8. 导出音频
    print("7. 导出音频...")
    sf.write(output_file, final_audio, fs)
    print(f"处理完成，输出到 {output_file}")
    print(f"最终音频长度: {len(final_audio)/fs:.2f} 秒")

# ========== 使用示例 ==========

if __name__ == "__main__":
    process_ssb(
        input_file="input.wav",      # 输入音频，格式wav
        output_file="output_ssb.wav", # 输出文件
        noise_file="noise.wav",      # 背景噪声文件
        radar_file="radar.wav",      # 雷达干扰声文件
        lowcut=300,                  # 带通滤波低频截止
        highcut=2700,                # 带通滤波高频截止
        seg_min=44100 * 1,          # 音量变化最短段（2秒）
        seg_max=44100 * 5,         # 音量变化最长段（10秒）
        min_db=-10,                  # 最小音量（分贝）
        max_db=10,                    # 最大音量（分贝）
        radar_density=0.02,          # 雷达干扰密度（次/秒）
        snr_db=3,                  # 信噪比（分贝）
        pre_silence=44100 * 3,       # 前置噪声段长度（3秒）
        post_silence=44100 * 3       # 后置噪声段长度（3秒）
    )