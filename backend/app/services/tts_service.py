"""
간단한 TTS 서비스: gTTS를 사용해 음성 파일 생성
컨테이너 내에서는 파일로 저장하고 로그에 경로만 출력합니다.
"""

from gtts import gTTS
from datetime import datetime
from pathlib import Path
from loguru import logger


class TTSService:
    def __init__(self, output_dir: str = "logs/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def speak(self, text: str) -> str:
        try:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_path = self.output_dir / f"tts_{ts}.mp3"
            tts = gTTS(text=text, lang="ko")
            tts.save(str(file_path))
            logger.info(f"TTS 파일 생성: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"TTS 생성 실패: {e}")
            return ""


tts_service = TTSService()


