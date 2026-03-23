"""File-system scanner for Suivi Médiathèque.

Walks directories (local or SMB/CIFS), parses filenames and returns
structured media data.
"""
from __future__ import annotations

import logging
import os
import re
import stat as stat_mod
from dataclasses import dataclass, field

from .const import SUPPORTED_EXTENSIONS

_LOGGER = logging.getLogger(__name__)

try:
    import smbclient as _smb

    _HAS_SMB = True
except ImportError:
    _smb = None  # type: ignore[assignment]
    _HAS_SMB = False


# ---------------------------------------------------------------------------
# File-system abstraction (local + SMB)
# ---------------------------------------------------------------------------


class _FileOps:
    """Unified file operations for local paths and SMB/CIFS shares."""

    def __init__(self, nas_config: dict | None = None) -> None:
        self._nas = nas_config or {}
        self._smb_registered = False

    # -- internal ------------------------------------------------------------

    def _ensure_smb(self) -> None:
        if self._smb_registered:
            return
        if not _HAS_SMB:
            raise RuntimeError(
                "Le package smbprotocol est requis pour accéder à un NAS. "
                "Il devrait être installé automatiquement par Home Assistant."
            )
        server = self._nas.get("server", "")
        if not server:
            return
        _smb.register_session(
            server,
            username=self._nas.get("username", ""),
            password=self._nas.get("password", ""),
        )
        self._smb_registered = True

    # -- path helpers --------------------------------------------------------

    def resolve_path(self, raw_path: str) -> str:
        """Convert user-entered path to a usable path.

        - Absolute local path (/media/films) -> used as-is
        - UNC path (//server/share) -> used as-is (SMB)
        - Relative path (Films) + NAS configured -> //server/Films
        """
        raw_path = raw_path.strip()
        if raw_path.startswith("/") and not raw_path.startswith("//"):
            return raw_path  # local absolute path
        if raw_path.startswith("//") or raw_path.startswith("\\\\"):
            self._ensure_smb()
            return raw_path.replace("\\", "/")
        server = self._nas.get("server")
        if server:
            self._ensure_smb()
            return f"//{server}/{raw_path}"
        return raw_path  # no NAS, treat as local

    @staticmethod
    def is_smb(path: str) -> bool:
        return path.startswith("//")

    def isdir(self, path: str) -> bool:
        if self.is_smb(path):
            try:
                return stat_mod.S_ISDIR(_smb.stat(path).st_mode)
            except Exception:
                return False
        return os.path.isdir(path)

    def listdir(self, path: str) -> list[str]:
        if self.is_smb(path):
            return _smb.listdir(path)
        return os.listdir(path)

    def walk(self, path: str):
        if self.is_smb(path):
            for dirpath, dirnames, filenames in _smb.walk(path):
                yield dirpath.replace("\\", "/"), dirnames, filenames
        else:
            yield from os.walk(path)

    def join(self, base: str, *parts: str) -> str:
        if self.is_smb(base):
            result = base.rstrip("/")
            for p in parts:
                result = result + "/" + p.strip("/")
            return result
        return os.path.join(base, *parts)

    def relpath(self, path: str, base: str) -> str:
        if self.is_smb(path):
            path_n = path.replace("\\", "/")
            base_n = base.replace("\\", "/").rstrip("/")
            if path_n.startswith(base_n):
                rel = path_n[len(base_n) :].lstrip("/")
                return rel if rel else "."
            return path_n
        return os.path.relpath(path, base)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ScannedMovie:
    title: str
    year: int | None = None
    file_path: str = ""

@dataclass
class ScannedEpisode:
    season: int = 0
    episode: int = 0
    file_path: str = ""

@dataclass
class ScannedSeries:
    title: str
    year: int | None = None
    episodes: list[ScannedEpisode] = field(default_factory=list)

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

_RE_MOVIE_PAREN_YEAR = re.compile(r"^(.+?)\s*\((\d{4})\)")
_RE_MOVIE_DOT_YEAR = re.compile(r"^(.+?)[\.\s_-]+(\d{4})[\.\s_-]")
_RE_EPISODE = re.compile(r"[Ss](\d{1,2})[Ee](\d{1,3})")
_RE_EPISODE_ALT = re.compile(r"(\d{1,2})x(\d{1,3})")
_RE_SEASON_DIR = re.compile(r"[Ss](?:aison|eason)?\s*(\d{1,2})", re.IGNORECASE)
_RE_JUNK = re.compile(
    r"[\.\s_-]*(720p|1080p|2160p|4[Kk]|BluRay|BDRip|BRRip|DVDRip|WEBRip|"
    r"WEB-DL|HDTV|PROPER|REPACK|REMUX|x264|x265|HEVC|AAC|DTS|AC3|MULTI|"
    r"TRUEFRENCH|FRENCH|VOSTFR|SUBFRENCH|MULTi).*$",
    re.IGNORECASE,
)


