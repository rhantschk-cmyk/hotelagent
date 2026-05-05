"""HotelAgent — Voice: Spracheingabe (STT) und Sprachausgabe (TTS)."""

import io
import tempfile
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
import pyttsx3

from scripts.config_manager import get_llm_config

# Aufnahme-Parameter
SAMPLE_RATE = 16000
CHANNELS = 1


class VoiceRecorder:
    """Mikrofon-Aufnahme mit Push-to-Talk (Enter)."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._recording = False
        self._frames: list[np.ndarray] = []

    def record_until_enter(self) -> np.ndarray | None:
        """Aufnahme starten und bei Enter stoppen. Gibt Audio-Array zurueck."""
        self._frames = []
        self._recording = True

        def callback(indata, frames, time_info, status):
            if self._recording:
                self._frames.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=CHANNELS,
                dtype="float32",
                callback=callback,
            ):
                input()  # Warten auf Enter
                self._recording = False
        except sd.PortAudioError as e:
            self._recording = False
            raise RuntimeError(f"Audio-Fehler: {e}")

        if not self._frames:
            return None

        return np.concatenate(self._frames, axis=0)

    def save_to_file(self, audio: np.ndarray, path: str | Path) -> Path:
        """Audio-Array als WAV-Datei speichern."""
        path = Path(path)
        sf.write(str(path), audio, self.sample_rate)
        return path


class SpeechToText:
    """Sprache-zu-Text via Google Speech Recognition (kostenlos, kein API-Key noetig)."""

    def __init__(self):
        import speech_recognition as sr
        self.recognizer = sr.Recognizer()

    def transcribe(self, audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
        """Audio-Array transkribieren."""
        import speech_recognition as sr

        # float32 -> int16 konvertieren fuer SpeechRecognition
        audio_int16 = (audio.flatten() * 32767).astype(np.int16)
        audio_data = sr.AudioData(audio_int16.tobytes(), sample_rate, 2)

        return self.recognizer.recognize_google(audio_data, language="de-DE")


class TextToSpeech:
    """Text-zu-Sprache via pyttsx3 (offline)."""

    def __init__(self):
        self._engine = pyttsx3.init()
        # Stimme und Geschwindigkeit konfigurieren
        self._engine.setProperty("rate", 175)
        voices = self._engine.getProperty("voices")
        # Deutsche Stimme suchen falls vorhanden
        for voice in voices:
            if "german" in voice.name.lower() or "de" in voice.id.lower():
                self._engine.setProperty("voice", voice.id)
                break

    def speak(self, text: str) -> None:
        """Text vorlesen."""
        self._engine.say(text)
        self._engine.runAndWait()

    def speak_async(self, text: str) -> threading.Thread:
        """Text asynchron vorlesen."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()
        return thread


def get_microphone_info() -> dict | None:
    """Info ueber Standard-Mikrofon zurueckgeben."""
    try:
        info = sd.query_devices(kind="input")
        return {
            "name": info["name"],
            "channels": info["max_input_channels"],
            "sample_rate": info["default_samplerate"],
        }
    except Exception:
        return None


def test_tts() -> bool:
    """TTS-Engine testen."""
    try:
        engine = pyttsx3.init()
        engine.stop()
        return True
    except Exception:
        return False
