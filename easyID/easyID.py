import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication, QIcon, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from easyID.settings import (
    API_KEY,
    DEFAULT_DIRECTORY,
    DEFAULT_HOST,
    DEFAULT_PORT,
    MUTE_ALERTS,
    SELF_SIGNED_CERT_DIR,
    UNIDENTIFIED_SUBJECTS_TIMEOUT,
    WEBCAM_HEIGHT,
    WEBCAM_ID,
    WEBCAM_WIDTH,
)
from easyID.threads.logging_thread import LoggingThread
from easyID.threads.recognition_thread import RecognitionThread
from easyID.threads.video_thread import VideoThread
from easyID.threads.webcam_thread import WebcamThread


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--api-key",
        help="CompreFace recognition service API key",
        type=str,
        default=API_KEY,
    )
    parser.add_argument("--host", help="CompreFace host", type=str, default=DEFAULT_HOST)
    parser.add_argument("--port", help="CompreFace port", type=str, default=DEFAULT_PORT)

    args = parser.parse_args()

    return args


# Image View Widget (On new image tabs)
class ImageView(QWidget):
    def __init__(self, index: int, parent: QTabWidget, preview_pixmap: QPixmap, file_name: str) -> None:
        super().__init__()

        self._index = index
        self._parent = parent
        self._file_name = file_name

        main_layout = QVBoxLayout(self)
        self._image_label = QLabel()
        self._image_label.setPixmap(preview_pixmap)
        main_layout.addWidget(self._image_label)

        top_layout = QHBoxLayout()
        self._file_name_label = QLabel(file_name)
        self._file_name_label.setTextInteractionFlags(Qt.TextBrowserInteraction)

        top_layout.addWidget(self._file_name_label)
        top_layout.addStretch()
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setToolTip("Delete this image")
        top_layout.addWidget(delete_button)
        delete_button.clicked.connect(self.delete)
        # Copy button
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self.copy)
        copy_button.setToolTip("Copy file name to clipboard")
        top_layout.addWidget(copy_button)
        copy_button.clicked.connect(self.copy)
        # Launch button
        launch_button = QPushButton("Launch")
        launch_button.setToolTip("Launch image viewer")
        top_layout.addWidget(launch_button)
        launch_button.clicked.connect(self.launch)
        main_layout.addLayout(top_layout)

    # These are for the buttons
    @Slot()
    def delete(self) -> None:
        os.remove(self._file_name)
        self._parent.removeTab(self._index)

    @Slot()
    def copy(self) -> None:
        QGuiApplication.clipboard().setText(self._file_name_label.text())

    @Slot()
    def launch(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(self._file_name))


