# this is used by the import scripts & used by the app to re standardize the data
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SubjectRecord:
    last_name: str
    first_name: str
    id_number: str  # it's a string because we want to keep leading zeros
    grade: int  # 13 means teacher

    def __post_init__(self):
        if not self.id_number.isnumeric():
            raise ValueError(f"Invalid ID number: {self.id_number} for {self.last_name}, {self.first_name}")
        if not (0 <= self.grade <= 13):
            raise ValueError(f"Invalid grade: {self.grade} for {self.last_name}, {self.first_name}")

    @classmethod
    def from_string(cls, subject_string: str) -> "SubjectRecord":
        """
        This is used by the app to reparse the subject data
        """
        # split the string back into its parts
        last_name, first_name, id_number, grade = subject_string.split(" ")
        # remove the brackets
        grade = grade[1:-1] if grade[1] != "T" else 13
        # remove the parentheses
        id_number = id_number[1:-1]
        # remove the comma
        last_name = last_name[:-1]
        if not id_number.isdigit():
            raise ValueError("Invalid ID number")
        return cls(last_name, first_name, id_number, int(grade))

    @property
    def is_teacher(self) -> bool:
        return self.grade == 13

    def std_subject_name(self) -> str:
        return f"{self.last_name}, {self.first_name} ({self.id_number}) [{self.grade if not self.is_teacher else 'T'}]"


@dataclass(frozen=True)
class SubjectPathRecord(SubjectRecord):  # we have a separate path because the path is only used by the import scripts
    image_path: Path
