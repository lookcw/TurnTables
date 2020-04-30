import speech_recognition as sr

r = sr.Recognizer()

src_file = sr.AudioFile('No google.wav')
with src_file as source:
    audio = r.record(source)
    text = r.recognize_google(audio)
    print(text)