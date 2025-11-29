from flask import Flask, request, jsonify
import os, requests, io, json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = Flask(__name__)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_drive_service():
    token_json = os.environ.get("GOOGLE_TOKEN_JSON")
    if not token_json:
        raise RuntimeError("GOOGLE_TOKEN_JSON missing")

    creds_info = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
    return build("drive", "v3", credentials=creds)

@app.route("/", methods=["GET"])
def home():
    return "Server is running!"

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json(force=True)
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL missing"}), 400

    file_data = requests.get(url)
    if file_data.status_code != 200:
        return jsonify({"error": "Download failed"}), 400

    filename = url.split("/")[-1] or "file"
    content = io.BytesIO(file_data.content)

    drive = get_drive_service()
    media = MediaIoBaseUpload(content, mimetype="application/octet-stream", resumable=True)

    uploaded = drive.files().create(
        body={"name": filename},
        media_body=media,
        fields="id"
    ).execute()

    file_id = uploaded.get("id")
    return jsonify({
        "status": "success",
        "drive_link": f"https://drive.google.com/file/d/{file_id}/view"
    })

if __name__ == "__main__":
    port = int(os.environ["PORT"])   # <-- 100% required for Railway
    app.run(host="0.0.0.0", port=port)
