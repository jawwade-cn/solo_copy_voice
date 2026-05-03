# 声音复刻智能体项目搭建记录

## 日期
2026-05-03

## 项目概述
在 `d:\trae_projects\solo_coder_10\solo_copy_voice\` 文件夹下搭建一个声音复刻智能体项目，使用Git管理，远程地址为 `https://github.com/jawwade-cn/solo_copy_voice.git`。

---

## 步骤1：检查Git仓库状态

### 操作
```bash
git status
git remote -v
```

### 结果
- Git仓库已初始化
- 远程地址已配置为：`https://github.com/jawwade-cn/solo_copy_voice.git`
- 当前分支：main

---

## 步骤2：检查Python环境

### 操作
```bash
py --version
py -0
```

### 结果
- Python版本：3.13.12
- 系统中只有Python 3.13可用

---

## 步骤3：创建Python虚拟环境

### 操作
```bash
py -m venv .venv
```

### 验证
```bash
.\.venv\Scripts\python.exe --version
```

### 结果
- 虚拟环境创建成功，位于 `.venv` 目录
- Python版本：3.13.12

---

## 步骤4：安装依赖（第一次尝试 - 失败）

### 原始requirements.txt内容
```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
aiofiles==23.2.1
TTS==0.22.0
torch==2.1.1
torchaudio==2.1.1
librosa==0.10.1
pydub==0.25.1
numpy==1.26.2
scipy==1.11.4
soundfile==0.12.1
```

### 操作
```bash
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### 问题1：TTS库不支持Python 3.13
- **错误信息**：`ERROR: Could not find a version that satisfies the requirement TTS==0.22.0 (from versions: none)`
- **原因**：Coqui TTS库最多只支持到Python 3.12，当前Python版本是3.13
- **影响**：无法安装TTS、torch、torchaudio等库

### 问题2：numpy需要编译
- **错误信息**：`Preparing metadata (pyproject.toml) did not run successfully`
- **原因**：系统中没有C++编译器，无法从源码编译numpy
- **影响**：无法安装numpy、scipy、soundfile等需要编译的库

---

## 步骤5：修改代码以支持演示模式

### 问题分析
由于Python 3.13与TTS库不兼容，且系统缺少C++编译器，需要修改代码使其在没有这些库的情况下也能运行。

### 修改内容

#### 1. 修改 `app/voice_cloner.py`
- 移除对 `numpy` 和 `soundfile` 的硬依赖
- 使用Python内置的 `wave` 模块生成演示用的静音WAV文件
- 改进错误处理，当TTS、librosa、pydub等库不可用时，使用演示模式

#### 2. 修改 `app/main.py`
- 移除未使用的导入 `Jinja2Templates` 和 `Request`

#### 3. 修改 `requirements.txt`
简化依赖列表，只保留纯Python库：
```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
aiofiles==23.2.1
```

---

## 步骤6：重新安装基础依赖（成功）

### 操作
```bash
.\.venv\Scripts\pip.exe install -r requirements.txt
```

### 结果
```
Successfully installed:
- aiofiles-23.2.1
- annotated-types-0.7.0
- anyio-3.7.1
- click-8.3.3
- colorama-0.4.6
- fastapi-0.104.1
- h11-0.16.0
- idna-3.13
- pydantic-2.13.3
- pydantic-core-2.46.3
- python-multipart-0.0.6
- sniffio-1.3.1
- starlette-0.27.0
- typing-extensions-4.15.0
- typing-inspection-0.4.2
- uvicorn-0.24.0
```

### 验证代码导入
```bash
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); from app.main import app; print('Import successful')"
```

### 结果
```
TTS library not installed. Voice cloning will not be available.
librosa not available. Audio processing will be limited.
pydub not available. Audio format conversion will be limited.
Import successful
```

✅ **代码导入成功！** 这意味着：
- 所有必要的依赖都已正确安装
- 代码语法正确
- 即使缺少TTS、librosa、pydub等可选库，代码也能正常运行（演示模式）

---

## 步骤7：安装预编译的音频处理库（成功）

### 问题分析
之前的numpy安装失败是因为尝试从源码编译。但实际上，PyPI上已经有支持Python 3.13的预编译wheel文件。

### 操作
```bash
.\.venv\Scripts\pip.exe install numpy --only-binary :all:
.\.venv\Scripts\pip.exe install soundfile scipy --only-binary :all:
.\.venv\Scripts\pip.exe install librosa pydub --only-binary :all:
```

### 结果
```
Successfully installed:
- numpy-2.4.4
- soundfile-0.13.1
- scipy-1.17.1
- librosa-0.11.0
- pydub-0.25.1
- 以及相关依赖（numba, llvmlite, scikit-learn等）
```

---

## 步骤8：安装edge-tts（微软文本转语音库）

### 问题分析
由于Coqui TTS不支持Python 3.13，我们需要一个替代方案来生成实际的语音。edge-tts是微软的开源TTS库，支持多种语言和语音，并且与Python 3.13兼容。

### 操作
```bash
.\.venv\Scripts\pip.exe install edge-tts
```

### 结果
```
Successfully installed:
- edge_tts-7.2.8
- aiohttp-3.13.5
- 以及相关依赖
```

---

## 步骤9：修改代码集成edge-tts

### 问题分析
需要修改代码，使其在Coqui TTS不可用时，使用edge-tts来生成实际的语音。

### 修改内容

#### 1. 修改 `app/voice_cloner.py`
- 添加edge-tts的导入和可用性检查
- 创建 `_generate_with_edge_tts` 方法，使用edge-tts生成语音
- 支持语速和音调调整
- 处理ffmpeg不可用的情况（无法转换MP3到WAV时，直接返回MP3）
- 修复参数问题：当pitch为0时，edge-tts不接受"+0%"格式

#### 2. 关键修复

**问题1：pitch参数为0时的格式问题**
- **错误**：`Invalid pitch '+0%'`
- **原因**：edge-tts不接受"+0%"格式，只接受"0%"或不传递参数
- **修复**：当rate或pitch为0时，不传递这些参数

**问题2：ffmpeg不可用导致转换失败**
- **错误**：`[WinError 2] 系统找不到指定的文件`
- **原因**：pydub需要ffmpeg来转换音频格式
- **修复**：当转换失败时，直接返回MP3文件，不进行格式转换

**问题3：重命名时的路径冲突**
- **错误**：`FileNotFoundError: [WinError 2] ... -> ...`
- **原因**：临时文件和目标文件是同一个文件
- **修复**：添加检查，只有当路径不同时才进行重命名

---

## 步骤10：测试完整流程

### 测试脚本
创建 `test_full_flow.py` 来测试完整的流程：
1. 检查库的可用性
2. 创建VoiceCloner实例
3. 注册声音（演示模式）
4. 生成语音（使用edge-tts）

### 操作
```bash
.\.venv\Scripts\python.exe test_full_flow.py
```

### 测试结果

```
============================================================
Testing Full Flow: Voice Registration and Text-to-Speech
============================================================

