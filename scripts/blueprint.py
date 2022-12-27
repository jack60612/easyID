import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Union

from scripts.subject_info import SubjectRecord


# when exporting the csv file, use default settings for the delimiter and quotechar. You need to at least include the following columns:
# Last Name, First Name, Subject ID(student ID), Grade, Images. The order doesn't matter, but don't change the names of the rows.
def parse_arguments() -> Tuple[Path, Path]:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--spreadsheet-path",
        help="The location of the spreadsheet(csv) exported from blueprint",
        type=str,
        default=str(Path(".") / "students.csv"),
    )
    parser.add_argument(
        "--photo-dir",
        help="Directory where all the photos are located",
        type=str,
        default=str(Path(".")),
    )

    args = parser.parse_args()

    return Path(args.spreadsheet_path), Path(args.photo_dir)


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
            image_path = self.photo_dir / row["Images"]
            if not image_path.exists() and not image_path.is_file():
                raise ValueError(
                    f"The image for {row['Last Name']}, {row['First Name']} does not exist"
                )
            # now we create the SubjectRecord object
            subject_records.append(
                SubjectRecord(
                    row["Last Name"],
                    row["First Name"],
                    row["Subject ID"],
                    row["Grade"],
                    image_path,
                )
            )
        self.subject_records = subject_records

    def spreadsheet_to_dict(self) -> List[Dict[str, Union[str, int]]]:
        sheet_list = []
        with open(self.spreadsheet_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            # validate that format matches what we expect (I do this kinda stupidly)
            loop = 0
            for row in reader:
                if loop == 0:
                    loop = 1
                    # if all required elements exist, continue
                    if not all(
                        elem in row.keys()
                        for elem in [
                            "Last Name",
                            "First Name",
                            "Subject ID",
                            "Grade",
                            "Images",
                        ]
                    ):
                        raise ValueError("The spreadsheet is not in the correct format")
                sheet_list.append(row)
        return sheet_list


def main() -> None:
    spreadsheet_path, photo_dir = parse_arguments()
    blueprint_data = ParseBlueprintData(spreadsheet_path, photo_dir)
    blueprint_data.parse_subject_records()


if __name__ == "__main__":
    main()
