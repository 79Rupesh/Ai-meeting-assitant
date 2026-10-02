import json
import webview
from speech_input import MicrophoneSpeechProvider

class API:
    def __init__(self):
        self.speech = MicrophoneSpeechProvider(self._send_text, self._set_status)

    def _call_page(self, function, *args):
        if webview.windows:
            values = ", ".join(json.dumps(arg) for arg in args)
            webview.windows[0].evaluate_js(f"window.{function}({values})")

    def _send_text(self, text):
        self._call_page("receiveSpeechTranscript", text)

    def _set_status(self, state, message):
        self._call_page("setSpeechStatus", state, message)

    def start_speaking(self):
        return self.speech.start()

    def stop_speaking(self):
        return self.speech.stop()

    def close_app(self):
        if webview.windows:
            webview.windows[0].destroy()
        return "Application closed"

api = API()
window = webview.create_window(
    title="AI Meeting Companion",
    url="http://127.0.0.1:8000/frontend/meeting.html",
    js_api=api,

    # Compact Gemini-style window
    width=470,
    height=620,

    # Prevent layout from becoming smaller
    min_size=(450, 580),

    # Fixed compact size
    resizable=False,

    # Keep companion above other windows
    on_top=True,
)
webview.start(debug=True)
