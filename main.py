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
        return None

    creds_info = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
    return build("drive", "v3", credentials=creds)


@app.route("/", methods=["GET"])
def home():
    return "Server is running successfully!"


@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        data = request.get_json()
        url = data.get("url")
        if not url:
            return jsonify({"error": "URL missing"}), 400

        # Download file from URL
        file_data = requests.get(url, stream=True)
        if file_data.status_code != 200:
            return jsonify({"error": "Failed to download file"}), 400

        filename = url.split("/")[-1] or "file.bin"
        file_bytes = io.BytesIO(file_data.content)

        service = get_drive_service()
        if service is None:
            return jsonify({"error": "Google token missing"}), 500

        media = MediaIoBaseUpload(file_bytes, mimetype="application/octet-stream", resumable=True)
        uploaded = service.files().create(
            media_body=media,
            body={"name": filename},
            fields="id"
        ).execute()

        return jsonify({
            "status": "success",
            "file": filename,
            "drive_link": f"https://drive.google.com/file/d/{uploaded['id']}/view"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
