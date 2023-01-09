import csv
from datetime import datetime
from pathlib import Path

from easyID.classes.subject_record import SubjectRecord
from easyID.settings import DEFAULT_DIRECTORY


class SpreadsheetExporter:
    """Export data to a spreadsheet."""

    def __init__(self, folder_path: Path = DEFAULT_DIRECTORY / "Data") -> None:
        folder_path.mkdir(parents=True, exist_ok=True)
        self.file_name: Path = get_file_name(folder_path)
        self.fieldnames = ["ID Number", "Last Name", "First Name", "Grade", "First Seen", "Last Seen", "Times Seen"]
        self.initialized = False

    def export(self, records_and_times: dict[SubjectRecord, list[datetime]]) -> None:
        with open(self.file_name, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames, dialect="excel")
            if not self.initialized:
                writer.writeheader()
                self.initialized = True
            for record, times in records_and_times.items():
                writer.writerow(
                    {
                        "ID Number": record.id_number,
                        "Last Name": record.last_name,
                        "First Name": record.first_name,
                        "Grade": record.grade,
                        "First Seen": times[0].strftime("%x %X"),
                        "Last Seen": times[-1].strftime("%x %X"),
                        "Times Seen": len(times),
                    }
                )


def get_file_name(root_dir: Path) -> Path:
    date_string = datetime.now().strftime("%Y%m%d")
    pattern = f"easyID_log_{date_string}{{}}.csv"
    n = 0
    while True:
        if n == 0:
            i_str = ""
        else:
            i_str = f"({n})"
        resulting_dir = pattern.format(i_str)
        result = root_dir / resulting_dir
        if not result.exists():
            return result
        n = n + 1
