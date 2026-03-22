"""Gap analysis engine for Media Gap Analyzer.

Compares scanned media against TMDb collection / series data to find
missing movies and episodes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .scanner import ScannedMovie, ScannedSeries
from .tmdb_client import TMDbClient

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------------

@dataclass
class MissingMovie:
    collection_name: str
    title: str
    year: int | None = None
    tmdb_id: int = 0
    poster_path: str | None = None

    def as_dict(self) -> dict:
        return {
            "collection": self.collection_name,
            "title": self.title,
            "year": self.year,
            "tmdb_id": self.tmdb_id,
        }


@dataclass
class MissingEpisode:
    series_name: str
    season: int
    episode: int
    episode_title: str = ""
    tmdb_id: int = 0

    def as_dict(self) -> dict:
        return {
            "series": self.series_name,
            "season": self.season,
            "episode": self.episode,
            "episode_title": self.episode_title,
        }


@dataclass
class AnalysisResult:
    missing_movies: list[MissingMovie] = field(default_factory=list)
    missing_episodes: list[MissingEpisode] = field(default_factory=list)
    total_scanned: int = 0
    collections_found: int = 0
    series_analyzed: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _best_match(name: str, year: int | None, results: list[dict], date_key: str = "release_date", title_key: str = "title") -> dict | None:
    if not results:
        return None
    # Prefer exact year match
    if year:
        for r in results:
            r_year = (r.get(date_key) or "")[:4]
            if r_year == str(year) and _similarity(name, r.get(title_key, "")) > 0.6:
                return r
    # Fallback: best similarity
    best = max(results, key=lambda r: _similarity(name, r.get(title_key, "")))
    if _similarity(name, best.get(title_key, "")) > 0.5:
        return best
    return None


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

class MediaAnalyzer:
    """Finds gaps in media collections / series using TMDb data."""

    def __init__(self, client: TMDbClient) -> None:
        self._client = client

    async def analyze_movies(self, movies: list[ScannedMovie]) -> AnalysisResult:
        result = AnalysisResult(total_scanned=len(movies))
        # collection_id -> set of owned tmdb movie ids
        collections_owned: dict[int, set[int]] = {}
        # collection_id -> collection data
        collections_data: dict[int, dict] = {}

        for movie in movies:
            try:
                results = await self._client.search_movie(movie.title, movie.year)
                match = _best_match(movie.title, movie.year, results, "release_date", "title")
                if not match:
                    _LOGGER.debug("No TMDb match for movie: %s (%s)", movie.title, movie.year)
                    continue

                details = await self._client.get_movie(match["id"])
                coll = details.get("belongs_to_collection")
                if not coll:
                    continue  # standalone movie, no collection

                coll_id = coll["id"]
                if coll_id not in collections_data:
                    collections_data[coll_id] = await self._client.get_collection(coll_id)
                    collections_owned[coll_id] = set()

                collections_owned[coll_id].add(match["id"])
            except Exception:
                _LOGGER.exception("Error analyzing movie: %s", movie.title)

        # Now find gaps
        result.collections_found = len(collections_data)
        for coll_id, coll_data in collections_data.items():
            owned_ids = collections_owned[coll_id]
            for part in coll_data.get("parts", []):
                if part["id"] not in owned_ids:
                    year_str = (part.get("release_date") or "")[:4]
                    result.missing_movies.append(
                        MissingMovie(
                            collection_name=coll_data.get("name", "Unknown"),
                            title=part.get("title", "Unknown"),
                            year=int(year_str) if year_str else None,
                            tmdb_id=part["id"],
                            poster_path=part.get("poster_path"),
                        )
                    )

        result.missing_movies.sort(key=lambda m: (m.collection_name, m.year or 0))
        return result

    async def analyze_series(self, series_list: list[ScannedSeries]) -> AnalysisResult:
        result = AnalysisResult(total_scanned=len(series_list))

        for series in series_list:
            try:
                results = await self._client.search_tv(series.title, series.year)
                match = _best_match(series.title, series.year, results, "first_air_date", "name")
                if not match:
                    _LOGGER.debug("No TMDb match for series: %s", series.title)
                    continue

                result.series_analyzed += 1
                tv_id = match["id"]
                tv_data = await self._client.get_tv(tv_id)
                show_name = tv_data.get("name", series.title)

                # Build set of owned (season, episode)
                owned = {(ep.season, ep.episode) for ep in series.episodes}

                for season_info in tv_data.get("seasons", []):
                    season_num = season_info["season_number"]
                    if season_num == 0:
                        continue  # skip specials

                    try:
                        season_data = await self._client.get_tv_season(tv_id, season_num)
                    except Exception:
                        _LOGGER.warning("Could not fetch S%02d for %s", season_num, show_name)
                        continue

                    for ep_info in season_data.get("episodes", []):
                        ep_num = ep_info["episode_number"]
                        if (season_num, ep_num) not in owned:
                            result.missing_episodes.append(
                                MissingEpisode(
                                    series_name=show_name,
                                    season=season_num,
                                    episode=ep_num,
                                    episode_title=ep_info.get("name", ""),
                                    tmdb_id=tv_id,
                                )
                            )
            except Exception:
                _LOGGER.exception("Error analyzing series: %s", series.title)

        result.missing_episodes.sort(key=lambda e: (e.series_name, e.season, e.episode))
        return result
