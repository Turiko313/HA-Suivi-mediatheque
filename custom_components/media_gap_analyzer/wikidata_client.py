"""Wikidata client for Suivi Médiathèque.

Falls back to Wikidata SPARQL + entity API when no TMDb key is configured,
allowing movie collection / franchise gap detection without any API key.
No authentication required.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# Wikidata property IDs
_P_INSTANCE_OF = "P31"
_P_PART_OF_SERIES = "P179"
_P_PUB_DATE = "P577"

# Acceptable "instance of" QIDs that represent a film
_FILM_QIDS = {
    "Q11424",     # film
    "Q24862",     # short film
    "Q506240",    # television film
    "Q202866",    # animated film
    "Q226730",    # 3D film
    "Q5765569",   # computer-animated film
    "Q17013749",  # live-action film
}

# Quick description-level hints (cheaper than fetching entities)
_FILM_DESC_HINTS = {"film", "movie", "película", "filme"}


class WikidataClient:
    """Async Wikidata client — no API key needed."""

    _API = "https://www.wikidata.org/w/api.php"
    _SPARQL = "https://query.wikidata.org/sparql"
    _UA = (
        "SuiviMediatheque/1.2 "
        "(Home Assistant integration; "
        "https://github.com/Turiko313/HA-Suivi-mediatheque)"
    )

    def __init__(self, hass: HomeAssistant, language: str = "fr") -> None:
        self._hass = hass
        self._lang = language
        self._session = async_get_clientsession(hass)
        self._cache: dict[str, Any] = {}
        self._last_sparql: float = 0.0

    # ----- low-level helpers ------------------------------------------------

    async def _api(self, params: dict[str, Any]) -> dict[str, Any]:
        """Call the Wikidata MediaWiki API (wbsearchentities, wbgetentities)."""
        params["format"] = "json"
        cache_key = str(sorted(params.items()))
        if cache_key in self._cache:
            return self._cache[cache_key]
        headers = {"User-Agent": self._UA}
        try:
            async with self._session.get(
                self._API, params=params, headers=headers, timeout=20
            ) as resp:
                resp.raise_for_status()
                data: dict[str, Any] = await resp.json()
                self._cache[cache_key] = data
                return data
        except Exception as exc:
            _LOGGER.error("Wikidata API error: %s", exc)
            raise

    async def _sparql(self, query: str) -> list[dict[str, Any]]:
        """Execute a SPARQL query on the Wikidata endpoint (rate-limited)."""
        cache_key = f"sparql|{query}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        # Wikidata asks ≤ 1 req/s on the SPARQL endpoint
        now = asyncio.get_event_loop().time()
        wait = 1.1 - (now - self._last_sparql)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_sparql = asyncio.get_event_loop().time()

        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": self._UA,
        }
        try:
            async with self._session.get(
                self._SPARQL,
                params={"query": query},
                headers=headers,
                timeout=30,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                bindings: list[dict[str, Any]] = data.get("results", {}).get(
                    "bindings", []
                )
                self._cache[cache_key] = bindings
                return bindings
        except Exception as exc:
            _LOGGER.error("Wikidata SPARQL error: %s", exc)
            raise

    async def _get_entities(self, qids: list[str]) -> dict[str, Any]:
        """Batch-fetch entity data (claims + labels)."""
        if not qids:
            return {}
        data = await self._api(
            {
                "action": "wbgetentities",
                "ids": "|".join(qids),
                "props": "claims|labels",
                "languages": f"{self._lang}|en",
            }
        )
        return data.get("entities", {})

    # ----- parsing helpers --------------------------------------------------

    @staticmethod
    def _is_film(claims: dict) -> bool:
        """Check P31 (instance of) for known film types."""
        for claim in claims.get(_P_INSTANCE_OF, []):
            qid = (
                claim.get("mainsnak", {})
                .get("datavalue", {})
                .get("value", {})
                .get("id", "")
            )
            if qid in _FILM_QIDS:
                return True
        return False

    def _label(self, entity: dict) -> str:
        """Best label in preferred language, fallback to English."""
        labels = entity.get("labels", {})
        for lang in (self._lang, "en"):
            if lang in labels:
                return labels[lang]["value"]
        if labels:
            return next(iter(labels.values()))["value"]
        return "Unknown"

    @staticmethod
    def _year_from_claims(claims: dict) -> int | None:
        """Extract publication year from P577."""
        for claim in claims.get(_P_PUB_DATE, []):
            time_val = (
                claim.get("mainsnak", {})
                .get("datavalue", {})
                .get("value", {})
                .get("time", "")
            )
            if time_val:
                try:
                    return int(time_val[1:5])  # "+2010-07-…" -> 2010
                except (ValueError, IndexError):
                    pass
        return None

    # ----- public API -------------------------------------------------------

    async def search_movie(
        self, name: str, year: int | None = None
    ) -> dict[str, Any] | None:
        """Find a movie in Wikidata.

        Returns ``{qid, label, year, series_qid, series_label}`` or *None*.
        """
        search_term = f"{name} {year}" if year else name

        data = await self._api(
            {
                "action": "wbsearchentities",
                "search": search_term,
                "language": self._lang,
                "uselang": self._lang,
                "type": "item",
                "limit": 10,
            }
        )
        candidates = data.get("search", [])

        # Fallback: retry in English
        if not candidates and self._lang != "en":
            data = await self._api(
                {
                    "action": "wbsearchentities",
                    "search": search_term,
                    "language": "en",
                    "uselang": "en",
                    "type": "item",
                    "limit": 10,
                }
            )
            candidates = data.get("search", [])

        if not candidates:
            return None

        # Quick description filter — cheaper than fetching full entities
        film_candidates = [
            c
            for c in candidates
            if any(h in c.get("description", "").lower() for h in _FILM_DESC_HINTS)
        ]
        if not film_candidates:
            film_candidates = candidates[:5]

        # Fetch entity details
        qids = [c["id"] for c in film_candidates[:6]]
        entities = await self._get_entities(qids)

        best: dict[str, Any] | None = None
        for qid in qids:
            entity = entities.get(qid)
            if not entity:
                continue
            claims = entity.get("claims", {})
            if not self._is_film(claims):
                continue

            info: dict[str, Any] = {
                "qid": qid,
                "label": self._label(entity),
                "year": self._year_from_claims(claims),
                "series_qid": None,
                "series_label": None,
            }

            # Check P179 (part of series / collection)
            series_claims = claims.get(_P_PART_OF_SERIES, [])
            if series_claims:
                s_qid = (
                    series_claims[0]
                    .get("mainsnak", {})
                    .get("datavalue", {})
                    .get("value", {})
                    .get("id")
                )
                if s_qid:
                    info["series_qid"] = s_qid

            # Exact year match → perfect
            if year and info["year"] == year:
                best = info
                break
            # Prefer entries that belong to a collection
            if best is None or (
                info["series_qid"] and not best.get("series_qid")
            ):
                best = info

        # Resolve series label
        if best and best["series_qid"]:
            s_entities = await self._get_entities([best["series_qid"]])
            s_entity = s_entities.get(best["series_qid"])
            if s_entity:
                best["series_label"] = self._label(s_entity)

        return best

    async def get_collection_movies(
        self, series_qid: str
    ) -> list[dict[str, Any]]:
        """Return every film belonging to a franchise / collection."""
        # VALUES clause covers the common film sub-types without slow P279*
        film_values = " ".join(f"wd:{q}" for q in _FILM_QIDS)
        query = (
            "SELECT ?item ?itemLabel ?date WHERE { "
            f"?item wdt:P179 wd:{series_qid} . "
            f"VALUES ?type {{ {film_values} }} "
            "?item wdt:P31 ?type . "
            "OPTIONAL { ?item wdt:P577 ?date } "
            "SERVICE wikibase:label { bd:serviceParam wikibase:language "
            f'"{self._lang},en" }} '
            "} ORDER BY ?date"
        )
        bindings = await self._sparql(query)

        movies: list[dict[str, Any]] = []
        seen: set[str] = set()
        for b in bindings:
            qid = b["item"]["value"].rsplit("/", 1)[-1]
            if qid in seen:
                continue
            seen.add(qid)
            yr: int | None = None
            date_val = b.get("date", {}).get("value", "")
            if date_val:
                try:
                    yr = int(date_val[:4])
                except (ValueError, IndexError):
                    pass
            movies.append(
                {
                    "qid": qid,
                    "label": b.get("itemLabel", {}).get("value", "Unknown"),
                    "year": yr,
                }
            )
        return movies

    def clear_cache(self) -> None:
        """Release cached results."""
        self._cache.clear()
