# temporary Settings / Constants
from pathlib import Path

FPS_LIMIT = 1 / 60  # 60 fps
UNIDENTIFIED_SUBJECTS_TIMEOUT = 5  # seconds
SIMILARITY_THRESHOLD = 0.6  # 60% similarity
NUMBER_OF_SUBJECTS = 2  # number of subjects to be recognized

# config options
WEBCAM_ID = 0
DEFAULT_HOST = "https://localhost"
DEFAULT_PORT = "443"
API_KEY = "00000000-0000-0000-0000-000000000002"
SELF_SIGNED_CERT_DIR = None  # Default off
# SELF_SIGNED_CERT_DIR = Path("../easyID-server/main-nginx/nginx-selfsigned.crt")
ADD_TIMESTAMP = True
MUTE_ALERTS = False
