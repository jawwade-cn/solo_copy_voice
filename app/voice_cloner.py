import os
import uuid
import wave
import struct
import asyncio
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
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts library not installed. Using silent demo mode.")

try:
    import librosa
    import librosa.effects
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available. Audio processing will be limited.")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available. Audio format conversion will be limited.")


# 预设的语音列表（edge-tts支持的中文语音）
PRESET_VOICES = {
    "zh-CN-XiaoxiaoNeural": {"name": "晓晓", "gender": "Female", "language": "zh-CN"},
    "zh-CN-YunxiNeural": {"name": "云希", "gender": "Male", "language": "zh-CN"},
    "zh-CN-YunjianNeural": {"name": "云健", "gender": "Male", "language": "zh-CN"},
    "zh-CN-XiaoyiNeural": {"name": "晓伊", "gender": "Female", "language": "zh-CN"},
    "zh-HK-HiuGaaiNeural": {"name": "曉佳", "gender": "Female", "language": "zh-HK"},
    "zh-HK-WanLungNeural": {"name": "雲龍", "gender": "Male", "language": "zh-HK"},
    "zh-TW-HsiaoChenNeural": {"name": "曉臻", "gender": "Female", "language": "zh-TW"},
    "zh-TW-YunJheNeural": {"name": "雲哲", "gender": "Male", "language": "zh-TW"},
}


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
            
            if not TTS_AVAILABLE:
                logger.warning("TTS library not available. Running in demo mode with edge-tts.")
                return {
                    "success": True,
                    "speaker_id": speaker_id,
                    "message": "Voice registered (Demo Mode - using preset voices from edge-tts)",
                    "demo_mode": True,
                    "note": "Voice cloning requires Python 3.11 or 3.12 with Coqui TTS"
                }
            
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
        try:
            # 检查说话人是否存在
            if speaker_id not in self.speaker_embeddings:
                return {
                    "success": False,
                    "error": f"Speaker not found: {speaker_id}. Please clone a voice first."
                }
            
            # 生成输出文件名
            if output_filename is None:
                output_filename = f"{speaker_id}_{uuid.uuid4().hex[:8]}.wav"
            
            output_path = self.output_dir / output_filename
            
            # 如果Coqui TTS不可用，尝试使用edge-tts
            if not TTS_AVAILABLE:
                if EDGE_TTS_AVAILABLE:
                    logger.info("Using edge-tts for text-to-speech (demo mode)")
                    success, actual_output_path = self._generate_with_edge_tts(
                        str(output_path), text, language, speed, pitch
                    )
                    if success:
                        # 获取实际的文件名
                        actual_filename = os.path.basename(actual_output_path)
                        return {
                            "success": True,
                            "output_path": actual_output_path,
                            "filename": actual_filename,
                            "message": "Speech generated with edge-tts (Demo Mode - using preset voice)",
                            "demo_mode": True,
                            "voice_used": "zh-CN-XiaoxiaoNeural (晓晓)",
                            "note": "Voice cloning requires Python 3.11 or 3.12 with Coqui TTS",
                            "format": "MP3" if actual_output_path.endswith('.mp3') else "WAV"
                        }
                
                # 如果edge-tts也不可用，生成静音
                logger.warning("No TTS library available. Generating silent audio.")
                self._generate_silent_audio(str(output_path), text, speed)
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "filename": output_filename,
                    "message": "Silent audio generated (no TTS library available)",
                    "demo_mode": True,
                    "silent": True
                }
            
            # 加载TTS模型
            tts = self._load_tts_model()
            
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
    
    def _generate_with_edge_tts(
        self, 
        output_path: str, 
        text: str, 
        language: str = "zh",
        speed: float = 1.0,
        pitch: float = 0.0
    ) -> tuple:
        """
        使用edge-tts生成语音
        
        Args:
            output_path: 输出文件路径
            text: 文本内容
            language: 语言代码
            speed: 语速
            pitch: 音调
        
        Returns:
            (成功标志, 实际输出路径)
        """
        try:
            # 选择合适的语音
            voice = "zh-CN-XiaoxiaoNeural"  # 默认使用晓晓
            
            # 计算语速和音调参数
            # edge-tts的语速范围：-50% 到 +100%
            # 我们的speed参数：0.5 到 2.0
            # 转换：speed=0.5 -> rate=-50%, speed=2.0 -> rate=+100%
            rate_percent = int((speed - 1.0) * 100)
            # edge-tts不接受"+0%"，只接受"0%"或不传递参数
            if rate_percent == 0:
                rate_str = None
            else:
                rate_str = f"{rate_percent:+d}%"
            
            # 音调参数：edge-tts使用Hz或百分比
            # 我们的pitch参数：-12 到 +12（半音数）
            # 粗略转换为百分比
            pitch_percent = int(pitch * 5)  # 每个半音约5%
            # edge-tts不接受"+0%"，只接受"0%"或不传递参数
            if pitch_percent == 0:
                pitch_str = None
            else:
                pitch_str = f"{pitch_percent:+d}%"
            
            # 创建临时MP3文件
            temp_mp3 = output_path.replace('.wav', '.mp3')
            
            # 定义异步函数来生成语音
            async def generate_speech():
                # 构建参数字典
                kwargs = {
                    "text": text,
                    "voice": voice
                }
                if rate_str is not None:
                    kwargs["rate"] = rate_str
                if pitch_str is not None:
                    kwargs["pitch"] = pitch_str
                
                communicate = edge_tts.Communicate(**kwargs)
                await communicate.save(temp_mp3)
            
            # 运行异步函数
            asyncio.run(generate_speech())
            
            # 检查MP3文件是否生成成功
            if not os.path.exists(temp_mp3):
                logger.error(f"edge-tts failed to generate MP3 file: {temp_mp3}")
                self._generate_silent_audio(output_path, text, speed)
                return (False, output_path)
            
            # 尝试转换为WAV格式（需要ffmpeg）
            conversion_success = False
            if PYDUB_AVAILABLE:
                try:
                    audio = AudioSegment.from_mp3(temp_mp3)
                    audio.export(output_path, format="wav")
                    conversion_success = True
                    logger.info(f"Converted MP3 to WAV: {output_path}")
                    
                    # 删除临时MP3文件
                    if os.path.exists(temp_mp3):
                        os.remove(temp_mp3)
                    
                    return (True, output_path)
                except Exception as convert_error:
                    logger.warning(f"Failed to convert MP3 to WAV (ffmpeg not available?): {convert_error}")
                    conversion_success = False
            
            # 如果转换失败或pydub不可用，直接使用MP3文件
            # 检查输出路径是否以.wav结尾，如果是，改为.mp3
            if output_path.endswith('.wav'):
                actual_output_path = output_path.replace('.wav', '.mp3')
                logger.info(f"Using MP3 format instead of WAV: {actual_output_path}")
            else:
                actual_output_path = output_path
            
            # 如果临时文件和目标文件不同，移动文件
            if temp_mp3 != actual_output_path:
                # 删除已存在的目标文件
                if os.path.exists(actual_output_path):
                    os.remove(actual_output_path)
                # 重命名/移动临时文件
                os.rename(temp_mp3, actual_output_path)
            # 如果相同，不需要移动
            
            logger.info(f"Speech generated with edge-tts: {actual_output_path}")
            return (True, actual_output_path)
            
        except Exception as e:
            logger.error(f"Error generating speech with edge-tts: {str(e)}")
            import traceback
            traceback.print_exc()
            # 生成静音作为备用
            self._generate_silent_audio(output_path, text, speed)
            return (False, output_path)
    
    def _generate_silent_audio(self, output_path: str, text: str, speed: float):
        """
        生成静音音频
        
        Args:
            output_path: 输出文件路径
            text: 文本内容（用于计算音频长度）
            speed: 语速
        """
        try:
            # 计算音频长度（基于文本长度和语速）
            text_length = len(text)
            duration = max(1.0, text_length / 3.0 / speed)  # 至少1秒
            
            # 使用Python内置的wave模块生成静音WAV文件
            sample_rate = 22050
            num_channels = 1
            sample_width = 2  # 16-bit
            num_frames = int(duration * sample_rate)
            
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(num_channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.setnframes(num_frames)
                
                # 写入静音数据（所有样本为0）
                silence = b'\x00\x00' * num_frames
                wav_file.writeframes(silence)
            
            logger.info(f"Silent audio generated: {output_path} (duration: {duration:.2f}s)")
            
        except Exception as e:
            logger.error(f"Error generating silent audio: {str(e)}")
            # 创建一个非常短的静音文件作为备用
            try:
                sample_rate = 22050
                num_channels = 1
                sample_width = 2
                num_frames = sample_rate  # 1秒静音
                
                with wave.open(output_path, 'w') as wav_file:
                    wav_file.setnchannels(num_channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(sample_rate)
                    wav_file.setnframes(num_frames)
                    
                    silence = b'\x00\x00' * num_frames
                    wav_file.writeframes(silence)
            except:
                pass
    
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
    
    @staticmethod
    def get_available_voices() -> Dict[str, Dict[str, str]]:
        """
        获取可用的预设语音列表
        
        Returns:
            语音ID到语音信息的映射
        """
        return PRESET_VOICES.copy()
