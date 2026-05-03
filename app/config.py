import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 上传文件目录
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 模型文件目录
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

# 输出文件目录
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# 静态文件目录
STATIC_DIR = BASE_DIR / "static"

# 允许的音频文件格式
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}

# 最大文件大小（100MB）
MAX_FILE_SIZE = 100 * 1024 * 1024

# 配置设置
class Settings:
    def __init__(self):
        self.base_dir = BASE_DIR
        self.upload_dir = UPLOAD_DIR
        self.model_dir = MODEL_DIR
        self.output_dir = OUTPUT_DIR
        self.static_dir = STATIC_DIR
        self.allowed_extensions = ALLOWED_EXTENSIONS
        self.max_file_size = MAX_FILE_SIZE
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))

settings = Settings()
