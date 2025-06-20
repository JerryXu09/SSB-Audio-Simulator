# SSB Audio Simulator
Making an audio sounds like played from a SSB radio. Coded with AI.

让一段音频具有听起来像是从单边带电台中传出的效果。代码由 AI 生成。

## 原理
- 对音频进行带通滤波(默认留下300Hz~2700Hz)
- 混合本底噪声，模拟真实收听的效果
- 模拟电离层传播不稳定时声音忽大忽小的效果
- 在随机位置添加电离层扫描雷达的声音
- 音频前后留白，模拟真实收听效果

## 使用方法
1. 安装依赖

```
pip install numpy soundfile scipy
```

2. 下载程序
3. 在程序同级目录下准备需要制作的音频文件 `input.wav`。其他所需音频已准备好，可立即使用，也可自行替换。
4. 运行 `python3 main.py`

## 文件解释
`input.wav` - 这是你的音频输入文件，似乎只支持 wav 格式。

`noise.wav` - 这是底噪文件。

`radar.wav` - 这是电离层扫描雷达的声音。

## 参数解释
> 这一部分用来调整文件相关参数。

```
input_file="input.wav",      # 输入音频文件(格式wav)
output_file="output_ssb.wav", # 输出音频文件
noise_file="noise.wav",      # 背景噪声文件
radar_file="radar.wav",      # 雷达扫描声文件
```

> 这一部分对所有音频进行带通滤波。
```
lowcut=300,                  # 带通滤波低频截止
highcut=2700,                # 带通滤波高频截止
```

> 这一部分用来模拟电离层传播不稳定而造成的衰落/回升的效果。
> 将音频分为若干段，每一段音量会变大/变小，且每段长度(默认1~5s)均不同。
```
seg_min=44100 * 1,          # 音量变化最短段
seg_max=44100 * 5,         # 音量变化最长段
min_db=-10,                  # 最小音量
max_db=10,                    # 最大音量
```

> 这一部分用来调整电离层扫描雷达出现的频率。

```
radar_density=0.02,          # 雷达出现密度(每秒出现的次数)
```

> 这一部分用来调整信噪比。

```
snr_db=3,                  # 信噪比
```

> 这一部分用来调整前后留白时间的长短。

```
pre_silence=44100 * 3,       # 前置噪声留白段长度
post_silence=44100 * 3        # 后置噪声留白段长度
```
