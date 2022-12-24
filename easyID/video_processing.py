# this thread contacts the CompreFace server and actually does the face recognition
from typing import Any, List

import cv2
from PySide6.QtCore import QThread
from compreface import CompreFace
from compreface.service import RecognitionService

from easyID.common_classes import process_rec_results
from easyID.webcam_thread import VideoThread

class ProcessingThread(QThread):

    def __init__(self, video_thread: VideoThread, args: Any, parent=None):
        QThread.__init__(self, parent)
        self.video_thread: VideoThread = video_thread

        self.compre_face: CompreFace = CompreFace(args.host, args.port, {
            "limit": 2,
            "det_prob_threshold": 0.8,
            "prediction_count": 1,
            "face_plugins": "age,gender",
            "status": False
        })
        self.recognition: RecognitionService = self.compre_face.init_face_recognition(args.api_key)

    def run(self):
        while self.video_thread.cap.isOpened():
            if self.video_thread.frame is not None:
                _, im_buf_arr = cv2.imencode(".jpg", self.video_thread.frame)
                byte_im = im_buf_arr.tobytes()
                data = self.recognition.recognize(byte_im)
                self.video_thread.results = process_rec_results(data.get('result'))
