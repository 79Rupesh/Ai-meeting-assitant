import threading
import time

import numpy as np
import sounddevice as sd
import speech_recognition as sr


class SystemAudioSpeechProvider:
    def __init__(self, on_text, on_status):
        self.on_text = on_text
        self.on_status = on_status

        self.device = 17
        self.sample_rate = 48000
        self.chunk_seconds = 1

        self.recognizer = sr.Recognizer()

        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self):
        if not self._lock.acquire(blocking=False):
            return {
                "started": False,
                "message": "System audio already running."
            }

        self._stop_event.clear()

        thread = threading.Thread(
            target=self._listen,
            daemon=True,
            name="system-audio-input"
        )

        thread.start()

        return {
            "started": True,
            "message": "System audio listening..."
        }

    def stop(self):
        self._stop_event.set()

        return {
            "stopped": True,
            "message": "System audio stopping..."
        }

    def _listen(self):
        try:
            self.on_status(
                "listening",
                "Meeting audio listening..."
            )

            print("🎧 System audio started")

            while not self._stop_event.is_set():

                print("System audio chunk...")

                audio_data = sd.rec(
                    int(self.sample_rate * self.chunk_seconds),
                    samplerate=self.sample_rate,
                    channels=2,
                    dtype="float32",
                    device=self.device
                )

                sd.wait()

                if self._stop_event.is_set():
                    break

                # Stereo → Mono
                if audio_data.ndim > 1:
                    audio_data = np.mean(
                        audio_data,
                        axis=1
                    )

                # Check whether audio exists
                volume = np.max(
                    np.abs(audio_data)
                )

                if volume < 0.01:
                    continue

                audio_data = np.clip(
                    audio_data,
                    -1,
                    1
                )

                audio_data = (
                    audio_data * 32767
                ).astype(np.int16)

                audio = sr.AudioData(
                    audio_data.tobytes(),
                    self.sample_rate,
                    2
                )

                try:
                    text = self.recognizer.recognize_google(
                        audio,
                        language="en-IN"
                    ).strip()

                    if text:
                        print("🎧 Meeting:", text)
                        self.on_text(text)

                except sr.UnknownValueError:
                    pass

                except sr.RequestError as error:
                    print(
                        "Speech service error:",
                        error
                    )

                    self.on_status(
                        "idle",
                        "Speech service unavailable."
                    )

                    time.sleep(2)

        except Exception as error:
            print(
                "System audio error:",
                error
            )

            self.on_status(
                "idle",
                "System audio unavailable."
            )

        finally:
            self._stop_event.set()

            try:
                self._lock.release()
            except RuntimeError:
                pass

            print("🎧 System audio stopped")

            self.on_status(
                "idle",
                "System audio stopped."
            )