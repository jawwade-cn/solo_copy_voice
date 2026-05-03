import sys
import os
import asyncio
import io

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing edge-tts Text-to-Speech")
print("=" * 60)

# 测试edge-tts功能
try:
    import edge_tts
    print("[OK] edge-tts imported successfully")
    
    # 测试参数
    TEXT = "你好，这是一个声音复刻智能体的测试。我正在使用微软的edge-tts进行文本转语音。"
    VOICE = "zh-CN-XiaoxiaoNeural"  # 晓晓
    OUTPUT_FILE = "test_output.mp3"
    
    print("\nGenerating speech with:")
    print(f"  - Text: {TEXT}")
    print(f"  - Voice: {VOICE}")
    print(f"  - Output: {OUTPUT_FILE}")
    
    # 定义异步函数
    async def test_tts():
        communicate = edge_tts.Communicate(TEXT, VOICE)
        await communicate.save(OUTPUT_FILE)
        print("\n[OK] Speech generated successfully!")
        
        # 检查文件是否存在
        if os.path.exists(OUTPUT_FILE):
            file_size = os.path.getsize(OUTPUT_FILE)
            print(f"  - File size: {file_size} bytes")
            print(f"  - File path: {os.path.abspath(OUTPUT_FILE)}")
            return True
        else:
            print("[ERROR] Output file not found")
            return False
    
    # 运行异步函数
    success = asyncio.run(test_tts())
    
    if success:
        print("\n" + "=" * 60)
        print("Test PASSED! edge-tts is working correctly.")
        print("=" * 60)
        print("\nNotes:")
        print("- You can play the generated audio file with any media player.")
        print("- This uses Microsoft's edge-tts service (requires internet).")
        print("- Voice cloning requires Python 3.11 or 3.12 with Coqui TTS.")
    else:
        print("\n" + "=" * 60)
        print("Test FAILED!")
        print("=" * 60)
        sys.exit(1)
        
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
