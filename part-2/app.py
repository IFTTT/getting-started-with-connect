import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import Tuple

import requests
from PIL import Image
from flask import Flask
from flask import request

service_key = os.environ["IFTTT_SERVICE_KEY"]

app = Flask(__name__)


@app.route("/ifttt/v1/webhooks/trigger_subscription/fired", methods=["POST"])
def handle_trigger_subscription_fired():
    # Extract event details from the incoming webhook request
    connection_id, user_id, original_filename, photo_url = parse_request()

    # Download the photo using the url from the webhook event
    photo_bytes = download_photo(photo_url)

    # Make a thumbnail and save it to static/thumbnails/ directory on your computer.
    # This makes it available for download by Google Drive.
    thumbnail_filename = make_thumbnail(photo_bytes)

    # Run the Google Drive action that will make Google Drive download the thumbnail,
    # effectively uploading the file from our computer to Google Drive.
    schedule_upload(connection_id, user_id, original_filename, thumbnail_filename)

    return ""


def parse_request() -> Tuple[str, str, str, str]:
    body = request.get_json()
    # Request body example:
    # {
    #     "sent_at": 1543520153824,
    #     "data": {
    #         "user_id": "test_user",
    #         "connection_id": "ABC12345",
    #         "trigger_id": "google_drive.any_new_photo"
    #     },
    #     "event_data": {
    #         "ingredients": {
    #             "filename": "photo.jpg",
    #             "photo_url": "https://google.com/photo.jpg",
    #             "path": "/IFTTT/sample.txt",
    #             "created_at": "May 5, 2013 at 11:30PM"
    #         }
    #     },
    #    "sent_at": 1569541305410
    # }
    ingredients = body["event_data"]["ingredients"]
    # TODO: use slugs, not names
    user_id = body["data"]["user_id"]
    connection_id = body["data"]["connection_id"]

    original_filename = ingredients["Filename"]

    photo_url = ingredients["PhotoUrl"]

    return connection_id, user_id, original_filename, photo_url


def download_photo(photo_url: str) -> bytes:
    return requests.get(photo_url).content


def make_thumbnail(photo_bytes: bytes) -> str:
    im = Image.open(BytesIO(photo_bytes))
    im.thumbnail((128, 128))
    thumbnail_filename = f"{uuid.uuid4()}.png"
    im.save(f"{app.root_path}/static/thumbnails/{thumbnail_filename}")

    return thumbnail_filename


def schedule_upload(connection_id: str, user_id: str, original_filename: str, thumbnail_filename: str) -> None:
    url = f"https://connect.ifttt.com/v2/connections/{connection_id}/actions/google_drive.upload_file_from_url_google_drive/run?user_id={user_id}"
    headers = {
        "Content-Type": "application/json",
        f"IFTTT-Service-Key": service_key
    }
    body = {
        "fields": {
            "url": f"https://image-processor.ngrok.io/static/thumbnails/{thumbnail_filename}",
            "filename": str(Path(original_filename).with_suffix(".png"))
        }
    }

    requests.post(url, headers=headers, json=body)
