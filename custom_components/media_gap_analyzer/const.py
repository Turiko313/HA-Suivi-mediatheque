"""Constants for Media Gap Analyzer."""

DOMAIN = "media_gap_analyzer"
PLATFORMS = ["sensor"]

# -- Config keys
CONF_TMDB_API_KEY = "tmdb_api_key"
CONF_LANGUAGE = "language"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MOVIES_PATHS = "movies_paths"
CONF_SERIES_PATHS = "series_paths"
CONF_ANIME_PATHS = "anime_paths"

# -- Media types
MEDIA_TYPE_MOVIES = "movies"
MEDIA_TYPE_SERIES = "series"
MEDIA_TYPE_ANIME = "anime"

# -- Defaults
DEFAULT_SCAN_INTERVAL = 24  # hours
DEFAULT_LANGUAGE = "fr"

# -- TMDb
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# -- Supported video file extensions
SUPPORTED_EXTENSIONS = {
    ".mkv", ".avi", ".mp4", ".m4v", ".wmv",
    ".flv", ".mov", ".ts", ".iso", ".img",
    ".mpg", ".mpeg", ".divx", ".ogm", ".webm",
}
