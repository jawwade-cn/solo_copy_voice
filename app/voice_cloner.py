import os
import uuid
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("TTS library not installed. Voice cloning will not be available.")

try:
    import librosa
    import librosa.effects
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not installed. Audio processing will be limited.")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not installed. Audio format conversion will be limited.")


class VoiceCloner:
    """声音复刻类，支持声音克隆和文本转语音"""
    
    def __init__(self, model_dir: Path, output_dir: Path):
        """
        初始化声音复刻器
        
        Args:
            model_dir: 模型文件目录
            output_dir: 输出文件目录
        """
        self.model_dir = model_dir
        self.output_dir = output_dir
        self.tts_model = None
        self.speaker_embeddings = {}
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_tts_model(self):
        """加载TTS模型"""
        if not TTS_AVAILABLE:
            raise RuntimeError("TTS library is not available. Please install it with 'pip install TTS'.")
        
        if self.tts_model is None:
            logger.info("Loading TTS model...")
            # 使用多语言TTS模型，支持声音克隆
            self.tts_model = TTS("tts_models/multilingual/multi-dataset/your_tts")
            logger.info("TTS model loaded successfully.")
        
        return self.tts_model
    
    def clone_voice(self, audio_path: str, speaker_name: Optional[str] = None) -> Dict[str, Any]:
        """
        从音频文件中克隆声音
        
        Args:
            audio_path: 音频文件路径
            speaker_name: 说话人名称（可选）
        
        Returns:
            包含克隆结果的字典
        """
        if not TTS_AVAILABLE:
            return {
                "success": False,
                "error": "TTS library is not available. Please install it with 'pip install TTS'."
            }
        
        try:
            # 生成唯一的说话人ID
            speaker_id = speaker_name or str(uuid.uuid4())
            
            # 加载音频文件
            if not os.path.exists(audio_path):
                return {
                    "success": False,
                    "error": f"Audio file not found: {audio_path}"
                }
            
            # 保存说话人音频路径
            self.speaker_embeddings[speaker_id] = audio_path
            
            logger.info(f"Voice cloned successfully for speaker: {speaker_id}")
            
            return {
                "success": True,
                "speaker_id": speaker_id,
                "message": "Voice cloned successfully"
            }
            
        except Exception as e:
            logger.error(f"Error cloning voice: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def text_to_speech(
        self, 
        text: str, 
        speaker_id: str, 
        language: str = "zh",
        speed: float = 1.0,
        pitch: float = 0.0,
        emotion: str = "neutral",
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用克隆的声音将文本转换为语音
        
        Args:
            text: 要转换的文本
            speaker_id: 说话人ID
            language: 语言代码（默认中文"zh"）
            speed: 语速调整（1.0为正常速度）
            pitch: 音调调整（0.0为正常音调）
            emotion: 语气风格（neutral, happy, sad, angry等）
            output_filename: 输出文件名（可选）
        
        Returns:
            包含生成结果的字典
        """
        if not TTS_AVAILABLE:
            return {
                "success": False,
                "error": "TTS library is not available. Please install it with 'pip install TTS'."
            }
        
        try:
            # 检查说话人是否存在
            if speaker_id not in self.speaker_embeddings:
                return {
                    "success": False,
                    "error": f"Speaker not found: {speaker_id}. Please clone a voice first."
                }
            
            # 加载TTS模型
            tts = self._load_tts_model()
            
            # 生成输出文件名
            if output_filename is None:
                output_filename = f"{speaker_id}_{uuid.uuid4().hex[:8]}.wav"
            
            output_path = self.output_dir / output_filename
            
            # 获取说话人音频路径
            speaker_wav = self.speaker_embeddings[speaker_id]
            
            # 生成语音
            logger.info(f"Generating speech for text: {text[:50]}...")
            
            # 使用your_tts模型进行声音克隆
            tts.tts_to_file(
                text=text,
                file_path=str(output_path),
                speaker_wav=speaker_wav,
                language=language
            )
            
            # 应用音频参数调整
            if speed != 1.0 or pitch != 0.0:
                self._adjust_audio_parameters(str(output_path), speed, pitch)
            
            logger.info(f"Speech generated successfully: {output_path}")
            
            return {
                "success": True,
                "output_path": str(output_path),
                "filename": output_filename,
                "message": "Speech generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _adjust_audio_parameters(self, audio_path: str, speed: float, pitch: float):
        """
        调整音频参数（语速和音调）
        
        Args:
            audio_path: 音频文件路径
            speed: 语速调整系数
            pitch: 音调调整（半音数）
        """
        if not LIBROSA_AVAILABLE:
            logger.warning("librosa not available. Skipping audio parameter adjustment.")
            return
        
        try:
            # 加载音频
            y, sr = librosa.load(audio_path, sr=None)
            
            # 调整语速
            if speed != 1.0:
                y = librosa.effects.time_stretch(y, rate=speed)
            
            # 调整音调
            if pitch != 0.0:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch)
            
            # 保存调整后的音频
            sf.write(audio_path, y, sr)
            
            logger.info(f"Audio parameters adjusted: speed={speed}, pitch={pitch}")
            
        except Exception as e:
            logger.error(f"Error adjusting audio parameters: {str(e)}")
    
    def list_speakers(self) -> Dict[str, str]:
        """
        列出所有已克隆的说话人
        
        Returns:
            说话人ID到音频路径的映射
        """
        return self.speaker_embeddings.copy()
    
    def delete_speaker(self, speaker_id: str) -> bool:
        """
        删除指定的说话人
        
        Args:
            speaker_id: 说话人ID
        
        Returns:
            是否成功删除
        """
        if speaker_id in self.speaker_embeddings:
            del self.speaker_embeddings[speaker_id]
            logger.info(f"Speaker deleted: {speaker_id}")
            return True
        return False
    
    def convert_audio_format(self, input_path: str, output_path: str, output_format: str = "wav") -> bool:
        """
        转换音频格式
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            output_format: 输出格式（wav, mp3等）
        
        Returns:
            是否成功转换
        """
        if not PYDUB_AVAILABLE:
            logger.warning("pydub not available. Cannot convert audio format.")
            return False
        
        try:
            # 加载音频
            audio = AudioSegment.from_file(input_path)
            
            # 导出为指定格式
            audio.export(output_path, format=output_format)
            
            logger.info(f"Audio converted from {input_path} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error converting audio format: {str(e)}")
            return False