[1] Library Availability:
  - Coqui TTS (Voice Cloning):   NOT AVAILABLE (Requires Python 3.11/3.12)
  - edge-tts (Basic TTS):         AVAILABLE
  - librosa (Audio Processing):   AVAILABLE
  - pydub (Audio Format):         AVAILABLE

[2] Creating VoiceCloner instance...
    [OK] VoiceCloner created successfully

[3] Testing Voice Registration (Demo Mode)...
    [OK] Voice registered: test_speaker
    [NOTE] Running in Demo Mode
    [NOTE] Voice cloning requires Python 3.11 or 3.12 with Coqui TTS

[4] Testing Text-to-Speech...
    [OK] Speech generated successfully!
    - Output file: outputs\test_speaker_2c14a5ac.mp3
    - Filename: test_speaker_2c14a5ac.mp3
    - Message: Speech generated with edge-tts (Demo Mode - using preset voice)
    - Voice used: zh-CN-XiaoxiaoNeural (晓晓)
    - Note: Voice cloning requires Python 3.11 or 3.12 with Coqui TTS
    - File size: 45072 bytes

[SUCCESS] You can now play the audio file!
          File location: D:\trae_projects\solo_coder_10\solo_copy_voice\outputs\test_speaker_2c14a5ac.mp3

============================================================
FULL FLOW TEST COMPLETED SUCCESSFULLY!
============================================================
```

### 关键发现

1. **edge-tts成功生成了实际的语音文件**
   - 输出文件：`outputs\test_speaker_2c14a5ac.mp3`
   - 文件大小：**45072字节**（约45KB）- 这是**实际的语音文件**，不是静音！
   - 之前的静音WAV文件是543944字节，现在的MP3文件是45072字节

2. **使用的语音**：`zh-CN-XiaoxiaoNeural (晓晓)` - 微软的中文女声

3. **输出格式**：MP3（因为ffmpeg不可用，无法转换为WAV）

---

## 步骤11：启动应用

### 启动命令
```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 或者（开发模式，带自动重载）
```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 访问界面
启动后，打开浏览器访问：`http://127.0.0.1:8000`

---

## 当前安装的所有依赖

