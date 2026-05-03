import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("Testing imports...")
print("=" * 50)

# 测试voice_cloner模块
try:
    from app.voice_cloner import (
        VoiceCloner, 
        TTS_AVAILABLE, 
        EDGE_TTS_AVAILABLE, 
        LIBROSA_AVAILABLE, 
        PYDUB_AVAILABLE,
        PRESET_VOICES
    )
    print("✓ app.voice_cloner imported successfully")
    print(f"  - TTS_AVAILABLE: {TTS_AVAILABLE}")
    print(f"  - EDGE_TTS_AVAILABLE: {EDGE_TTS_AVAILABLE}")
    print(f"  - LIBROSA_AVAILABLE: {LIBROSA_AVAILABLE}")
    print(f"  - PYDUB_AVAILABLE: {PYDUB_AVAILABLE}")
    print(f"  - PRESET_VOICES: {len(PRESET_VOICES)} voices available")
except Exception as e:
    print(f"✗ Failed to import app.voice_cloner: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试main模块
try:
    from app.main import app
    print("✓ app.main imported successfully")
    print(f"  - FastAPI app title: {app.title}")
except Exception as e:
    print(f"✗ Failed to import app.main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("All imports successful!")
print("=" * 50)

# 测试edge-tts功能
if EDGE_TTS_AVAILABLE:
    print("\nTesting edge-tts...")
    try:
        import edge_tts
        print("✓ edge-tts is available")
        
        # 列出可用的中文语音
        print("\nAvailable Chinese voices:")
        for voice_id, voice_info in PRESET_VOICES.items():
            print(f"  - {voice_id}: {voice_info['name']} ({voice_info['gender']}, {voice_info['language']})")
            
    except Exception as e:
        print(f"✗ Failed to test edge-tts: {e}")

print("\n" + "=" * 50)
print("Test completed successfully!")
print("=" * 50)
