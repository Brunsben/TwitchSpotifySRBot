"""Internationalization support."""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in normal Python environment
        base_path = Path(__file__).parent.parent.parent
    
    return base_path / relative_path


class I18n:
    """Internationalization manager for multi-language support."""
    
    def __init__(self, locales_dir: Optional[Path] = None):
        """Initialize I18n manager.
        
        Args:
            locales_dir: Directory containing language JSON files
        """
        if locales_dir is None:
            # Use resource path for PyInstaller compatibility
            self.locales_dir = get_resource_path("locales")
        else:
            self.locales_dir = locales_dir
        
        self._translations: Dict[str, Any] = {}
        self._current_language = "de"
        
        # Don't create directory in PyInstaller mode
        if not hasattr(sys, '_MEIPASS'):
            self.locales_dir.mkdir(exist_ok=True)
    
    def load_language(self, language: str) -> bool:
        """Load language translations.
        
        Args:
            language: Language code (e.g., 'de', 'en')
            
        Returns:
            True if loaded successfully
        """
        lang_file = self.locales_dir / f"{language}.json"
        
        if not lang_file.exists():
            logger.warning(f"Language file not found: {lang_file}")
            return False
        
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
            
            self._current_language = language
            logger.info(f"Loaded language: {language}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading language {language}: {e}")
            return False
    
    def get(self, key: str, **kwargs) -> str:
        """Get translated string.
        
        Args:
            key: Translation key in dot notation (e.g., 'gui.title')
            **kwargs: Format parameters for the string
            
        Returns:
            Translated and formatted string
        """
        try:
            # Navigate nested dictionary
            keys = key.split(".")
            value = self._translations
            
            for k in keys:
                value = value[k]
            
            # Format if kwargs provided
            if kwargs:
                return value.format(**kwargs)
            
            return value
            
        except (KeyError, TypeError):
            logger.warning(f"Translation key not found: {key}")
            return f"[{key}]"
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages.
        
        Returns:
            Dictionary mapping language codes to display names
        """
        languages = {}
        
        for lang_file in self.locales_dir.glob("*.json"):
            lang_code = lang_file.stem
            
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Try to get language name from file
                    lang_name = data.get("meta", {}).get("name", lang_code)
                    languages[lang_code] = lang_name
            except Exception:
                languages[lang_code] = lang_code
        
        return languages
    
    @property
    def current_language(self) -> str:
        """Get current language code."""
        return self._current_language


# Global instance
_i18n: Optional[I18n] = None


def get_i18n() -> I18n:
    """Get global I18n instance."""
    global _i18n
    if _i18n is None:
        _i18n = I18n()
    return _i18n


def t(key: str, **kwargs) -> str:
    """Shortcut for translation.
    
    Args:
        key: Translation key
        **kwargs: Format parameters
        
    Returns:
        Translated string
    """
    return get_i18n().get(key, **kwargs)
