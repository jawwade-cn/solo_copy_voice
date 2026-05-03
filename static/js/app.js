// DOM 元素
const audioFileInput = document.getElementById('audio-file');
const speakerNameInput = document.getElementById('speaker-name');
const cloneBtn = document.getElementById('clone-btn');
const cloneResult = document.getElementById('clone-result');

const speakerSelect = document.getElementById('speaker-select');
const refreshSpeakersBtn = document.getElementById('refresh-speakers-btn');
const speakersList = document.getElementById('speakers-list');

const textInput = document.getElementById('text-input');
const languageSelect = document.getElementById('language');
const speedInput = document.getElementById('speed');
const speedValue = document.getElementById('speed-value');
const pitchInput = document.getElementById('pitch');
const pitchValue = document.getElementById('pitch-value');
const emotionSelect = document.getElementById('emotion');
const ttsBtn = document.getElementById('tts-btn');
const ttsResult = document.getElementById('tts-result');

const audioSection = document.getElementById('audio-section');
const audioPlayer = document.getElementById('audio-player');
const downloadLink = document.getElementById('download-link');

const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text');

// API 基础 URL
const API_BASE = '';

// 显示加载状态
function showLoading(text = '处理中...') {
    loadingText.textContent = text;
    loadingOverlay.style.display = 'flex';
}

// 隐藏加载状态
function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// 显示结果消息
function showResult(element, message, isSuccess = true) {
    element.textContent = message;
    element.className = `result ${isSuccess ? 'success' : 'error'}`;
    element.style.display = 'block';
}

// 隐藏结果消息
function hideResult(element) {
    element.style.display = 'none';
}

// 更新语速显示
speedInput.addEventListener('input', function() {
    speedValue.textContent = this.value;
});

// 更新音调显示
pitchInput.addEventListener('input', function() {
    pitchValue.textContent = this.value;
});

// 克隆声音
cloneBtn.addEventListener('click', async function() {
    const file = audioFileInput.files[0];
    const speakerName = speakerNameInput.value.trim();
    
    if (!file) {
        showResult(cloneResult, '请选择一个音频文件', false);
        return;
    }
    
    // 检查文件类型
    const allowedTypes = ['.wav', '.mp3', '.m4a', '.flac', '.ogg'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        showResult(cloneResult, '不支持的文件格式。支持的格式：WAV, MP3, M4A, FLAC, OGG', false);
        return;
    }
    
    hideResult(cloneResult);
    showLoading('正在克隆声音，请稍候...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        if (speakerName) {
            formData.append('speaker_name', speakerName);
        }
        
        const response = await fetch(`${API_BASE}/api/clone-voice`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showResult(cloneResult, `声音克隆成功！说话人ID: ${result.speaker_id}`, true);
            // 刷新说话人列表
            await refreshSpeakers();
        } else {
            showResult(cloneResult, result.detail || '克隆声音失败', false);
        }
    } catch (error) {
        console.error('克隆声音时出错:', error);
        showResult(cloneResult, '克隆声音时发生错误: ' + error.message, false);
    } finally {
        hideLoading();
    }
});

// 刷新说话人列表
async function refreshSpeakers() {
    try {
        const response = await fetch(`${API_BASE}/api/speakers`);
        const result = await response.json();
        
        if (response.ok) {
            // 更新下拉选择框
            speakerSelect.innerHTML = '';
            speakersList.innerHTML = '';
            
            if (result.count > 0) {
                // 添加默认选项
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = '-- 请选择一个说话人 --';
                speakerSelect.appendChild(defaultOption);
                
                // 添加说话人选项
                for (const [speakerId, audioPath] of Object.entries(result.speakers)) {
                    const option = document.createElement('option');
                    option.value = speakerId;
                    option.textContent = speakerId;
                    speakerSelect.appendChild(option);
                    
                    // 添加到列表显示
                    const speakerItem = document.createElement('div');
                    speakerItem.className = 'speaker-item';
                    speakerItem.innerHTML = `
                        <h4>${speakerId}</h4>
                        <p>音频路径: ${audioPath}</p>
                        <button class="btn btn-secondary delete-speaker-btn" data-id="${speakerId}">删除</button>
                    `;
                    speakersList.appendChild(speakerItem);
                }
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = '-- 请先克隆声音 --';
                speakerSelect.appendChild(option);
            }
        } else {
            console.error('获取说话人列表失败:', result);
        }
    } catch (error) {
        console.error('获取说话人列表时出错:', error);
    }
}

// 刷新说话人按钮事件
refreshSpeakersBtn.addEventListener('click', refreshSpeakers);

// 删除说话人事件委托
speakersList.addEventListener('click', async function(e) {
    if (e.target.classList.contains('delete-speaker-btn')) {
        const speakerId = e.target.dataset.id;
        if (confirm(`确定要删除说话人 "${speakerId}" 吗？`)) {
            try {
                const response = await fetch(`${API_BASE}/api/speakers/${speakerId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    await refreshSpeakers();
                } else {
                    const result = await response.json();
                    alert('删除失败: ' + (result.detail || '未知错误'));
                }
            } catch (error) {
                console.error('删除说话人时出错:', error);
                alert('删除时发生错误: ' + error.message);
            }
        }
    }
});

// 文本转语音
ttsBtn.addEventListener('click', async function() {
    const text = textInput.value.trim();
    const speakerId = speakerSelect.value;
    const language = languageSelect.value;
    const speed = parseFloat(speedInput.value);
    const pitch = parseFloat(pitchInput.value);
    const emotion = emotionSelect.value;
    
    if (!text) {
        showResult(ttsResult, '请输入要朗读的文本', false);
        return;
    }
    
    if (!speakerId) {
        showResult(ttsResult, '请选择一个说话人', false);
        return;
    }
    
    hideResult(ttsResult);
    showLoading('正在生成语音，请稍候...');
    
    try {
        const response = await fetch(`${API_BASE}/api/text-to-speech`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                speaker_id: speakerId,
                language: language,
                speed: speed,
                pitch: pitch,
                emotion: emotion
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showResult(ttsResult, '语音生成成功！', true);
            
            // 设置音频播放器
            audioPlayer.src = result.download_url;
            downloadLink.href = result.download_url;
            downloadLink.download = result.filename;
            
            // 显示音频部分
            audioSection.style.display = 'block';
            
            // 自动播放
            audioPlayer.play().catch(e => console.log('自动播放被阻止:', e));
        } else {
            showResult(ttsResult, result.detail || '生成语音失败', false);
        }
    } catch (error) {
        console.error('生成语音时出错:', error);
        showResult(ttsResult, '生成语音时发生错误: ' + error.message, false);
    } finally {
        hideLoading();
    }
});

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', async function() {
    // 刷新说话人列表
    await refreshSpeakers();
    
    // 检查服务是否可用
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        if (response.ok) {
            console.log('服务运行正常');
        }
    } catch (error) {
        console.warn('无法连接到服务:', error);
    }
});
