import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Union

from easyID.settings import API_KEY, DEFAULT_HOST, DEFAULT_PORT
from scripts.subject_info import SubjectRecord
from scripts.upload_subjects import UploadSubjects


# when exporting the csv file, use default settings for the delimiter and quotechar. You need to at least include the following columns:
# Last Name, First Name, Subject ID(student ID), Internal ID, Grade, Images. The order doesn't matter, but don't change the names of the rows.
def parse_arguments() -> Tuple[Path, Path, str, str, str]:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--spreadsheet-path", help="The location of the spreadsheet(csv) exported from blueprint", type=str, default=str(Path(".") / "students.csv")
    )
    parser.add_argument("--photo-dir", help="Directory where all the photos are located", type=str, default=str(Path(".")))
    parser.add_argument("--api-key", help="CompreFace recognition service API key", type=str, default=API_KEY)
    parser.add_argument("--host", help="CompreFace host", type=str, default=DEFAULT_HOST)
    parser.add_argument("--port", help="CompreFace port", type=str, default=DEFAULT_PORT)

    args = parser.parse_args()

    return (
        Path(args.spreadsheet_path),
        Path(args.photo_dir),
        args.api_key,
        args.host,
        args.port,
    )


@dataclass
class ParseBlueprintData:
    def __init__(self, spreadsheet_path: Path, photo_dir: Path) -> None:
        self.spreadsheet_path: Path = spreadsheet_path
        self.photo_dir: Path = photo_dir
        self.subject_records: List[SubjectRecord] = []
        # validate the paths
        if not self.spreadsheet_path.exists() and not self.spreadsheet_path.is_file():
            raise ValueError("The spreadsheet does not exist")
        if not self.photo_dir.exists() and not self.photo_dir.is_dir():
            raise ValueError("The photo directory does not exist")

    def parse_subject_records(self) -> None:
        # get the spreadsheet data as a dict
        sheet_list = self.spreadsheet_to_dict()
        # now we parse the data into a list of SubjectRecord objects
        subject_records = []
        for row in sheet_list:
            # first we get the image path
            if row["Images"] == "":
                print(f"Skipping {row['First Name']} {row['Last Name']} because they have no picture")
                continue
            image_path = self.photo_dir / row["Images"]
            if not image_path.exists() and not image_path.is_file():
                raise ValueError(f"The image for {row['Last Name']}, {row['First Name']} does not exist")
            # now we create the SubjectRecord object
            try:
                id_number = row["Subject ID"] if row["Subject ID"] else row["Internal ID"]  # if empty, use Internal ID (for volunteers)
                int(id_number)  # validate that the id number can be converted to an int (keep leading zeros)
                subject_records.append(
                    SubjectRecord(
                        str(row["Last Name"]),
                        str(row["First Name"]),
                        id_number,
                        int(row["Grade"] if row["Grade"] else 13),
                        Path(image_path),
                    )
                )

            except ValueError:
                raise ValueError(f"Invalid data for {row}")
        self.subject_records = subject_records

    def spreadsheet_to_dict(self) -> List[Dict[str, Union[str, int]]]:
        expected_rows = [
            "Last Name",
            "First Name",
            "Subject ID",
            "Internal ID",
            "Grade",
            "Images",
        ]
        sheet_list = []
        with open(self.spreadsheet_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            # validate that format matches what we expect (I do this kinda stupidly)
            loop = 0
            for row in reader:
                if loop == 0:
                    loop = 1
                    # if all required elements exist, continue
                    if not all(elem in row.keys() for elem in expected_rows):
                        raise ValueError("The spreadsheet is not in the correct format")
                sheet_list.append(row)
        return sheet_list


def main() -> None:
    # load args and process data
    spreadsheet_path, photo_dir, api_key, host, port = parse_arguments()
    print(f"Processing spreadsheet: {spreadsheet_path}")
    blueprint_data = ParseBlueprintData(spreadsheet_path, photo_dir)
    blueprint_data.parse_subject_records()
    # load data into standardized upload script
    upload_subjects = UploadSubjects(api_key, host, port)
    upload_subjects.add_subjects(blueprint_data.subject_records)
    if input("Upload all subjects? (y/n): ").lower() == "y":
        # upload subjects
        upload_subjects.upload_subjects()
        # upload photos for the subjects
        upload_subjects.upload_subject_photos()
        print("Done!")


if __name__ == "__main__":
    main()
