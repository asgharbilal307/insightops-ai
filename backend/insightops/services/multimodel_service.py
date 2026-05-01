from transformers import pipeline
from PIL import Image
import librosa
import numpy as np

image_classifier = pipeline(
    "image-classification",
    model="google/vit-base-patch16-224"
)


def analyze_image(image_path: str):

    image = Image.open(image_path)

    result = image_classifier(image)

    top_result = result[0]

    return {
        "label": top_result["label"],
        "confidence": round(top_result["score"], 3)
    }


audio_transcriber = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-base"
)


def transcribe_audio(audio_path: str):

    result = audio_transcriber(audio_path)

    return result["text"]

def detect_audio_emotion(audio_path: str):

    y, sr = librosa.load(audio_path)

    energy = np.mean(np.abs(y))

    if energy > 0.05:
        return "HIGH_URGENCY"

    elif energy > 0.02:
        return "MEDIUM_URGENCY"

    return "LOW_URGENCY"



def multimodal_analysis(
    text=None,
    image_path=None,
    audio_path=None
):

    result = {}

    if text:
        result["text"] = text

    if image_path:
        result["image_analysis"] = analyze_image(image_path)

    # AUDIO
    if audio_path:

        transcription = transcribe_audio(audio_path)

        emotion = detect_audio_emotion(audio_path)

        result["audio_analysis"] = {
            "transcription": transcription,
            "emotion": emotion
        }

    return result