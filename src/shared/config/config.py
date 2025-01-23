import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        # Load environment variables
        load_dotenv()
        
        # Get config path from environment
        config_path = os.getenv('CONFIG_PATH', 'config/development/config.yaml')
        
        # Load YAML config
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        
        # Override with environment variables
        self._override_from_env()

    def _override_from_env(self) -> None:
        """Override configuration values with environment variables."""
        for key, value in os.environ.items():
            # Convert environment variables to nested dictionary structure
            current = self._config
            parts = key.lower().split('_')
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            current[parts[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        try:
            current = self._config
            for part in key.split('.'):
                current = current[part]
            return current
        except (KeyError, TypeError):
            return default

    @property
    def config(self) -> Dict[str, Any]:
        """Get entire configuration dictionary."""
        return self._config 