"""File-system scanner for Media Gap Analyzer.

Walks directories, parses filenames and returns structured media data.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

from .const import SUPPORTED_EXTENSIONS

_LOGGER = logging.getLogger(__name__)

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

def scan_movies(paths_csv: str) -> list[ScannedMovie]:
    movies: list[ScannedMovie] = []
    paths = [p.strip() for p in paths_csv.split(",") if p.strip()]
    for base in paths:
        if not os.path.isdir(base):
            _LOGGER.warning("Movies path does not exist: %s", base)
            continue
        for entry in os.listdir(base):
            full = os.path.join(base, entry)
            if os.path.isdir(full):
                # folder-per-movie: use folder name
                title, year = _parse_movie_name(entry)
                has_video = any(_is_video(f) for f in os.listdir(full) if os.path.isfile(os.path.join(full, f)))
                if has_video:
                    movies.append(ScannedMovie(title=title, year=year, file_path=full))
            elif os.path.isfile(full) and _is_video(entry):
                name = os.path.splitext(entry)[0]
                title, year = _parse_movie_name(name)
                movies.append(ScannedMovie(title=title, year=year, file_path=full))
    _LOGGER.info("Scanned %d movies across %d paths", len(movies), len(paths))
    return movies


def scan_series(paths_csv: str) -> list[ScannedSeries]:
    series_map: dict[str, ScannedSeries] = {}
    paths = [p.strip() for p in paths_csv.split(",") if p.strip()]
    for base in paths:
        if not os.path.isdir(base):
            _LOGGER.warning("Series path does not exist: %s", base)
            continue
        for show_dir in sorted(os.listdir(base)):
            show_path = os.path.join(base, show_dir)
            if not os.path.isdir(show_path):
                continue
            title, year = _parse_movie_name(show_dir)
            if title in series_map:
                series = series_map[title]
            else:
                series = ScannedSeries(title=title, year=year)
                series_map[title] = series

            # Walk the show directory tree
            for dirpath, _dirnames, filenames in os.walk(show_path):
                # Detect season from parent folder name
                rel = os.path.relpath(dirpath, show_path)
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
                                file_path=os.path.join(dirpath, fname),
                            )
                        )
                    elif folder_season is not None:
                        # file without SxxExx pattern but inside a season dir
                        _LOGGER.debug("Could not parse episode from: %s", fname)

    result = list(series_map.values())
    _LOGGER.info("Scanned %d series across %d paths", len(result), len(paths))
    return result
