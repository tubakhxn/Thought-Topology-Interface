# download_model.py
import urllib.request
import os

MODEL_URL = 'https://storage.googleapis.com/mediapipe-assets/hand_landmarker.task'
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')

def download_model():
    if not os.path.exists(MODEL_PATH):
        print('Downloading hand_landmarker.task model...')
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print('Model downloaded to', MODEL_PATH)
    else:
        print('Model already exists at', MODEL_PATH)

if __name__ == '__main__':
    download_model()
