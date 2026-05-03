import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging

from .config import settings
from .voice_cloner import VoiceCloner

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="声音复刻智能体",
    description="一个可以复刻声音并用于文本朗读的智能体",
    version="1.0.0"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

# 初始化声音复刻器
voice_cloner = VoiceCloner(settings.model_dir, settings.output_dir)

# 定义请求模型
class TextToSpeechRequest(BaseModel):
    text: str
    speaker_id: str
    language: str = "zh"
    speed: float = 1.0
    pitch: float = 0.0
    emotion: str = "neutral"


# 根路由，返回主页
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回主页"""
    index_path = settings.static_dir / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>声音复刻智能体</h1><p>请创建index.html文件</p>")


# 上传音频文件并克隆声音
@app.post("/api/clone-voice")
async def clone_voice(
    file: UploadFile = File(...),
    speaker_name: Optional[str] = Form(None)
):
    """
    上传音频文件并克隆声音
    
    Args:
        file: 音频文件
        speaker_name: 说话人名称（可选）
    
    Returns:
        克隆结果
    """
    try:
        # 检查文件类型
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持的格式: {', '.join(settings.allowed_extensions)}"
            )
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        save_filename = f"{file_id}{file_ext}"
        save_path = settings.upload_dir / save_filename
        
        # 保存上传的文件
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"文件已保存: {save_path}")
        
        # 克隆声音
        result = voice_cloner.clone_voice(str(save_path), speaker_name)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "speaker_id": result["speaker_id"],
                    "message": "声音克隆成功",
                    "original_file": file.filename
                }
            )
        else:
            # 删除保存的文件
            if save_path.exists():
                save_path.unlink()
            
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"克隆声音时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"克隆声音时出错: {str(e)}"
        )


# 使用克隆的声音进行文本转语音
@app.post("/api/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """
    使用克隆的声音进行文本转语音
    
    Args:
        request: 文本转语音请求
    
    Returns:
        生成的音频文件
    """
    try:
        # 验证参数
        if not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="文本不能为空"
            )
        
        if not request.speaker_id:
            raise HTTPException(
                status_code=400,
                detail="说话人ID不能为空"
            )
        
        # 检查语速范围
        if request.speed < 0.5 or request.speed > 2.0:
            raise HTTPException(
                status_code=400,
                detail="语速范围应为0.5到2.0"
            )
        
        # 检查音调范围
        if request.pitch < -12 or request.pitch > 12:
            raise HTTPException(
                status_code=400,
                detail="音调范围应为-12到12（半音数）"
            )
        
        # 生成语音
        result = voice_cloner.text_to_speech(
            text=request.text,
            speaker_id=request.speaker_id,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            emotion=request.emotion
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "filename": result["filename"],
                    "download_url": f"/api/download/{result['filename']}",
                    "message": "语音生成成功"
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成语音时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"生成语音时出错: {str(e)}"
        )


# 下载生成的音频文件
@app.get("/api/download/{filename}")
async def download_audio(filename: str):
    """
    下载生成的音频文件
    
    Args:
        filename: 文件名
    
    Returns:
        音频文件
    """
    try:
        file_path = settings.output_dir / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        return FileResponse(
            path=str(file_path),
            media_type="audio/wav",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"下载文件时出错: {str(e)}"
        )


# 获取所有已克隆的说话人
@app.get("/api/speakers")
async def list_speakers():
    """
    获取所有已克隆的说话人
    
    Returns:
        说话人列表
    """
    try:
        speakers = voice_cloner.list_speakers()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "speakers": speakers,
                "count": len(speakers)
            }
        )
    except Exception as e:
        logger.error(f"获取说话人列表时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取说话人列表时出错: {str(e)}"
        )


# 删除指定的说话人
@app.delete("/api/speakers/{speaker_id}")
async def delete_speaker(speaker_id: str):
    """
    删除指定的说话人
    
    Args:
        speaker_id: 说话人ID
    
    Returns:
        删除结果
    """
    try:
        if voice_cloner.delete_speaker(speaker_id):
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": f"说话人 {speaker_id} 已删除"
                }
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"说话人 {speaker_id} 不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除说话人时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除说话人时出错: {str(e)}"
        )


# 健康检查
@app.get("/api/health")
async def health_check():
    """
    健康检查接口
    
    Returns:
        服务状态
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": "1.0.0",
            "message": "声音复刻智能体服务运行正常"
        }
    )


# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
