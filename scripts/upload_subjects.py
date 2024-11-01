import os
from datetime import datetime
from typing import Dict, List, Set

import requests
from compreface import CompreFace
from compreface.collections import FaceCollection, Subjects
from compreface.service import RecognitionService

from easyID.classes.subject_record import SubjectPathRecord
from easyID.settings import CF_OPTIONS, DETECTION_PROBABILITY_THRESHOLD, SELF_SIGNED_CERT_DIR


class UploadSubjects:
    def __init__(self, api_key: str, host: str, port: str) -> None:
        if SELF_SIGNED_CERT_DIR is not None:  # add self-signed certificate
            os.environ["REQUESTS_CA_BUNDLE"] = str(SELF_SIGNED_CERT_DIR)
        # setup CompreFace
        self.compre_face: CompreFace = CompreFace(host, port, CF_OPTIONS)  # init compreface
        self.recognition: RecognitionService = self.compre_face.init_face_recognition(
            api_key
        )  # setup recognition service
        self.cf_subjects: Subjects = (
            self.recognition.get_subjects()
        )  # this is how we add new subjects & find existing ones
        self.cf_face_collection: FaceCollection = self.recognition.get_face_collection()  # this is how we add new faces

        # std options for uploading subjects
        self.upload_options: dict = dict(det_prob_threshold=DETECTION_PROBABILITY_THRESHOLD)

        # setup other class properties
        self.check_existing_subjects = True
        self.subjects_to_upload: Dict[str, SubjectPathRecord] = {}  # {Subject name: record}

    def add_subjects(self, subjects: List[SubjectPathRecord]) -> None:
        for subject in subjects:
            self.subjects_to_upload[subject.std_subject_name()] = subject
        print(f"{len(self.subjects_to_upload)} Subjects Loaded")

    def upload_subjects(self) -> None:
        existing_subject_names = []  # if they exist, we don't need to add them
        if self.check_existing_subjects:
            existing_subject_names = self.cf_subjects.list().get("subjects", [])
        print("Adding Subjects to DB, This may take a while...")
        s_time = datetime.now()
        for subject_name in self.subjects_to_upload.keys():
            if self.check_existing_subjects and subject_name in existing_subject_names:
                print(f"Subject {subject_name} already exists. Skipping.")
                continue
            print(f"{self.cf_subjects.add(subject_name)['subject']} Added to DB")
        print(f"\n\n\n\n{len(self.subjects_to_upload)- len(existing_subject_names)} Subjects Added to DB")
        print(f"Upload complete in {datetime.now() - s_time} Seconds\n\n\n\n")

    def upload_subject_photos(self) -> None:
        existing_subject_names: set[str] = set()  # if they already have a photo, we don't need to upload another.
        if self.check_existing_subjects:
            existing_subject_names = self.get_existing_subject_photos()
        print("Uploading Photos, This may take a while...")
        s_time = datetime.now()
        total_subjects = len(self.subjects_to_upload)
        s_index = 0
        for subject_name, subject_record in self.subjects_to_upload.items():
            s_index += 1
            if self.check_existing_subjects and subject_name in existing_subject_names:
                print(f"Subject {subject_name} already has a photo. Skipping. {s_index}/{total_subjects}")
                continue
            result = self.cf_face_collection.add(str(subject_record.image_path), subject_name, self.upload_options)
            if result.get("image_id") is None:
                print(f"Error adding {subject_name} to DB. Skipping. {s_index}/{total_subjects}")
                continue
            print(f"Image ID: {result.get('image_id')} For {subject_name} Added to DB, {s_index}/{total_subjects}")
        print(f"\n\n\n\n{total_subjects-len(existing_subject_names)} Pictures Added to DB")
        print(f"Picture Upload complete in {datetime.now() - s_time} Seconds")

    def get_existing_subject_photos(self) -> Set[str]:
        existing_subject_names = set()  # sets have no duplicates
        # setup client
        face_client = self.cf_face_collection.list_of_all_saved_subjects.add_example_of_subject
        photo_url = face_client.url + "?size=1000"

        # send request & loop until we get all the subjects
        response = requests.get(photo_url, headers={"x-api-key": face_client.api_key}).json()
        existing_subject_names.update(set(images["subject"] for images in response["faces"]))
        cur_page = response["page_number"]
        total_pages = response["total_pages"]
        while cur_page < total_pages - 1:
            response = requests.get(
                photo_url + "&page=" + str(cur_page + 1),
                headers={"x-api-key": face_client.api_key},
            ).json()
            cur_page = response["page_number"]
            total_pages = response["total_pages"]
            existing_subject_names.update(set(images["subject"] for images in response["faces"]))
        return existing_subject_names
