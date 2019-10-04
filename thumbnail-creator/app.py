import os
import uuid
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image
from flask import Flask
from flask import request

# The url of your service. It is passed to Google Drive to be used for downloading a thumbnail.
service_url = os.environ["IFTTT_SERVICE_URL"]
# Your service secret key. Used to authenticate this client with Connect API.
service_key = os.environ["IFTTT_SERVICE_KEY"]

app = Flask(__name__)


# A webhook request handler.
# IFTTT will send this webhook when a new photo is added to a user's Google Drive.
@app.route("/ifttt/v1/webhooks/trigger_subscription/fired", methods=["POST"])
def handle_trigger_subscription_fired():
    # Extract event details from the incoming webhook request
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
    request_json = request.get_json()

    # The id of your user (https://platform.ifttt.com/docs/api_reference#user-information)
    user_id = request_json["data"]["user_id"]
    # The id of this trigger's the connection
    connection_id = request_json["data"]["connection_id"]
    # The original photo file name (ex: My Graduation 01.jpg)
    photo_filename = request_json["event_data"]["ingredients"]["filename"]
    # The download url for the photo
    photo_url = request_json["event_data"]["ingredients"]["photo_url"]

    # Download the photo
    photo_bytes = requests.get(photo_url).content

    # Make a thumbnail
    image = Image.open(BytesIO(photo_bytes))
    image.thumbnail((128, 128))
    thumbnail_filename = f"{uuid.uuid4()}.png"  # Use a random name to avoid collisions
    # Save the thumbnail to static/thumbnails/ directory on your computer.
    # This makes it available for download by Google Drive.
    image.save(f"{app.root_path}/static/thumbnails/{thumbnail_filename}")

    # Run the Google Drive action that will make Google Drive download the thumbnail,
    # effectively uploading the file from our computer to Google Drive.
    action_run_url = f"https://connect.ifttt.com/v2/connections/{connection_id}/actions/google_drive.upload_file_from_url_google_drive/run?user_id={user_id}"
    headers = {
        "Content-Type": "application/json",
        f"IFTTT-Service-Key": service_key
    }
    # Override the field values with the actual url and filename
    action_run_body = {
        "fields": {
            "url": f"{service_url}/static/thumbnails/{thumbnail_filename}",
            "filename": str(Path(photo_filename).with_suffix(".png"))
        }
    }

    r = requests.post(action_run_url, headers=headers, json=action_run_body)
    r.raise_for_status()

    return ""
