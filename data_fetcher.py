"""
data_fetcher.py
---------------
Fetches NBA player stats from the balldontlie API and caches results locally.
"""

import requests
import json
import os
import time
from typing import Optional

BASE_URL  = "https://api.balldontlie.io/v1"
CACHE_DIR = "cache"
RATE_LIMIT_DELAY = 0.6


class NBADataFetcher:
    """
    Wraps the balldontlie v1 API with local JSON caching.
    Tries both header auth formats so the key always works.
    """

    def __init__(self, api_key: Optional[str] = None):
        raw = api_key or os.getenv("BALLDONTLIE_API_KEY", "")
        self.api_key = raw.strip()
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if self.api_key:
            # balldontlie v1 accepts the key directly in Authorization
            self.session.headers.update({"Authorization": self.api_key})
        os.makedirs(CACHE_DIR, exist_ok=True)

    # ── Connection test ───────────────────────────────────────────────────────
    def test_connection(self) -> tuple[bool, str]:
        """
        Quick check: hit /teams (lightest endpoint) to verify the key works.
        Returns (ok: bool, message: str).
        """
        try:
            url  = f"{BASE_URL}/teams"
            resp = self.session.get(url, params={"per_page": 1}, timeout=10)
            if resp.status_code == 200:
                return True, "Connected ✓"
            elif resp.status_code == 401:
                return False, (
                    "401 Unauthorized — your API key was rejected.\n"
                    "Check that you copied it correctly from balldontlie.io."
                )
            else:
                return False, f"Unexpected status {resp.status_code}"
        except Exception as exc:
            return False, f"Network error: {exc}"

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _cache_path(self, key: str) -> str:
        safe = key.replace("/", "_").replace("?", "_").replace("&", "_")
        return os.path.join(CACHE_DIR, f"{safe}.json")

    def _load_cache(self, key: str):
        path = self._cache_path(key)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return None

    def _save_cache(self, key: str, data) -> None:
        with open(self._cache_path(key), "w") as f:
            json.dump(data, f)

    def _get(self, endpoint: str, params: dict = None) -> dict:
        params = params or {}
        cache_key = endpoint + "_" + "_".join(f"{k}{v}" for k, v in sorted(params.items()))
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached

        url = f"{BASE_URL}/{endpoint}"
        time.sleep(RATE_LIMIT_DELAY)
        resp = self.session.get(url, params=params, timeout=15)

        # If bare-key 401, try Bearer format automatically
        if resp.status_code == 401 and self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            resp = self.session.get(url, params=params, timeout=15)

        resp.raise_for_status()
        data = resp.json()
        self._save_cache(cache_key, data)
        return data

    def _paginate(self, endpoint: str, params: dict = None, max_pages: int = 50) -> list:
        params = params or {}
        params["per_page"] = 100
        all_items = []
        cursor = None

        for _ in range(max_pages):
            if cursor:
                params["cursor"] = cursor
            data = self._get(endpoint, dict(params))
            all_items.extend(data.get("data", []))
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break

        return all_items

    # ── Public endpoints ──────────────────────────────────────────────────────
    def get_teams(self) -> list:
        return self._get("teams").get("data", [])

    def get_players(self, search: str = "", per_page: int = 25) -> list:
        params = {"per_page": per_page}
        if search:
            params["search"] = search
        return self._get("players", params).get("data", [])

    def get_season_stats(self, season: int, player_ids: list = None) -> list:
        params = {"seasons[]": season}
        if player_ids:
            base = {"seasons[]": season, "per_page": 100}
            all_stats = []
            for i in range(0, len(player_ids), 50):
                p = dict(base)
                p["player_ids[]"] = player_ids[i:i+50]
                all_stats.extend(self._paginate("stats", p))
            return all_stats
        return self._paginate("stats", params)

    def get_player_season_averages(self, season: int, player_ids: list) -> list:
        if not player_ids:
            return []
        params = {"season": season, "player_ids[]": player_ids}
        return self._get("season_averages", params).get("data", [])

    def get_games(self, season: int, team_ids: list = None) -> list:
        params = {"seasons[]": season}
        if team_ids:
            params["team_ids[]"] = team_ids
        return self._paginate("games", params)
