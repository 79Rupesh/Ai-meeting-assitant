import speech_recognition as sr

recognizer = sr.Recognizer()

print("Microphone test started...")
print("Speak something...")

with sr.Microphone() as source:

    recognizer.adjust_for_ambient_noise(
        source,
        duration=1
    )

    print("Listening...")

    audio = recognizer.listen(source)

print("Processing speech...")

try:

    text = recognizer.recognize_google(audio)

    print("You said:")
    print(text)

except sr.UnknownValueError:

    print("Could not understand the speech.")

except sr.RequestError as error:

    print("Speech service error:")
    print(error)