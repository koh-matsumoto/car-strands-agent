"""
ElevenLabs テキスト読み上げ（TTS）モジュール。
TTS_ENABLED=false で無効化できる。
"""

import os
from dotenv import load_dotenv

load_dotenv()


def generate_audio(text: str) -> bytes | None:
    """テキストをElevenLabsで音声合成してバイト列を返す（再生しない）。"""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return None
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings

        client = ElevenLabs(api_key=api_key)
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
        model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_v3")
        output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")
        speed = float(os.getenv("ELEVENLABS_SPEED", "1.0"))

        chunks = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format=output_format,
            voice_settings=VoiceSettings(speed=speed),
        )
        return b"".join(chunks)
    except Exception as e:
        print(f"[TTS Error] {e}")
        return None


def speak(text: str) -> None:
    """テキストをElevenLabsで音声合成して再生する。"""
    if os.getenv("TTS_ENABLED", "true").lower() == "false":
        return

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return

    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs.play import play
        from elevenlabs import VoiceSettings

        client = ElevenLabs(api_key=api_key)
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
        model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_v3")
        output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")
        speed = float(os.getenv("ELEVENLABS_SPEED", "1.0"))

        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format=output_format,
            voice_settings=VoiceSettings(speed=speed),
        )
        play(audio)
    except Exception as e:
        print(f"[TTS Error] {e}")
