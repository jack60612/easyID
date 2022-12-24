from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RecognitionResult:
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    age_high: Optional[int]
    age_low: Optional[int]
    gender: Optional[str]
    subject: Optional[str]
    similarity: Optional[float]

    @classmethod
    def from_result(cls, result: Dict[str, Any]) -> "RecognitionResult":
        if result["box"]:
            age = result.get("age", {})
            age_high = age.get("high")
            age_low = age.get("low")
            gender = result.get("gender", {}).get("value")
            subject_d = result.get("subjects", [{}])[0]
            subject = subject_d.get("subject")
            similarity = subject_d.get("similarity")
            return cls(
                result["box"]["x_min"],
                result["box"]["y_min"],
                result["box"]["x_max"],
                result["box"]["y_max"],
                age_high,
                age_low,
                gender,
                subject,
                similarity,
            )


def process_rec_results(
    results: Optional[list[dict[str, Any]]]
) -> List[RecognitionResult]:
    if results is None:
        return []
    return [RecognitionResult.from_result(result) for result in results]
