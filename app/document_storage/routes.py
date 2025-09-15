from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from pathlib import Path
import io
import logging
from app.document_storage.services import GoogleDriveService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

drive_router = APIRouter()


# Initialize GoogleDriveService
google_drive_service = GoogleDriveService()

@drive_router.get("/auth")
async def auth():
    """Initialize OAuth flow and return authorization URL."""
    try:
        auth_url, state = google_drive_service.authenticate()
        return {"auth_url": auth_url, "state": state}
    except Exception as e:
        logger.error(f"Error initializing OAuth flow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing OAuth flow: {str(e)}")

@drive_router.get("/auth/callback")
async def auth_callback(code: str, state: str):
    """Handle OAuth callback and save credentials."""
    try:
        credentials = google_drive_service.handle_auth_callback(code)
        return JSONResponse({"message": "Authentication successful. You can now use the API."})
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@drive_router.get("/list-files/")
async def list_files(folder_id: str | None = None):
    """List metadata of files in Google Drive."""
    credentials = google_drive_service.load_credentials()
    if not credentials or not credentials.valid:
        logger.warning("Invalid credentials, re-authentication required")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    drive_service = google_drive_service.get_drive_service(credentials)

    try:
        query = "trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
            try:
                drive_service.files().get(fileId=folder_id, fields='id').execute()
            except Exception as e:
                logger.error(f"Folder not found or access denied: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Folder not found or access denied: {str(e)}")

        results = drive_service.files().list(
            q=query,
            fields="files(id, name, mimeType, createdTime, modifiedTime)"
        ).execute()
        files = results.get('files', [])
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error listing files: {str(e)}")

@drive_router.post("/upload/")
async def upload_file(file: UploadFile = File(...), folder_id: str | None = None):
    """Upload a file to Google Drive."""
    credentials = google_drive_service.load_credentials()
    if not credentials or not credentials.valid:
        logger.warning("Invalid credentials, re-authentication required")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    drive_service = google_drive_service.get_drive_service(credentials)

    if folder_id:
        try:
            drive_service.files().get(fileId=folder_id, fields='id').execute()
        except Exception as e:
            logger.error(f"Folder not found or access denied: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Folder not found or access denied: {str(e)}")

    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        file_metadata = {"name": file.filename}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(temp_file_path, mimetype=file.content_type)
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        file_id = uploaded_file.get("id")
        return {"file_id": file_id, "message": f"File {file.filename} uploaded successfully"}
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")
    finally:
        if Path(temp_file_path).exists():
            Path(temp_file_path).unlink()

@drive_router.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download a file from Google Drive."""
    credentials = google_drive_service.load_credentials()
    if not credentials or not credentials.valid:
        logger.warning("Invalid credentials, re-authentication required")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    drive_service = google_drive_service.get_drive_service(credentials)

    try:
        file_metadata = drive_service.files().get(fileId=file_id, fields='name').execute()
        file_name = file_metadata.get('name', 'downloaded_file')
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return StreamingResponse(fh, headers={"Content-Disposition": f"attachment; filename={file_name}"})
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")