def _clean_name(raw: str) -> str:
    name = _RE_JUNK.sub("", raw)
    name = re.sub(r"[\._]", " ", name)
    name = re.sub(r"\s{2,}", " ", name)
    return name.strip(" -")


def _is_video(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in SUPPORTED_EXTENSIONS


def _parse_movie_name(name: str) -> tuple[str, int | None]:
    m = _RE_MOVIE_PAREN_YEAR.match(name)
    if m:
        return _clean_name(m.group(1)), int(m.group(2))
    m = _RE_MOVIE_DOT_YEAR.match(name)
    if m:
        return _clean_name(m.group(1)), int(m.group(2))
    return _clean_name(name), None


def _parse_episode(filename: str, fallback_season: int | None = None) -> tuple[int, int] | None:
    m = _RE_EPISODE.search(filename)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = _RE_EPISODE_ALT.search(filename)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


# ---------------------------------------------------------------------------
# Public scanner functions (blocking - run via executor)
# ---------------------------------------------------------------------------

def scan_movies(paths: str | list[str], nas_config: dict | None = None) -> list[ScannedMovie]:
    fs = _FileOps(nas_config)
    movies: list[ScannedMovie] = []
    if isinstance(paths, str):
        path_list = [p.strip() for p in paths.split(",") if p.strip()]
    else:
        path_list = [p.strip() for p in paths if p.strip()]
    for raw in path_list:
        base = fs.resolve_path(raw)
        if not fs.isdir(base):
            _LOGGER.warning("Movies path does not exist: %s", base)
            continue
        for entry in fs.listdir(base):
            full = fs.join(base, entry)
            if fs.isdir(full):
                # folder-per-movie: use folder name
                title, year = _parse_movie_name(entry)
                has_video = any(_is_video(f) for f in fs.listdir(full))
                if has_video:
                    movies.append(ScannedMovie(title=title, year=year, file_path=full))
            elif _is_video(entry):
                name = os.path.splitext(entry)[0]
                title, year = _parse_movie_name(name)
                movies.append(ScannedMovie(title=title, year=year, file_path=full))
    _LOGGER.info("Scanned %d movies across %d paths", len(movies), len(path_list))
    return movies


def scan_series(paths: str | list[str], nas_config: dict | None = None) -> list[ScannedSeries]:
    fs = _FileOps(nas_config)
    series_map: dict[str, ScannedSeries] = {}
    if isinstance(paths, str):
        path_list = [p.strip() for p in paths.split(",") if p.strip()]
    else:
        path_list = [p.strip() for p in paths if p.strip()]
    for raw in path_list:
        base = fs.resolve_path(raw)
        if not fs.isdir(base):
            _LOGGER.warning("Series path does not exist: %s", base)
            continue
        for show_dir in sorted(fs.listdir(base)):
            show_path = fs.join(base, show_dir)
            if not fs.isdir(show_path):
                continue
            title, year = _parse_movie_name(show_dir)
            if title in series_map:
                series = series_map[title]
            else:
                series = ScannedSeries(title=title, year=year)
                series_map[title] = series

            # Walk the show directory tree
            for dirpath, _dirnames, filenames in fs.walk(show_path):
                # Detect season from parent folder name
                rel = fs.relpath(dirpath, show_path)
                folder_season: int | None = None
                sm = _RE_SEASON_DIR.search(rel)
                if sm:
                    folder_season = int(sm.group(1))

                for fname in filenames:
                    if not _is_video(fname):
                        continue
                    ep = _parse_episode(fname, folder_season)
                    if ep:
                        season_num, ep_num = ep
                        series.episodes.append(
                            ScannedEpisode(
                                season=season_num,
                                episode=ep_num,
                                file_path=fs.join(dirpath, fname),
                            )
                        )
                    elif folder_season is not None:
                        # file without SxxExx pattern but inside a season dir
                        _LOGGER.debug("Could not parse episode from: %s", fname)

    result = list(series_map.values())
    _LOGGER.info("Scanned %d series across %d paths", len(result), len(path_list))
    return result
