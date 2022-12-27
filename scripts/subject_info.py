from dataclasses import dataclass
from pathlib import Path


# this is an easy way to provide standardized data to the upload scripts
@dataclass(frozen=True)
class SubjectRecord:
    last_name: str
    first_name: str
    id_number: int
    grade: int  # 13 means teacher
    image_path: Path

    @property
    def is_teacher(self) -> bool:
        return self.grade == 13

    def std_subject_name(self) -> str:
        return f"{self.last_name}, {self.first_name} ({self.id_number})[{self.grade if not self.is_teacher else 'T'}]"
