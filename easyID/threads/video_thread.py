# This Thread Interacts with the GUI Directly

import sys
from datetime import datetime

import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage, QPixmap

from easyID.settings import ADD_TIMESTAMP
from easyID.threads.webcam_thread import WebcamThread


# this thread is used to capture frames from the webcam
class VideoThread(QThread):
    updateFrame = Signal(QPixmap, bool)

    def __init__(self, webcam_thread: WebcamThread, parent=None) -> None:
        QThread.__init__(self, parent)
        self._stop: bool = False
        self.webcam_thread: WebcamThread = webcam_thread

    def stop(self) -> None:
        self._stop = True
        self.exit()

    def run(self) -> None:
        prev_frame = None
        prev_results = None
        unknown_subjects = False
        while self.webcam_thread.cap.isOpened() and not self._stop:
            frame = self.webcam_thread.frame
            results = self.webcam_thread.results
            if frame is not None and (frame is not prev_frame or results is not prev_results):
                if ADD_TIMESTAMP:  # put timestamp on frame
                    cv2.putText(
                        img=frame,
                        text=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]),
                        org=(20, self.webcam_thread.height - 10),
                        fontFace=cv2.FONT_HERSHEY_PLAIN,
                        fontScale=1,
                        color=(255, 255, 255),
                    )
                if results:
                    for result in results:
                        cv2.rectangle(
                            img=frame,
                            pt1=(result.x_min, result.y_min),
                            pt2=(result.x_max, result.y_max),
                            color=(0, 255, 0),
                            thickness=1,
                        )
                        if result.age_low and result.age_high:
                            age = f"Age: {result.age_low} - {result.age_high}"
                            cv2.putText(
                                frame,
                                age,
                                (result.x_max, result.y_min + 15),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 255, 0),
                                1,
                            )
                        if result.sex:
                            gender = f"Sex: {result.sex}"
                            cv2.putText(
                                frame,
                                gender,
                                (result.x_max, result.y_min + 35),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 255, 0),
                                1,
                            )

                        if result.subject and result.is_matching:
                            subject = f"Subject: {result.subject}"
                            similarity = f"Similarity: {result.similarity}"
                            cv2.putText(
                                frame,
                                subject,
                                (result.x_max, result.y_min + 75),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 255, 0),
                                1,
                            )
                            cv2.putText(
                                frame,
                                similarity,
                                (result.x_max, result.y_min + 95),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 255, 0),
                                1,
                            )
                        else:
                            unknown_subjects = True
                            subject = "No known faces"
                            cv2.putText(
                                frame,
                                subject,
                                (result.x_max, result.y_min + 75),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 255, 0),
                                1,
                            )
                # send frame to pyqt
                # print("Emitting frame")
                # convert cv2 frame to QImage for Qt(GUI)
                # rgb swapped changes bgr to rgb, then we change it to a PixMap for displaying in the GUI
                gui_pixmap = QPixmap.fromImage(
                    QImage(
                        frame.data,
                        self.webcam_thread.width,
                        self.webcam_thread.height,
                        3 * self.webcam_thread.width,
                        QImage.Format_RGB888,
                    ).rgbSwapped()
                )
                self.updateFrame.emit(gui_pixmap, unknown_subjects)
                # update / reset variables
                unknown_subjects = False
                prev_frame = frame
                prev_results = results
            else:
                # print("Video Thread Sleeping for  5ms")
                self.msleep(5)  # sleep for 5 ms
        # on exit:
        print("VideoThread exited")