### 列表
```
Package                   Version
------------------------- ---------
aiofiles                  23.2.1
aiohappyeyeballs         2.6.1
aiohttp                   3.13.5
aiosignal                 1.4.0
annotated-types           0.7.0
anyio                     3.7.1
attrs                     26.1.0
audioop-lts               0.2.2
audioread                 3.1.0
certifi                   2026.4.22
cffi                      2.0.0
charset-normalizer        3.4.7
click                     8.3.3
colorama                  0.4.6
decorator                 5.2.1
edge-tts                  7.2.8
fastapi                   0.104.1
frozenlist                1.8.0
h11                       0.16.0
idna                      3.13
joblib                    1.5.3
lazy-loader               0.5
librosa                   0.11.0
llvmlite                  0.47.0
msgpack                   1.1.2
multidict                 6.7.1
numba                     0.65.1
numpy                     2.4.4
packaging                 26.2
platformdirs              4.9.6
pooch                     1.9.0
propcache                 0.4.1
pydantic                  2.13.3
pydantic-core             2.46.3
pydub                     0.25.1
pycparser                 3.0
python-multipart          0.0.6
requests                  2.33.1
scikit-learn              1.8.0
scipy                     1.17.1
sniffio                   1.3.1
soundfile                 0.13.1
soxr                      1.1.0
standard-aifc             3.13.0
standard-chunk            3.13.0
standard-sunau            3.13.0
starlette                 0.27.0
tabulate                  0.10.0
threadpoolctl             3.6.0
typing-extensions         4.15.0
typing-inspection         0.4.2
urllib3                   2.6.3
uvicorn                   0.24.0
yarl                      1.23.0
```

---

## 项目结构

```
solo_copy_voice/
├── .venv/                          # Python虚拟环境
├── app/                            # 后端代码
│   ├── __init__.py                # 初始化文件
│   ├── config.py                  # 配置文件
│   ├── main.py                    # FastAPI主应用
│   └── voice_cloner.py            # 声音复刻核心功能（集成edge-tts）
├── static/                         # 前端静态文件
│   ├── css/
│   │   └── style.css              # 样式文件
│   ├── js/
│   │   └── app.js                 # 前端逻辑
│   └── index.html                 # 主页面
├── uploads/                        # 上传文件目录（运行时创建）
├── models/                         # 模型文件目录（运行时创建）
├── outputs/                        # 输出文件目录（运行时创建）
│   └── *.mp3 / *.wav              # 生成的音频文件
├── .gitignore                      # Git忽略文件
├── README.md                       # 项目说明
├── requirements.txt                # Python依赖（当前版本）
├── requirements_full.txt           # 完整依赖（需要Python 3.11/3.12）
├── test_import.py                  # 导入测试脚本
├── test_tts.py                     # edge-tts测试脚本
├── test_full_flow.py               # 完整流程测试脚本
└── SETUP_LOG.md                    # 本搭建记录文件
```

---

## API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 主页 |
| POST | /api/clone-voice | 上传音频并注册声音（演示模式） |
| POST | /api/text-to-speech | 使用edge-tts生成语音 |
| GET | /api/download/{filename} | 下载生成的音频文件 |
| GET | /api/speakers | 获取所有已注册的说话人 |
| DELETE | /api/speakers/{speaker_id} | 删除指定的说话人 |
| GET | /api/health | 健康检查 |

---

## 当前状态

### ✅ 已完成
1. ✅ Git仓库已配置并连接到远程
2. ✅ Python虚拟环境已创建
3. ✅ 基础依赖已安装（fastapi, uvicorn等）
4. ✅ 音频处理库已安装（numpy, scipy, librosa, pydub, soundfile）
5. ✅ edge-tts已安装并集成到代码中
6. ✅ 代码修改完成，支持演示模式
7. ✅ 完整流程测试通过，**可以生成实际的语音**

### ⚠️ 当前限制

#### 1. 声音克隆功能不可用
- **原因**：Coqui TTS（声音克隆库）不支持Python 3.13
- **影响**：无法从音频文件中复刻声音
- **替代方案**：使用edge-tts的预设语音

#### 2. 使用的是预设语音，不是克隆的声音
- **当前使用**：`zh-CN-XiaoxiaoNeural (晓晓)` - 微软的中文女声
- **可用语音**：
  - 晓晓（女，简体中文）
  - 云希（男，简体中文）
  - 云健（男，简体中文）
  - 晓伊（女，简体中文）
  - 曉佳（女，繁体中文-香港）
  - 雲龍（男，繁体中文-香港）
  - 曉臻（女，繁体中文-台湾）
  - 雲哲（男，繁体中文-台湾）

#### 3. 输出格式是MP3，不是WAV
- **原因**：系统中没有安装ffmpeg，pydub无法转换音频格式
- **影响**：生成的音频文件是MP3格式
- **解决方案**：安装ffmpeg后可以转换为WAV

### 🔧 如何启用完整的声音克隆功能

要实现从音频文件中克隆声音的功能，需要：

#### 方案1：安装Python 3.11或3.12（推荐）

**步骤：**
1. **下载并安装Python 3.11或3.12**
   - 从 https://www.python.org/downloads/ 下载
   - 安装时勾选"Add Python to PATH"