# this is the main gui window
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # window objects
        self.last_unidentified_time: int = 0  # gap between last unidentified subject and current time to avoid spam
        self._video_pixmap: QPixmap = QPixmap()
        self._tab_widget: QTabWidget = QTabWidget(self)
        self._camera_viewfinder: QLabel = QLabel(self)

        # unidentified alerts & audio ( use default device )
        self._unidentified_person_audio: QMediaPlayer = QMediaPlayer(self)
        self._unidentified_person_alert: QMessageBox = QMessageBox(self)

        # setup unidentified person alerts
        audio_output = QAudioOutput(self)
        audio_output.setVolume(0.0 if MUTE_ALERTS else 0.25)
        self._unidentified_person_audio.setAudioOutput(audio_output)
        self._unidentified_person_audio.setSource(QUrl.fromLocalFile("unidentified.wav"))
        self._unidentified_person_alert.setText("Unidentified Person")
        self._unidentified_person_alert.setIcon(QMessageBox.Icon.Warning)

        # setup toolbar and menus
        tool_bar = QToolBar(self)
        self.addToolBar(tool_bar)

        # setup file menu and take picture action
        file_menu = self.menuBar().addMenu("&File")
        shutter_icon = QIcon(str(Path(__file__).parent.parent / "shutter.svg"))
        self._take_picture_action = QAction(
            shutter_icon,
            "&Take Picture",
            self,
            shortcut="Ctrl+T",
            triggered=self.take_picture,
        )
        self._take_picture_action.setToolTip("Take Picture")
        file_menu.addAction(self._take_picture_action)
        tool_bar.addAction(self._take_picture_action)

        exit_action = QAction(
            QIcon.fromTheme("application-exit"),
            "E&xit",
            self,
            shortcut="Ctrl+Q",
            triggered=self.kill_threads,
        )
        file_menu.addAction(exit_action)

        # add About menu
        about_menu = self.menuBar().addMenu("&About")
        about_qt_action = QAction("About &Qt", self, triggered=qApp.aboutQt)  # type: ignore
        about_menu.addAction(about_qt_action)

        # setup main widget (main view)
        self.setCentralWidget(self._tab_widget)

        # initialize thread that connects to the webcam
        self.webcam_thread = WebcamThread()  # python thread
        self._camera_viewfinder.setScaledContents(False)  # we scale ourselves
        self._camera_viewfinder.setMinimumSize(1, 1)  # we set this to start window at smallest size
        self._camera_viewfinder.setMaximumSize(
            self.webcam_thread.width, self.webcam_thread.height - tool_bar.heightForWidth(self.webcam_thread.width)
        )  # dont stretch beyond camera resolution
        self._camera_viewfinder.setAlignment(Qt.AlignCenter)  # center the image

        # initialize and link thread that updates camera view
        self.main_video_thread = VideoThread(self.webcam_thread, self)  # Qt thread
        self.main_video_thread.finished.connect(self.close)  # type: ignore
        self.main_video_thread.updateFrame.connect(self.setImage)

        # initialize and link thread that gets facial recognition results
        self.recognition_thread = RecognitionThread(self.webcam_thread, args)  # python thread

        # initialize and link thread that processes the data and saves it locally or sends it to the api
        self.logging_thread = LoggingThread(self.recognition_thread)  # python thread

        # add the camera to the main view
        self._tab_widget.addTab(self._camera_viewfinder, "Viewfinder")
        self.setWindowTitle(f"EasyID viewer: Camera {WEBCAM_ID}")
        self.show_status_message(f"EasyID viewer: ({self.webcam_thread.width}x{self.webcam_thread.height})")
        # start all threads
        self.start_threads()

    def show_status_message(self, message):
        self.statusBar().showMessage(message, 5000)

    @Slot()
    def take_picture(self, manual: bool = True) -> None:
        file_name = next_image_file_name(manual)
        self._video_pixmap.save(file_name, format="JPG")
        index = self._tab_widget.count()
        image_view = ImageView(index, self._tab_widget, self._video_pixmap, file_name)
        if manual:
            self._tab_widget.addTab(image_view, f"Manual Capture #{index}")
        else:
            self._tab_widget.addTab(image_view, f"Unidentified Person #{index}")
            self._unidentified_person_alert.exec()
            self._unidentified_person_audio.play()
        # self._tab_widget.setCurrentIndex(index)  # switch to new tab

    @Slot()
    def start_threads(self) -> None:
        print("Starting...")
        self.webcam_thread.start()  # start webcam thread / connect to webcam
        self.main_video_thread.start()  # start video thread / update camera on gui
        self.recognition_thread.start()  # start recognition thread / get facial recognition results
        self.logging_thread.start()  # start logging thread / process data to save it locally or send it to the api
        self._take_picture_action.setEnabled(True)  # enable take picture button

    @Slot()
    def kill_threads(self) -> None:
        print("Finishing...")
        self._take_picture_action.setEnabled(False)
        # stop logging thread
        self.logging_thread.stop()
        # stop recognition
        self.recognition_thread.stop()
        # stop the video thread
        self.main_video_thread.stop()
        # stop the webcam thread
        self.webcam_thread.stop()
        # Finish closing the video thread
        self.main_video_thread.terminate()
        time.sleep(1)

    @Slot(QPixmap, bool)
    def setImage(self, pixmap: QPixmap, unidentified_subject: bool) -> None:
        # re-scale the pixmap based on the size of the label (video output thing)
        self._video_pixmap = pixmap.scaled(self._camera_viewfinder.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._camera_viewfinder.setPixmap(self._video_pixmap)
        if not unidentified_subject and time.time() - self.last_unidentified_time > 1:
            self.last_unidentified_time = time.time()
        elif unidentified_subject and time.time() - self.last_unidentified_time > UNIDENTIFIED_SUBJECTS_TIMEOUT:
            self.last_unidentified_time = time.time()
            self.take_picture(manual=False)


def next_image_file_name(manual: bool = True) -> str:
    pictures_location = DEFAULT_DIRECTORY / "Pictures"
    if not pictures_location.exists():
        pictures_location.mkdir()
    date_string = datetime.now().strftime("%Y%m%d")
    prefix = "manual_snapshot_" if manual else "snapshot_"
    pattern = f"{prefix}{date_string}_{{:03d}}.jpg"
    n = 1
    while True:
        resulting_dir = pattern.format(n)
        result = pictures_location / resulting_dir
        if not result.exists():
            return str(result)
        n = n + 1


args = None


def main() -> None:
    global args
    args = parse_arguments()
    if SELF_SIGNED_CERT_DIR is not None:
        os.environ["REQUESTS_CA_BUNDLE"] = str(SELF_SIGNED_CERT_DIR)
    app = QApplication(sys.argv)
    main_win = MainWindow()
    available_geometry = main_win.screen().availableGeometry()
    main_win.resize(available_geometry.width() / 3, available_geometry.height() / 2)
    main_win.show()
    app.exec()


if __name__ == "__main__":
    main()
