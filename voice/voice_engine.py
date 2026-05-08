# voice/voice_engine.py
import asyncio
import os
import random
import threading

import edge_tts
import pygame
import speech_recognition as sr

from core.services.logging_service import get_logger
from utils.ws_server import ws_server

logger = get_logger("zeno.voice")

class VoiceEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize pygame for audio playback
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        self.temp_audio_file = os.path.abspath("temp_voice.mp3")
        self.voice = "en-IN-PrabhatNeural" # Indian Male for Zeno
        self.is_speaking = False
        self.is_listening = False # Lock for microphone context
        self.mic_lock = threading.Lock() # Prevent concurrent mic access

    def listen(self):
        """
        Listens to the user via microphone and returns text.
        """
        with self.mic_lock:
            if self.is_listening:
                logger.warning("Mic already in use.")
                return None
            
            try:
                self.is_listening = True
                with self.microphone as source:
                    logger.info("Listening...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = self.recognizer.recognize_google(audio)  # type: ignore[attr-defined]
                    logger.info("User said: %s", text)
                    return text
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                logger.warning("STT: Could not understand audio")
                return None
            except Exception:
                logger.exception("STT Error")
                return None
            finally:
                self.is_listening = False

    async def _broadcast_amplitude(self):
        """Simulates and broadcasts voice amplitude for lip-sync."""
        try:
            logger.debug("Amplitude broadcast loop started")
            while self.is_speaking and pygame.mixer.music.get_busy():
                amp = random.uniform(0.3, 1.0) if random.random() > 0.1 else 0.1
                ws_server.broadcast({"type": "amplitude", "value": amp})
                await asyncio.sleep(0.05)  # 20fps amplitude updates
        except Exception:
            logger.exception("Amplitude broadcast loop crashed")
        finally:
            # Reset amplitude when done / error
            try:
                ws_server.broadcast({"type": "amplitude", "value": 0})
            except Exception:
                logger.exception("Amplitude reset failed")
            logger.debug("Amplitude broadcast loop stopped (amplitude reset sent)")

    async def speak_async(self, text):
        """
        Converts text to speech using edge-tts and plays it with visual sync.
        """
        if not text:
            return

        self.stop()  # Interrupt previous speech
        self.is_speaking = True

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(self.temp_audio_file)
        
        # Play using pygame
        if os.path.exists(self.temp_audio_file):
            try:
                pygame.mixer.music.load(self.temp_audio_file)
                pygame.mixer.music.play()
                
                # Start amplitude broadcasting in background
                asyncio.create_task(self._broadcast_amplitude())
                
                while pygame.mixer.music.get_busy() and self.is_speaking:
                    await asyncio.sleep(0.1)

            except Exception:
                logger.exception("Playback Error")
            finally:
                self.is_speaking = False
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass
                if os.path.exists(self.temp_audio_file):
                    try:
                        os.remove(self.temp_audio_file)
                    except Exception:
                        pass
        else:
            logger.warning("Voice skipped (no audio generated)")

    def stop(self):
        """Kills any current vocalization immediately."""
        self.is_speaking = False
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        return True

    def speak(self, text):
        """Synchronous wrapper for speak_async."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.speak_async(text))
        except Exception:
            logger.exception("Voice Error")

    def speak_threaded(self, text):
        """Runs TTS in a separate thread to avoid blocking UI."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()
        return thread

    def verify_vocal_signature(self):
        """Jarvis-style Voice Biometric verification (Phrase-based)."""
        self.speak("Commander, please provide your vocal signature to authorize this operation.")
        
        # Listening for the specific passphrase
        phrase = self.listen()
        if not phrase:
            return False
            
        expected = "zeno override alpha seven" # Security Bypass Phrase
        if phrase and expected in phrase.lower():
            self.speak("Vocal signature confirmed. Identity verified.")
            return True
        else:
            self.speak("Voice print mismatch. Operation aborted.")
            return False
