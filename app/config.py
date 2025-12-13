import os


class Config:
    def __init__(self):
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
        self.SQLALCHEMY_DATABASE_URI = os.getenv(
            "DATABASE_URL",
            "sqlite:///miwalavie.db",
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
        self.MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
