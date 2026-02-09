"""Configuration management for GHL CLI."""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class GHLConfig(BaseModel):
    """Configuration model for GHL CLI."""

    location_id: Optional[str] = Field(default=None, description="Default location/sub-account ID")
    api_version: str = Field(default="2021-07-28", description="API version header")
    output_format: str = Field(default="table", description="Default output format")

    class Config:
        extra = "ignore"


class ConfigManager:
    """Manages GHL CLI configuration storage and retrieval."""

    CONFIG_DIR = Path.home() / ".ghl_tui"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"

    def __init__(self):
        self._config: Optional[GHLConfig] = None

    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Secure the directory
        os.chmod(self.CONFIG_DIR, 0o700)

    @property
    def config(self) -> GHLConfig:
        """Get the current configuration, loading from disk if needed."""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> GHLConfig:
        """Load configuration from disk."""
        if self.CONFIG_FILE.exists():
            try:
                data = json.loads(self.CONFIG_FILE.read_text())
                return GHLConfig(**data)
            except (json.JSONDecodeError, Exception):
                return GHLConfig()
        return GHLConfig()

    def save_config(self, config: GHLConfig) -> None:
        """Save configuration to disk."""
        self._ensure_config_dir()
        self.CONFIG_FILE.write_text(config.model_dump_json(indent=2))
        os.chmod(self.CONFIG_FILE, 0o600)
        self._config = config

    def update_config(self, **kwargs) -> GHLConfig:
        """Update configuration with new values."""
        current = self.config.model_dump()
        current.update({k: v for k, v in kwargs.items() if v is not None})
        new_config = GHLConfig(**current)
        self.save_config(new_config)
        return new_config

    def get_token(self) -> Optional[str]:
        """Get the stored API token."""
        # First check environment variable
        env_token = os.environ.get("GHL_API_TOKEN")
        if env_token:
            return env_token

        # Then check credentials file
        if self.CREDENTIALS_FILE.exists():
            try:
                data = json.loads(self.CREDENTIALS_FILE.read_text())
                return data.get("api_token")
            except (json.JSONDecodeError, Exception):
                pass

        # Try keyring as fallback
        try:
            import keyring

            token = keyring.get_password("ghl_tui", "api_token")
            if token:
                return token
        except Exception:
            pass

        return None

    def set_token(self, token: str, use_keyring: bool = False) -> None:
        """Store the API token securely."""
        if use_keyring:
            try:
                import keyring

                keyring.set_password("ghl_tui", "api_token", token)
                return
            except Exception:
                pass  # Fall back to file storage

        # Store in credentials file
        self._ensure_config_dir()
        credentials = {"api_token": token}
        self.CREDENTIALS_FILE.write_text(json.dumps(credentials, indent=2))
        os.chmod(self.CREDENTIALS_FILE, 0o600)

    def clear_token(self) -> None:
        """Remove the stored API token."""
        # Try keyring first
        try:
            import keyring

            keyring.delete_password("ghl_tui", "api_token")
        except Exception:
            pass

        # Remove credentials file
        if self.CREDENTIALS_FILE.exists():
            self.CREDENTIALS_FILE.unlink()

    def get_location_id(self) -> Optional[str]:
        """Get the current location ID from config or environment."""
        # Environment variable takes precedence
        env_location = os.environ.get("GHL_LOCATION_ID")
        if env_location:
            return env_location
        return self.config.location_id


# Global config manager instance
config_manager = ConfigManager()