2. **创建新的虚拟环境**
   ```bash
   # 使用Python 3.11创建虚拟环境
   py -3.11 -m venv .venv311
   
   # 或者使用Python 3.12
   py -3.12 -m venv .venv312
   ```

3. **激活虚拟环境**
   ```bash
   .\.venv311\Scripts\activate
   ```

4. **安装完整依赖**
   ```bash
   pip install -r requirements_full.txt
   ```

   **requirements_full.txt内容：**
   ```
   fastapi==0.104.1
   uvicorn==0.24.0
   python-multipart==0.0.6
   aiofiles==23.2.1
   TTS==0.22.0
   torch==2.1.1
   torchaudio==2.1.1
   librosa==0.10.1
   pydub==0.25.1
   numpy==1.26.2
   scipy==1.11.4
   soundfile==0.12.1
   edge-tts==7.2.8
   ```

5. **启动应用**
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

#### 方案2：安装ffmpeg（可选，用于音频格式转换）

如果安装了ffmpeg，pydub可以将MP3转换为WAV格式。

**Windows安装步骤：**
1. 从 https://www.gyan.dev/ffmpeg/builds/ 下载ffmpeg
2. 解压到某个目录（如 `C:\ffmpeg`）
3. 将 `C:\ffmpeg\bin` 添加到系统PATH环境变量
4. 重启终端

---

## 使用说明

### 1. 启动应用
```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. 访问界面
打开浏览器访问：`http://127.0.0.1:8000`

### 3. 操作流程

#### 步骤1：注册声音（演示模式）
1. 点击"选择音频文件"，选择一段音频文件（WAV、MP3、M4A、FLAC、OGG格式）
2. （可选）输入说话人名称
3. 点击"克隆声音"按钮
4. 系统会保存音频路径，但**不会实际克隆声音**（需要Coqui TTS）

#### 步骤2：生成语音
1. 在下拉列表中选择已注册的声音
2. 输入要朗读的文本
3. 调整语速（0.5 - 2.0倍）
4. 调整音调（-12 - +12半音）
5. 选择语气（当前在演示模式下不生效）
6. 点击"生成语音"按钮
7. 系统会使用edge-tts的预设语音（晓晓）生成语音

#### 步骤3：播放和下载
1. 生成的音频文件会显示在"播放和下载"部分
2. 点击播放按钮可以直接在浏览器中播放
3. 点击"下载音频"按钮可以下载文件

---

## 功能对比

| 功能 | 演示模式（当前） | 完整模式（需要Python 3.11/3.12） |
|------|-----------------|-------------------------------|
| 上传音频文件 | ✅ | ✅ |
| 注册说话人 | ✅（演示） | ✅（实际克隆） |
| 文本转语音 | ✅（使用预设语音） | ✅（使用克隆的声音） |
| 语速调整 | ✅ | ✅ |
| 音调调整 | ✅ | ✅ |
| 从音频克隆声音 | ❌ | ✅ |
| 使用克隆的声音朗读 | ❌ | ✅ |
| 多种语音选择 | ✅（8种预设） | ✅（无限种，可克隆任何声音） |

---

## 测试文件说明

### 1. `test_import.py`
测试代码导入是否成功，检查库的可用性。

### 2. `test_tts.py`
单独测试edge-tts功能，生成测试音频文件。

### 3. `test_full_flow.py`
测试完整的流程：注册声音 → 生成语音。

---

## Git提交记录

### 初始提交
```
[main 13fbe93] Initial commit: 搭建声音复刻智能体项目
 9 files changed, 1367 insertions(+)
```

### 后续修改
- 集成edge-tts
- 修复参数格式问题
- 修复ffmpeg不可用的问题
- 修复路径冲突问题

---

## 总结

### 项目状态
项目已成功搭建，并且**可以生成实际的语音**（使用edge-tts的预设语音）。虽然无法实现从音频文件中克隆声音的功能（需要Python 3.11/3.12），但文本转语音功能完全可用。

### 当前可用的功能
1. ✅ **文本转语音**：使用微软edge-tts，支持8种中文语音
2. ✅ **语速调整**：0.5倍到2.0倍
3. ✅ **音调调整**：-12半音到+12半音
4. ✅ **Web界面**：直观的用户界面
5. ✅ **API接口**：完整的RESTful API

### 需要Python 3.11/3.12才能启用的功能
1. ❌ **声音克隆**：从音频文件中提取声音特征
2. ❌ **使用克隆的声音**：用复刻的声音朗读文本

### 下一步建议
1. 如果需要声音克隆功能，安装Python 3.11或3.12
2. （可选）安装ffmpeg以支持WAV格式输出
3. 启动应用并测试所有功能

---

*记录完成时间：2026-05-03*
*最后更新：2026-05-03（集成edge-tts，测试通过）*
