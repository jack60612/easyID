import argparse
import os
import sys
import time
from pathlib import Path

import cv2
from PySide6.QtCore import QDate, QDir, QStandardPaths, Qt, QUrl, Slot
from PySide6.QtGui import (
    QAction,
    QDesktopServices,
    QGuiApplication,
    QIcon,
    QImage,
    QPixmap,
)
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
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
    DEFAULT_HOST,
    DEFAULT_PORT,
    MUTE_ALERTS,
    SELF_SIGNED_CERT_DIR,
    UNIDENTIFIED_SUBJECTS_TIMEOUT,
    WEBCAM_ID,
)
from easyID.video_processing import ProcessingThread
from easyID.webcam_thread import VideoThread


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--api-key",
        help="CompreFace recognition service API key",
        type=str,
        default=API_KEY,
    )
    parser.add_argument(
        "--host", help="CompreFace host", type=str, default=DEFAULT_HOST
    )
    parser.add_argument(
        "--port", help="CompreFace port", type=str, default=DEFAULT_PORT
    )

    args = parser.parse_args()

    return args


# Image View Widget (On new image tabs)
class ImageView(QWidget):
    def __init__(
        self, index: int, parent: QTabWidget, preview_pixmap: QPixmap, file_name: str
    ) -> None:
        super().__init__()

        self._index = index
        self._parent = parent
        self._file_name = file_name

        main_layout = QVBoxLayout(self)
        self._image_label = QLabel()
        self._image_label.setPixmap(preview_pixmap)
        main_layout.addWidget(self._image_label)

        top_layout = QHBoxLayout()
        self._file_name_label = QLabel(QDir.toNativeSeparators(file_name))
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
        self.last_unidentified_time: int = (
            0  # gap between last unidentified subject and current time to avoid spam
        )
        self._preview_pixmap: QPixmap = QPixmap()
        self._tab_widget: QTabWidget = QTabWidget()
        self._camera_viewfinder: QLabel = QLabel(self)

        # unidentified alerts & audio ( use default device )
        self._unidentified_person_audio: QMediaPlayer = QMediaPlayer(self)
        self._unidentified_person_alert: QMessageBox = QMessageBox()

        # setup unidentifed person alerts
        audio_output = QAudioOutput(self)
        audio_output.setVolume(0.0 if MUTE_ALERTS else 0.25)
        self._unidentified_person_audio.setAudioOutput(audio_output)
        self._unidentified_person_audio.setSource(
            QUrl.fromLocalFile("unidentified.wav")
        )
        self._unidentified_person_alert.setText("Unidentified Person")
        self._unidentified_person_alert.setIcon(QMessageBox.Icon.Warning)

        # setup toolbar and menus
        tool_bar = QToolBar()
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

        # initalize and link thread that updates camera view
        self.main_video_thread = VideoThread(self)
        self.main_video_thread.finished.connect(self.close)
        self.main_video_thread.updateFrame.connect(self.setImage)
        self._camera_viewfinder.setFixedSize(
            self.main_video_thread.width, self.main_video_thread.height
        )

        # initialize and link thread that gets facial recognition results
        self.main_processing_thread = ProcessingThread(self.main_video_thread, args)
        self.main_processing_thread.finished.connect(self.close)

        # add the camera to the main view
        self._tab_widget.addTab(self._camera_viewfinder, "Viewfinder")
        self.setWindowTitle(f"EasyID viewer: Camera {WEBCAM_ID}")
        self.show_status_message(
            f"EasyID viewer: ({self.main_video_thread.width}x{self.main_video_thread.height})"
        )
        # start thread
        self.start()

    def show_status_message(self, message):
        self.statusBar().showMessage(message, 5000)

    @Slot()
    def take_picture(self, manual: bool = True) -> None:
        file_name = next_image_file_name(manual)
        self._preview_pixmap.save(file_name, format="JPG")
        index = self._tab_widget.count()
        image_view = ImageView(index, self._tab_widget, self._preview_pixmap, file_name)
        if manual:
            self._tab_widget.addTab(image_view, f"Manual Capture #{index}")
        else:
            self._tab_widget.addTab(image_view, f"Unidentified Person #{index}")
            self._unidentified_person_alert.exec()
            self._unidentified_person_audio.play()
        self._tab_widget.setCurrentIndex(index)

    @Slot()
    def kill_threads(self) -> None:
        print("Finishing...")
        self._take_picture_action.setEnabled(False)
        self.main_video_thread.cap.release()
        cv2.destroyAllWindows()
        self.main_video_thread.terminate()
        self.main_processing_thread.terminate()
        # Give time for the thread to finish
        time.sleep(1)

    @Slot()
    def start(self) -> None:
        print("Starting...")
        self._take_picture_action.setEnabled(True)
        self.main_video_thread.start()
        self.main_processing_thread.start()

    @Slot(QImage, bool)
    def setImage(self, image: QImage, unidentified_subject: bool) -> None:
        self._preview_pixmap = QPixmap.fromImage(image)
        self._camera_viewfinder.setPixmap(self._preview_pixmap)
        if (
            unidentified_subject
            and time.time() - self.last_unidentified_time
            > UNIDENTIFIED_SUBJECTS_TIMEOUT
        ):
            self.last_unidentified_time = time.time()
            self.take_picture(manual=False)


def next_image_file_name(manual: bool = True) -> str:
    pictures_location = (
        Path(QStandardPaths.writableLocation(QStandardPaths.PicturesLocation))
        / "easyID"
    )
    if not pictures_location.exists():
        pictures_location.mkdir()
    date_string = QDate.currentDate().toString("yyyyMMdd")
    prefix = "manual_snapshot_" if manual else "snapshot_"
    pattern = f"{pictures_location}/{prefix}{date_string}_{{:03d}}.jpg"
    n = 1
    while True:
        result = pattern.format(n)
        if not Path(result).exists():
            return result
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
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
