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


class ProfileModel(BaseModel):
    """A single GHL profile (token + location)."""

    api_token: str
    location_id: str

    class Config:
        extra = "ignore"


class ConfigManager:
    """Manages GHL CLI configuration storage and retrieval."""

    CONFIG_DIR = Path.home() / ".ghl_tui"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
    PROFILES_FILE = CONFIG_DIR / "profiles.json"

    def __init__(self):
        self._config: Optional[GHLConfig] = None
        self._profiles_data: Optional[dict] = None

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
        """Update configuration with new values. Updates active profile location_id if set."""
        if "location_id" in kwargs and kwargs["location_id"] is not None:
            active_name = self.get_active_profile_name()
            if active_name:
                profile = self.get_profile(active_name)
                if profile:
                    self.add_or_update_profile(
                        active_name, profile.api_token, kwargs["location_id"]
                    )
        current = self.config.model_dump()
        current.update({k: v for k, v in kwargs.items() if v is not None})
        new_config = GHLConfig(**current)
        self.save_config(new_config)
        return new_config

    def _load_profiles_data(self) -> dict:
        """Load profiles from disk. Returns {active, profiles: {name: {api_token, location_id}}}."""
        if self._profiles_data is not None:
            return self._profiles_data
        if not self.PROFILES_FILE.exists():
            self._profiles_data = {"active": None, "profiles": {}}
            return self._profiles_data
        try:
            data = json.loads(self.PROFILES_FILE.read_text())
            self._profiles_data = {
                "active": data.get("active"),
                "profiles": data.get("profiles") or {},
            }
            return self._profiles_data
        except (json.JSONDecodeError, Exception):
            self._profiles_data = {"active": None, "profiles": {}}
            return self._profiles_data

    def _save_profiles_data(self) -> None:
        """Persist profiles to disk."""
        self._ensure_config_dir()
        self.PROFILES_FILE.write_text(json.dumps(self._profiles_data or {}, indent=2))
        os.chmod(self.PROFILES_FILE, 0o600)

    def get_active_profile_name(self) -> Optional[str]:
        """Name of the currently active profile, or None."""
        data = self._load_profiles_data()
        active = data.get("active")
        if active and active in (data.get("profiles") or {}):
            return active
        return None

    def set_active_profile(self, name: str) -> None:
        """Set the active profile by name. Persists to disk."""
        data = self._load_profiles_data()
        profiles = data.get("profiles") or {}
        if name not in profiles:
            raise ValueError(f"Profile '{name}' does not exist")
        data["active"] = name
        self._profiles_data = data
        self._save_profiles_data()

    def list_profiles(self) -> list[tuple[str, bool]]:
        """Return list of (profile_name, is_active)."""
        data = self._load_profiles_data()
        profiles = data.get("profiles") or {}
        active = data.get("active")
        return [(name, name == active) for name in sorted(profiles.keys())]

    def get_profile(self, name: str) -> Optional[ProfileModel]:
        """Get a profile by name."""
        data = self._load_profiles_data()
        profiles = data.get("profiles") or {}
        raw = profiles.get(name)
        if not raw:
            return None
        try:
            return ProfileModel(api_token=raw["api_token"], location_id=raw["location_id"])
        except (KeyError, Exception):
            return None

    def add_or_update_profile(self, name: str, api_token: str, location_id: str) -> None:
        """Add a new profile or update existing. Persists to disk."""
        data = self._load_profiles_data()
        profiles = data.get("profiles") or {}
        profiles[name] = {"api_token": api_token, "location_id": location_id}
        data["profiles"] = profiles
        if not data.get("active") or data["active"] not in profiles:
            data["active"] = name
        self._profiles_data = data
        self._save_profiles_data()

    def remove_profile(self, name: str) -> Optional[str]:
        """Remove a profile. Returns previous active name if we removed it, else None."""
        data = self._load_profiles_data()
        profiles = data.get("profiles") or {}
        if name not in profiles:
            raise ValueError(f"Profile '{name}' does not exist")
        del profiles[name]
        data["profiles"] = profiles
        prev_active = data.get("active")
        if data.get("active") == name:
            data["active"] = next(iter(profiles), None)
        self._profiles_data = data
        self._save_profiles_data()
        return prev_active

    def clear_profiles(self) -> None:
        """Remove profiles file and clear in-memory cache."""
        self._profiles_data = {"active": None, "profiles": {}}
        if self.PROFILES_FILE.exists():
            self.PROFILES_FILE.unlink()

    def get_token(self) -> Optional[str]:
        """Get the stored API token."""
        # First check environment variable
        env_token = os.environ.get("GHL_API_TOKEN")
        if env_token:
            return env_token

        # Then active profile (token + location go together)
        active_name = self.get_active_profile_name()
        if active_name:
            profile = self.get_profile(active_name)
            if profile:
                return profile.api_token

        # Legacy: credentials file
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
        """Store the API token securely. Updates active profile if one is set."""
        active_name = self.get_active_profile_name()
        if active_name:
            profile = self.get_profile(active_name)
            if profile:
                self.add_or_update_profile(active_name, token, profile.location_id)
                return
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
        # Active profile (token + location go together)
        active_name = self.get_active_profile_name()
        if active_name:
            profile = self.get_profile(active_name)
            if profile:
                return profile.location_id
        return self.config.location_id


# Global config manager instance
config_manager = ConfigManager()
