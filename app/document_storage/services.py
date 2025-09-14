from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from fastapi import HTTPException
from pathlib import Path
import logging

from app.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN_FILE = Path(__file__).parent.parent.parent / 'token.json'
CREDENTIALS_FILE = Path(__file__).parent.parent.parent / 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
DOMAIN = Config.DOMAIN_NAME

class GoogleDriveService:
    def get_drive_service(self, credentials: Credentials):
        """Create a Google Drive service from credentials."""
        try:
            return build('drive', 'v3', credentials=credentials)
        except Exception as e:
            logger.error(f"Error initializing Drive service: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error initializing Drive service: {str(e)}")

    def load_credentials(self):
        """Load credentials from token.json and refresh if needed."""
        if TOKEN_FILE.exists():
            try:
                credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                # Refresh token if expired and refresh_token is available
                if credentials.expired and credentials.refresh_token:
                    logger.info("Access token expired, refreshing...")
                    credentials.refresh(Request())
                    self.save_credentials(credentials)
                return credentials
            except Exception as e:
                logger.error(f"Invalid credentials file: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid credentials file: {str(e)}")
        logger.warning("token.json not found, re-authentication required")
        return None

    def save_credentials(self, credentials: Credentials):
        """Save credentials to token.json."""
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(credentials.to_json())
            logger.info("Credentials saved to token.json")
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error saving credentials: {str(e)}")

    def authenticate(self):
        """Initialize OAuth flow and return authorization URL."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES,
                redirect_uri=f'{DOMAIN}/drive/auth/callback'
            )
            auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')
            logger.info(f"Generated auth URL: {auth_url}")
            return auth_url, state
        except Exception as e:
            logger.error(f"Error initializing OAuth flow: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error initializing OAuth flow: {str(e)}")

    def handle_auth_callback(self, code: str):
        """Handle OAuth callback and save credentials."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES,
                redirect_uri=f'{DOMAIN}:8000/drive/auth/callback'
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials
            self.save_credentials(credentials)
            logger.info("OAuth authentication successful")
            return credentials
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")