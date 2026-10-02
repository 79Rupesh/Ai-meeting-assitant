"""Authorized continuous microphone input provider for the desktop companion."""

import threading
from abc import ABC, abstractmethod

import speech_recognition as sr


class MeetingInputProvider(ABC):

    @abstractmethod
    def start(self):
        """Start authorized input without blocking the UI."""

    @abstractmethod
    def stop(self):
        """Stop authorized input."""


class MicrophoneSpeechProvider(MeetingInputProvider):

    def __init__(self, on_text, on_status):

        self.on_text = on_text
        self.on_status = on_status

        self.recognizer = sr.Recognizer()

        # Speech detection settings
        self.recognizer.pause_threshold = 1.5
        self.recognizer.non_speaking_duration = 0.8

        # Keep microphone energy adaptive
        self.recognizer.dynamic_energy_threshold = True

        # Prevent duplicate microphone sessions
        self._lock = threading.Lock()

        # Used to stop continuous listening
        self._stop_event = threading.Event()

        # Ambient noise calibration only once
        self._calibrated = False

    # ==================================================
    # START
    # ==================================================

    def start(self):

        if not self._lock.acquire(blocking=False):

            return {
                "started": False,
                "message": "Already listening."
            }

        self._stop_event.clear()

        thread = threading.Thread(
            target=self._listen_continuously,
            daemon=True,
            name="meeting-speech-input"
        )

        thread.start()

        return {
            "started": True,
            "message": "Listening..."
        }

    # ==================================================
    # STOP
    # ==================================================

    def stop(self):

        if not self._stop_event.is_set():

            self._stop_event.set()

            return {
                "stopped": True,
                "message": "Stopping microphone..."
            }

        return {
            "stopped": True,
            "message": "Microphone already stopped."
        }

    # ==================================================
    # CONTINUOUS LISTENING
    # ==================================================

    def _listen_continuously(self):

        try:

            self.on_status(
                "listening",
                "Listening continuously… speak normally."
            )

            with sr.Microphone() as source:

                print("🎤 Microphone started")

                # ------------------------------------------
                # Ambient noise calibration
                # ------------------------------------------

                if not self._calibrated:

                    print("Calibrating microphone...")

                    self.recognizer.adjust_for_ambient_noise(
                        source,
                        duration=0.5
                    )

                    self._calibrated = True

                    print("Microphone calibrated")

                print("🎤 Continuous listening started")

                # ------------------------------------------
                # CONTINUOUS LOOP
                # ------------------------------------------

                while not self._stop_event.is_set():

                    try:

                        print("Listening for speech...")

                        audio = self.recognizer.listen(
                            source,
                            timeout=3,
                            phrase_time_limit=20
                        )

                        if self._stop_event.is_set():
                            break

                        self.on_status(
                            "processing",
                            "Converting speech to text…"
                        )

                        print("Processing speech...")

                        text = self.recognizer.recognize_google(
                            audio,
                            language="en-IN"
                        ).strip()

                        if text:

                            print(
                                "Recognized:",
                                text
                            )

                            # Send every recognized chunk
                            self.on_text(text)

                            self.on_status(
                                "listening",
                                "Listening continuously…"
                            )

                    except sr.WaitTimeoutError:

                        # No speech for a short period.
                        # Continue listening instead of stopping.
                        continue

                    except sr.UnknownValueError:

                        print(
                            "Could not understand this speech chunk."
                        )

                        self.on_status(
                            "listening",
                            "Listening…"
                        )

                        # Continue listening
                        continue

                    except sr.RequestError as error:

                        print(
                            f"Speech recognition service error: {error}"
                        )

                        self.on_status(
                            "idle",
                            "Speech service is temporarily unavailable."
                        )

                        break

                    except Exception as error:

                        print(
                            f"Speech processing error: {error}"
                        )

                        self.on_status(
                            "listening",
                            "Listening…"
                        )

                        continue

        except Exception as error:

            print(
                f"Microphone error: {error}"
            )

            self.on_status(
                "idle",
                "Microphone is unavailable. Check its permissions."
            )

        finally:

            self._stop_event.set()

            self._lock.release()

            print("🎤 Continuous microphone stopped")

            self.on_status(
                "idle",
                "Microphone stopped."
            )