# temporary Settings / Constants
from pathlib import Path

UNIDENTIFIED_SUBJECTS_TIMEOUT = 5  # seconds
SIMILARITY_THRESHOLD = 0.8  # 80% similarity
NUMBER_OF_SUBJECTS = 5  # number of subjects to be recognized
DETECTION_PROBABILITY_THRESHOLD = 0.95  # 95% probability of a face
DEFAULT_DIRECTORY = Path.home() / "easyID"
# config options
CF_OPTIONS = {
    "limit": NUMBER_OF_SUBJECTS,
    "det_prob_threshold": DETECTION_PROBABILITY_THRESHOLD,
    "prediction_count": 1,
    # "face_plugins": "",  # if you want age and gender, add "age,gender" to this list.
    "status": False,
}

WEBCAM_ID = 0
WEBCAM_WIDTH = 960
WEBCAM_HEIGHT = 720

DEFAULT_HOST = "https://easyid-server.local"
DEFAULT_PORT = "443"
API_KEY = "9886bc85-44dc-4345-8e61-3b39a2a2dc42"
# SELF_SIGNED_CERT_DIR = None # Default off
SELF_SIGNED_CERT_DIR = Path("../easyID-server/main-nginx/nginx-selfsigned.crt")
ADD_TIMESTAMP = True
MUTE_ALERTS = False
