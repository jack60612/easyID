# This thread is used to log / remember who was seen and when.
import datetime
import time
from queue import Empty
from threading import Thread

from easyID.classes.recognition_result import RecognitionResult
from easyID.classes.subject_record import SubjectRecord
from easyID.threads.exporters.export_to_spreadsheet import SpreadsheetExporter
from easyID.threads.recognition_thread import RecognitionThread


class LoggingThread:
    """
    This class is made up of two threads. One thread initially process the results.
    Another thread either exports the results to a file or sends them to the api.
    """

    def __init__(self, recognition_thread: RecognitionThread) -> None:
        self._stop: bool = False
        self._receiving_thread: Thread = Thread(target=self._receiver)
        self._exporting_thread: Thread = Thread(target=self._export_data)

        self._recognition_thread: RecognitionThread = recognition_thread
        # {datetime to the minute: {SubjectRecord: list[all seconds seen]}}
        self._pending_results: dict[datetime.datetime, dict[SubjectRecord, list[int]]] = {}
        # export class
        self.export_class = SpreadsheetExporter()

    def start(self) -> None:
        self._receiving_thread.start()
        self._exporting_thread.start()

    def stop(self) -> None:
        self._stop = True
        self._exporting_thread.join()  # wait for exporter to stop
        for minute_ts, results in self._pending_results.keys():  # export remaining data on shutdown.
            final_subject_info = get_real_timestamps(minute_ts, results)
            self.export_class.export(final_subject_info)

    def _receiver(self) -> None:
        while not self._stop:
            if not self._recognition_thread.running:
                print("Recognition Thread not running, exiting Logging Thread")
                self.stop()
                break
            try:  # timestamp is datetime, results is a non-empty list of RecognitionResult
                timestamp, results = self._recognition_thread.logging_queue.get(timeout=1)  # 1 second timeout
            except Empty:
                continue
            filtered_results: list[RecognitionResult] = [
                result for result in results if result.is_matching and result.subject is not None
            ]
            if len(filtered_results) == 0:
                continue
            subjects: list[SubjectRecord] = [SubjectRecord.from_string(result.subject) for result in filtered_results]
            minute_timestamp = timestamp_to_minute(timestamp)
            if minute_timestamp not in self._pending_results:
                self._pending_results[minute_timestamp] = {}
            seconds = timestamp.second
            for subject in subjects:
                if subject not in self._pending_results[minute_timestamp]:
                    self._pending_results[minute_timestamp][subject] = []
                self._pending_results[minute_timestamp][subject].append(seconds)
        print("Logging Receiving Thread Exited")

    def _export_data(self) -> None:
        while not self._stop:
            if len(self._pending_results) == 0:
                time.sleep(1)
                continue
            oldest_minute = list(self._pending_results.keys())[0]
            if oldest_minute > datetime.datetime.now() - datetime.timedelta(minutes=1):
                time.sleep(1)
                continue
            minute_results: dict[SubjectRecord, list[int]] = self._pending_results.pop(oldest_minute)
            final_subject_info = get_real_timestamps(oldest_minute, minute_results)
            self.export_class.export(final_subject_info)
        print("Logging Exporting Thread Exited")


def get_real_timestamps(
    minute_timestamp: datetime.datetime, result_seconds: dict[SubjectRecord, list[int]]
) -> dict[SubjectRecord, list[datetime.datetime]]:
    return {
        result: [minute_timestamp + datetime.timedelta(seconds=second) for second in seconds]
        for result, seconds in result_seconds.items()
    }


def timestamp_to_minute(timestamp: datetime.datetime) -> datetime.datetime:
    return timestamp.replace(second=0, microsecond=0)
