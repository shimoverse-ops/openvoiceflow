#!/usr/bin/env python3
"""Build a private, local OpenVoiceFlow analytics dashboard.

The collector uses the authenticated GitHub CLI and, when available, the local
Vercel CLI token. Credentials are never copied into the generated snapshot or
HTML. It combines repository traffic, release-asset request counters, CI
activity, aggregate website analytics, and the app's own aggregate install and
usage counters (opt-out, on by default since 0.5.8 — see PRIVACY.md §7).

Everything here is aggregate. No source returns a per-user or per-device row,
and the app telemetry endpoint is token-gated precisely because the public
leaderboard hides the population size on purpose.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from zoneinfo import ZoneInfo

REPOSITORY = "shimoverse/openvoiceflow"
VERCEL_PROJECT = "openvoiceflow"
TIMEZONE = "America/Los_Angeles"
SCHEMA_VERSION = 1
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".analytics-dashboard" / "index.html"
DEFAULT_SNAPSHOT = ROOT / ".analytics-dashboard" / "snapshot.json"
VERCEL_AUTH = Path.home() / "Library/Application Support/com.vercel.cli/auth.json"
# Aggregate install + in-app usage counters (api/analytics/stats.js). Private:
# the public leaderboard hides the population size on purpose, so this needs
# the deployment's ANALYTICS_STATS_TOKEN.
APP_STATS_URL = "https://openvoiceflow.com/api/analytics/stats"
APP_STATS_TOKEN_ENV = "OVF_ANALYTICS_STATS_TOKEN"


class AnalyticsError(RuntimeError):
    """A source could not be collected without exposing credential details."""


def _utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _require_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _gh_api(path: str, accept: Optional[str] = None) -> Any:
    command = ["gh", "api", path]
    if accept:
        command.extend(["-H", f"Accept: {accept}"])
    try:
        result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise AnalyticsError("GitHub analytics request failed; confirm `gh auth status` succeeds") from exc
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AnalyticsError("GitHub returned an unreadable analytics response") from exc


def _gh_paginate(path: str, accept: Optional[str] = None, per_page: int = 100) -> List[Any]:
    separator = "&" if "?" in path else "?"
    items: List[Any] = []
    for page in range(1, 11):
        payload = _gh_api(f"{path}{separator}per_page={per_page}&page={page}", accept=accept)
        if not isinstance(payload, list):
            raise AnalyticsError("GitHub pagination returned an unexpected response")
        items.extend(payload)
        if len(payload) < per_page:
            break
    return items


def _gh_paginate_key(path: str, key: str, per_page: int = 100) -> List[Dict[str, Any]]:
    """Collect a GitHub paginated object response without truncating busy windows."""
    separator = "&" if "?" in path else "?"
    items: List[Dict[str, Any]] = []
    for page in range(1, 51):
        payload = _gh_api(f"{path}{separator}per_page={per_page}&page={page}")
        page_items = payload.get(key) if isinstance(payload, dict) else None
        if not isinstance(page_items, list):
            raise AnalyticsError(f"GitHub pagination returned an unexpected `{key}` response")
        items.extend(page_items)
        if len(page_items) < per_page:
            break
    return items


def _workflow_checkout_count(run_id: int) -> int:
    jobs = _gh_paginate_key(f"repos/{REPOSITORY}/actions/runs/{run_id}/jobs", "jobs")
    count = 0
    for job in jobs:
        steps = job.get("steps") or []
        if any("checkout" in str(step.get("name", "")).lower() and step.get("conclusion") != "skipped" for step in steps):
            count += 1
    return count


def collect_github(now: Optional[datetime] = None) -> Dict[str, Any]:
    """Collect GitHub's rolling traffic aggregates and corroborating signals."""
    now = now or datetime.now(timezone.utc)
    repository = _gh_api(f"repos/{REPOSITORY}")
    views = _gh_api(f"repos/{REPOSITORY}/traffic/views?per=day")
    clones = _gh_api(f"repos/{REPOSITORY}/traffic/clones?per=day")
    referrers = _gh_api(f"repos/{REPOSITORY}/traffic/popular/referrers")
    paths = _gh_api(f"repos/{REPOSITORY}/traffic/popular/paths")
    releases = _gh_paginate(f"repos/{REPOSITORY}/releases")

    traffic_days = [item.get("timestamp") for item in clones.get("clones", []) if item.get("timestamp")]
    oldest = min((_parse_datetime(item) for item in traffic_days), default=now - timedelta(days=13))
    created_filter = urllib.parse.quote(f">={oldest.date().isoformat()}")
    runs = _gh_paginate_key(
        f"repos/{REPOSITORY}/actions/runs?created={created_filter}",
        "workflow_runs",
    )
    workflow_runs: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_workflow_checkout_count, int(run["id"])): run for run in runs}
        for future in as_completed(futures):
            run = futures[future]
            checkout_jobs = future.result()
            workflow_runs.append(
                {
                    "id": run["id"],
                    "created_at": run.get("created_at"),
                    "name": run.get("name"),
                    "event": run.get("event"),
                    "checkout_jobs": checkout_jobs,
                }
            )

    stargazers_raw = _gh_paginate(
        f"repos/{REPOSITORY}/stargazers",
        accept="application/vnd.github.star+json",
    )
    stargazers: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_gh_api, f"users/{item['user']['login']}"): item
            for item in stargazers_raw
            if item.get("user", {}).get("login")
        }
        for future in as_completed(futures):
            item = futures[future]
            try:
                user = future.result()
            except AnalyticsError:
                continue
            stargazers.append(
                {
                    "login": user.get("login"),
                    "starred_at": item.get("starred_at"),
                    "created_at": user.get("created_at"),
                    "public_repos": user.get("public_repos", 0),
                    "followers": user.get("followers", 0),
                }
            )

    return {
        "repository": {
            "full_name": repository.get("full_name", REPOSITORY),
            "html_url": repository.get("html_url", f"https://github.com/{REPOSITORY}"),
            "stargazers_count": repository.get("stargazers_count", 0),
            "forks_count": repository.get("forks_count", 0),
            "open_issues_and_pull_requests_count": repository.get("open_issues_count", 0),
        },
        "views": views,
        "clones": clones,
        "popular_referrers": referrers,
        "popular_paths": paths,
        "releases": releases,
        "workflow_runs": workflow_runs,
        "stargazers": stargazers,
    }


def _vercel_token() -> str:
    token = os.environ.get("VERCEL_TOKEN", "").strip()
    if token:
        return token
    try:
        payload = json.loads(VERCEL_AUTH.read_text(encoding="utf-8"))
        token = str(payload.get("token", "")).strip()
    except (OSError, json.JSONDecodeError):
        token = ""
    if not token:
        raise AnalyticsError("Vercel analytics unavailable; run `vercel login` first")
    return token


def _vercel_json(url: str, token: str) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "OpenVoiceFlow-analytics-dashboard/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        status = getattr(exc, "code", "network")
        raise AnalyticsError(f"Vercel analytics request failed ({status})") from exc


def _discover_vercel_project(token: str, project_name: str) -> Tuple[Optional[str], str]:
    teams_payload = _vercel_json("https://api.vercel.com/v2/teams?limit=100", token)
    teams = teams_payload.get("teams", [])
    scopes: List[Optional[str]] = [None]
    scopes.extend(str(team["id"]) for team in teams if team.get("id"))
    for team_id in scopes:
        query = urllib.parse.urlencode({"teamId": team_id}) if team_id else ""
        try:
            suffix = f"?{query}" if query else ""
            project = _vercel_json(f"https://api.vercel.com/v9/projects/{project_name}{suffix}", token)
        except AnalyticsError:
            continue
        project_id = project.get("id")
        if project_id:
            return team_id, str(project_id)
    raise AnalyticsError(f"Vercel project `{project_name}` was not found in the authenticated account or teams")


def collect_vercel(
    now: Optional[datetime] = None,
    days: int = 30,
    project_name: str = VERCEL_PROJECT,
) -> Dict[str, Any]:
    """Collect aggregate Vercel Web Analytics without persisting its token."""
    now = now or datetime.now(timezone.utc)
    token = _vercel_token()
    team_id, project_id = _discover_vercel_project(token, project_name)
    local_now = now.astimezone(ZoneInfo(TIMEZONE))
    local_start = (local_now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    start = _utc_iso(local_start)
    end = _utc_iso(local_now)
    common = {
        "projectId": project_id,
        "since": start,
        "until": end,
    }
    if team_id:
        common["teamId"] = team_id
    base = "https://api.vercel.com/v1/query/web-analytics/"

    def request(endpoint: str, extra: Optional[Dict[str, str]] = None) -> Any:
        query = dict(common)
        query.update(extra or {})
        payload = _vercel_json(base + endpoint + "?" + urllib.parse.urlencode(query), token)
        if payload.get("version") != 1 or "data" not in payload:
            raise AnalyticsError("Vercel Web Analytics returned an unexpected response schema")
        return payload["data"]

    overview = request("visits/count")
    if not isinstance(overview, dict):
        raise AnalyticsError("Vercel Web Analytics count response was not an object")
    pageviews = _require_int(overview.get("pageviews"), "vercel pageviews")
    visitors = _require_int(overview.get("visitors"), "vercel visitors")

    dimensions = {
        "path": ("visits/aggregate", "requestPath"),
        "referrer": ("visits/aggregate", "referrerHostname"),
        "country": ("visits/aggregate", "country"),
        "device_type": ("visits/aggregate", "deviceType"),
        "os_name": ("visits/aggregate", "osName"),
        "client_name": ("visits/aggregate", "browserName"),
        "event_name": ("events/aggregate", "eventName"),
    }

    def normalize(rows: Any, dimension: str, event: bool = False) -> List[Dict[str, Any]]:
        if not isinstance(rows, list):
            raise AnalyticsError(f"Vercel `{dimension}` aggregate response was not a list")
        normalized = []
        for row in rows:
            if not isinstance(row, dict) or dimension not in row:
                raise AnalyticsError(f"Vercel `{dimension}` aggregate row had an unexpected shape")
            total_key = "count" if event else "pageviews"
            normalized.append(
                {
                    "key": str(row[dimension]),
                    "total": _require_int(row.get(total_key), f"vercel {dimension}.{total_key}"),
                    "visitors": _require_int(row.get("visitors"), f"vercel {dimension}.visitors"),
                }
            )
        return normalized

    stats: Dict[str, List[Dict[str, Any]]] = {}
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {
            executor.submit(request, endpoint, {"by": dimension, "limit": "25"}): (stat_type, dimension, endpoint)
            for stat_type, (endpoint, dimension) in dimensions.items()
        }
        for future in as_completed(futures):
            stat_type, dimension, endpoint = futures[future]
            stats[stat_type] = normalize(future.result(), dimension, event=endpoint.startswith("events/"))

    return {
        "available": True,
        "window": {"from": start, "to": end, "days": days, "timezone": TIMEZONE},
        "overview": {"pageviews": pageviews, "visitors": visitors},
        "stats": stats,
    }


def collect_app_telemetry(
    now: Optional[datetime] = None,
    days: int = 30,
    base_url: str = APP_STATS_URL,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """Collect aggregate install + in-app usage counters from the private API.

    The token is read from the environment and never written to the snapshot or
    the HTML. Without one the dashboard still builds — the app sections just
    report themselves unavailable, the same way the website sections do when
    `vercel login` has not been run.
    """
    token = token or os.environ.get(APP_STATS_TOKEN_ENV, "")
    if not token:
        raise AnalyticsError(
            f"App telemetry unavailable; set {APP_STATS_TOKEN_ENV} to the value configured on the deployment"
        )
    query = urllib.parse.urlencode({"activeDays": str(days), "recentDays": "7"})
    request = urllib.request.Request(
        f"{base_url}?{query}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Deliberately does not echo the response body — it is an authenticated
        # endpoint and the error text is not worth risking in a shared log.
        raise AnalyticsError(f"App telemetry request rejected (HTTP {exc.code})") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise AnalyticsError("App telemetry request failed") from exc

    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise AnalyticsError("App telemetry returned an unexpected response schema")
    totals = payload.get("totals")
    if not isinstance(totals, dict):
        raise AnalyticsError("App telemetry response had no totals")
    return {
        "available": True,
        "window": payload.get("window", {}),
        "totals": {
            "installs": _require_int(totals.get("installs"), "app totals.installs"),
            "active_recent": _require_int(totals.get("activeRecent"), "app totals.activeRecent"),
            "active_window": _require_int(totals.get("activeWindow"), "app totals.activeWindow"),
            "new_window": _require_int(totals.get("newWindow"), "app totals.newWindow"),
            "countries": _require_int(totals.get("countries"), "app totals.countries"),
        },
        "versions": _rank_payload(payload.get("versions"), "versions"),
        "countries": _rank_payload(payload.get("countries"), "countries"),
        "features": payload.get("features", {}),
        "events": _rank_payload(payload.get("events"), "events"),
    }


def _rank_payload(rows: Any, label: str) -> List[Dict[str, Any]]:
    """Normalize an API ranking into the {key,total} shape the renderer uses."""
    if not isinstance(rows, list):
        raise AnalyticsError(f"App telemetry `{label}` was not a list")
    normalized = []
    for row in rows:
        if not isinstance(row, dict) or "key" not in row:
            raise AnalyticsError(f"App telemetry `{label}` row had an unexpected shape")
        normalized.append(
            {
                "key": str(row["key"]),
                "total": _require_int(row.get("total"), f"app {label}.total"),
                "visitors": _require_int(row["devices"], f"app {label}.devices")
                if isinstance(row.get("devices"), int)
                else None,
            }
        )
    return normalized


def estimate_external_interest(
    github: Dict[str, Any],
    owner_logins: Set[str],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Return only defensible lower-bound interest signals, never a user claim."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)
    owners = {value.lower() for value in owner_logins}
    high_confidence = 0
    low_signal = 0
    considered = 0
    for star in github.get("stargazers", []):
        login = str(star.get("login", "")).lower()
        if not login or login in owners or not star.get("starred_at") or not star.get("created_at"):
            continue
        starred_at = _parse_datetime(star["starred_at"])
        if starred_at < cutoff:
            continue
        considered += 1
        account_age = starred_at - _parse_datetime(star["created_at"])
        public_repos = int(star.get("public_repos", 0) or 0)
        followers = int(star.get("followers", 0) or 0)
        established = account_age >= timedelta(days=180) and (public_repos >= 2 or followers >= 1)
        if established:
            high_confidence += 1
        else:
            low_signal += 1

    return {
        "verified_installs": None,
        "active_users": None,
        "exact_real_users": None,
        "possible_external_cloners": None,
        "high_confidence_external_interest": high_confidence,
        "low_signal_recent_stars": low_signal,
        "recent_external_stars_considered": considered,
        "label": "High-confidence external interest — not installs or active users",
        "method": (
            "Recent non-owner stargazers whose accounts were at least 180 days old and had "
            "at least two public repositories or one follower. This is a conservative engagement "
            "signal, not proof that they downloaded or used the app."
        ),
    }


def _release_assets(releases: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assets: List[Dict[str, Any]] = []
    for release in releases:
        for asset in release.get("assets", []):
            name = str(asset.get("name", ""))
            if not name.lower().endswith((".dmg", ".zip", ".pkg")):
                continue
            assets.append(
                {
                    "tag": release.get("tag_name"),
                    "name": name,
                    "requests": _require_int(asset.get("download_count", 0), "release asset download_count"),
                    "published_at": release.get("published_at"),
                    "scope": "cumulative",
                }
            )
    return sorted(assets, key=lambda item: str(item.get("published_at") or ""), reverse=True)


def build_snapshot(
    github: Dict[str, Any],
    vercel: Dict[str, Any],
    now: Optional[datetime] = None,
    owner_logins: Optional[Set[str]] = None,
    app: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Normalize provider responses into the dashboard's stable data contract."""
    now = now or datetime.now(timezone.utc)
    owner_logins = owner_logins or {REPOSITORY.split("/", 1)[0]}
    clone_count = _require_int(github.get("clones", {}).get("count"), "clones.count")
    clone_uniques = _require_int(github.get("clones", {}).get("uniques"), "clones.uniques")
    view_count = _require_int(github.get("views", {}).get("count"), "views.count")
    view_uniques = _require_int(github.get("views", {}).get("uniques"), "views.uniques")
    checkout_jobs = sum(_require_int(run.get("checkout_jobs", 0), "workflow checkout_jobs") for run in github.get("workflow_runs", []))
    estimate = estimate_external_interest(github, owner_logins=owner_logins, now=now)

    app = app or {"available": False, "error": "App telemetry unavailable"}
    if app.get("available"):
        # The app does report installs now (opt-out, aggregate — see
        # UsageCounters and PRIVACY.md §7), so the honest answer is no longer
        # "unknown". It is still a count of installs that opted in, not of
        # people: one person with two Macs is two.
        totals = app["totals"]
        estimate["verified_installs"] = totals["installs"]
        estimate["active_users"] = totals["active_window"]
        estimate["install_note"] = (
            "Installs that share anonymous usage (on by default, Settings ▸ Privacy). "
            "Devices, not people, and excludes anyone who opted out."
        )

    website: Dict[str, Any]
    if vercel.get("available"):
        overview = vercel.get("overview", {})
        website = {
            "available": True,
            "window": vercel.get("window", {}),
            "pageviews": _require_int(overview.get("pageviews"), "vercel overview.pageviews"),
            "visitors": _require_int(overview.get("visitors"), "vercel overview.visitors"),
            "stats": vercel.get("stats", {}),
            "note": "Anonymous aggregate visitors are not identifiable people, accounts, downloads, or installs.",
        }
    else:
        website = {"available": False, "error": "Website analytics unavailable", "pageviews": None, "visitors": None, "stats": {}}

    clone_days = github.get("clones", {}).get("clones", [])
    view_days = github.get("views", {}).get("views", [])
    traffic_dates = [item.get("timestamp") for item in clone_days + view_days if item.get("timestamp")]
    github_window = {
        "from": min(traffic_dates) if traffic_dates else None,
        "to": max(traffic_dates) if traffic_dates else None,
        "note": "GitHub repository traffic is a short rolling window and should be snapshotted regularly.",
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_iso(now),
        "repository": github.get("repository", {}),
        "adoption": estimate,
        "github": {
            "window": github_window,
            "views": {"operations": view_count, "unique_visitors": view_uniques, "daily": view_days},
            "clones": {"operations": clone_count, "unique_cloners": clone_uniques, "daily": clone_days},
            "automation": {
                "checkout_jobs": checkout_jobs,
                "owner_external_split": None,
                "note": (
                    "Checkout jobs are correlated automation, not one-to-one GitHub clone attribution. "
                    "GitHub cannot subtract maintainer work or identify the remaining operations as external users."
                ),
            },
            "stars": {
                "total": github.get("repository", {}).get("stargazers_count", 0),
                "high_confidence_recent_external": estimate["high_confidence_external_interest"],
                "low_signal_recent": estimate["low_signal_recent_stars"],
            },
            "forks": github.get("repository", {}).get("forks_count", 0),
            "open_issues_and_pull_requests": github.get("repository", {}).get(
                "open_issues_and_pull_requests_count", 0
            ),
            "popular_referrers": github.get("popular_referrers", []),
            "popular_paths": github.get("popular_paths", []),
            "release_assets": _release_assets(github.get("releases", [])),
        },
        "website": website,
        "app": app,
        "limitations": [
            "GitHub does not expose clone identities, IP addresses, user agents, or geography.",
            "GitHub clone operations and release-asset requests are not people, installations, or successful product use.",
            "Vercel's anonymous visitor metric cannot retroactively separate owner testing from external visits.",
            "Website download-click events measure clicks, not completed transfers or installations.",
            "App telemetry counts installs that share anonymous usage — devices, not people, and not anyone who opted out.",
            "In-app counters are lifetime totals per install with no timestamps, so they show what gets used, never when or in what order.",
        ],
    }


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _metric(value: Any) -> str:
    if value is None:
        return "Unknown"
    if isinstance(value, int):
        return f"{value:,}"
    return _esc(value)


def _sparkline(daily: List[Dict[str, Any]], key: str = "count", width: int = 420, height: int = 92) -> str:
    values = [int(item.get(key, 0) or 0) for item in daily]
    if not values:
        return '<div class="chart-empty">No daily data in this window</div>'
    maximum = max(max(values), 1)
    gap = 5
    bar_width = max(3, (width - gap * (len(values) - 1)) / len(values))
    bars = []
    for index, value in enumerate(values):
        bar_height = max(2, (value / maximum) * (height - 18))
        x = index * (bar_width + gap)
        y = height - bar_height
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="3">'
            f'<title>{_esc(value)}</title></rect>'
        )
    return f'<svg class="spark" viewBox="0 0 {width} {height}" role="img" aria-label="Daily trend">{"".join(bars)}</svg>'


def _ranked_rows(items: List[Dict[str, Any]], empty: str = "No data") -> str:
    if not items:
        return f'<p class="empty">{_esc(empty)}</p>'
    maximum = max((int(item.get("total", item.get("count", 0)) or 0) for item in items), default=1)
    rows = []
    for item in items[:8]:
        label = item.get("key") or item.get("referrer") or item.get("path") or "Direct / unknown"
        total = int(item.get("total", item.get("count", 0)) or 0)
        unique = item.get("visitors", item.get("uniques"))
        width = max(3, round(total / max(maximum, 1) * 100))
        detail = f"{total:,}"
        if isinstance(unique, int):
            detail += f" · {unique:,} unique"
        rows.append(
            '<div class="rank-row">'
            f'<div class="rank-copy"><span title="{_esc(label)}">{_esc(label)}</span><strong>{_esc(detail)}</strong></div>'
            f'<div class="rank-track"><span style="width:{width}%"></span></div>'
            "</div>"
        )
    return "".join(rows)


def render_dashboard(snapshot: Dict[str, Any]) -> str:
    """Render a self-contained dashboard with no external scripts or telemetry."""
    adoption = snapshot["adoption"]
    app = snapshot.get("app", {"available": False})
    app_days = app.get("window", {}).get("activeDays", 30)
    if app.get("available"):
        install_caption = "Opted-in installs · devices, not people"
        active_caption = f"Synced in the last {app_days} days"
    else:
        install_caption = "App telemetry unavailable"
        active_caption = "App telemetry unavailable"
    gh = snapshot["github"]
    website = snapshot["website"]
    updated = _parse_datetime(snapshot["generated_at"]).astimezone(ZoneInfo(TIMEZONE))
    updated_date = updated.strftime("%b %d, %Y").replace(" 0", " ")
    updated_time = updated.strftime("%I:%M %p PT").lstrip("0")
    latest_asset = gh["release_assets"][0] if gh["release_assets"] else None
    asset_value = latest_asset["requests"] if latest_asset else None
    asset_label = latest_asset["name"] if latest_asset else "No release asset"
    if website.get("available"):
        website_summary = f"""
          <div class="metric"><span>Website visitors</span><strong>{_metric(website['visitors'])}</strong><small>Anonymous estimate · {website.get('window', {}).get('days', 30)} days</small></div>
          <div class="metric"><span>Website pageviews</span><strong>{_metric(website['pageviews'])}</strong><small>Production web only</small></div>
        """
        website_panels = f"""
          <section class="section" id="website">
            <div class="section-head"><div><span class="eyebrow">Website</span><h2>Where discovery is happening</h2></div><span class="badge good">Vercel available</span></div>
            <div class="grid three">
              <article class="panel"><h3>Top pages</h3>{_ranked_rows(website['stats'].get('path', []))}</article>
              <article class="panel"><h3>Referrers</h3>{_ranked_rows(website['stats'].get('referrer', []), 'No attributed referrers')}</article>
              <article class="panel"><h3>Operating systems</h3>{_ranked_rows(website['stats'].get('os_name', []))}</article>
            </div>
            <div class="grid two compact-top">
              <article class="panel"><h3>Countries</h3>{_ranked_rows(website['stats'].get('country', []))}</article>
              <article class="panel"><h3>Tracked events</h3>{_ranked_rows(website['stats'].get('event_name', []), 'No custom events in this window')}</article>
            </div>
            <p class="footnote">{_esc(website['note'])}</p>
          </section>
        """
    else:
        website_summary = """
          <div class="metric muted"><span>Website visitors</span><strong>—</strong><small>Source unavailable</small></div>
          <div class="metric muted"><span>Website pageviews</span><strong>—</strong><small>Source unavailable</small></div>
        """
        website_panels = """
          <section class="section" id="website"><div class="section-head"><div><span class="eyebrow">Website</span><h2>Website analytics unavailable</h2></div><span class="badge warn">Needs Vercel login</span></div><article class="panel"><p>Run <code>vercel login</code>, then rebuild the dashboard. GitHub analytics remains available.</p></article></section>
        """

    if app.get("available"):
        features = app.get("features", {})
        feature_rows = _ranked_rows(
            [
                {"key": label, "total": features.get(field, 0)}
                for label, field in (
                    ("AI cleanup enabled", "cleanupEnabled"),
                    ("Uses snippets", "usesSnippets"),
                    ("Uses dictionary", "usesDictionary"),
                    ("Has Know-Me profile", "hasKnowMeProfile"),
                )
            ],
            "No feature data",
        )
        screens = [row for row in app["events"] if row["key"].startswith(("pane.", "tab."))]
        actions = [row for row in app["events"] if row["key"].startswith("action.")]
        app_panels = f"""
          <section class="section" id="app">
            <div class="section-head"><div><span class="eyebrow">App</span><h2>What people actually open</h2></div><span class="badge good">{_metric(app['totals']['installs'])} installs reporting</span></div>
            <div class="grid three">
              <article class="panel"><h3>Screens opened</h3>{_ranked_rows(screens, 'No screen counters yet')}</article>
              <article class="panel"><h3>Features used</h3>{_ranked_rows(actions, 'No feature counters yet')}</article>
              <article class="panel"><h3>Feature adoption</h3>{feature_rows}</article>
            </div>
            <div class="grid two compact-top">
              <article class="panel"><h3>App versions</h3>{_ranked_rows(app['versions'], 'No version data')}</article>
              <article class="panel"><h3>Countries</h3>{_ranked_rows(app['countries'], 'No country data')}</article>
            </div>
            <p class="footnote">Counters are lifetime totals per install, names and numbers only — no timestamps, no ordering, and never dictation text. {_metric(app['totals']['active_recent'])} of {_metric(app['totals']['installs'])} installs synced in the last 7 days; {_metric(app['totals']['new_window'])} first appeared in the last {app_days}.</p>
          </section>
        """
    else:
        app_panels = f"""
          <section class="section" id="app"><div class="section-head"><div><span class="eyebrow">App</span><h2>App telemetry unavailable</h2></div><span class="badge warn">Needs API token</span></div><article class="panel"><p>Set <code>{APP_STATS_TOKEN_ENV}</code> to the value configured on the deployment, then rebuild. The app does report aggregate install and usage counters (opt-out, on by default); this dashboard just could not read them.</p></article></section>
        """

    if app.get("available"):
        defensible_install_sentence = (
            f"Separately, {app['totals']['installs']} installs share anonymous usage "
            f"(on by default, Settings ▸ Privacy) and {app['totals']['active_window']} of them "
            f"synced in the last {app_days} days. Those are devices that opted in — a floor on real "
            "users, not a total, since anyone who opted out is uncounted."
        )
    else:
        defensible_install_sentence = (
            "Verified install and active-user counts are unavailable in this build because the "
            "telemetry API token was not configured — not because the app sends nothing."
        )

    # The hero used to assert "Actual users are not [visible]" unconditionally.
    # With app telemetry in hand that is simply false, and a page that
    # contradicts its own headline metric is worse than one that says less.
    if app.get("available"):
        hero_headline = "Installs are visible.<br>People are not."
        hero_value = adoption["verified_installs"]
        hero_label = "Opted-in installs"
        hero_caption = (
            f"{adoption['active_users']} active in {app_days} days · devices, not people · "
            f"{adoption['high_confidence_external_interest']} high-confidence external interest"
        )
    else:
        hero_headline = "Interest is visible.<br>Actual users are not."
        hero_value = adoption["high_confidence_external_interest"]
        hero_label = "High-confidence external interest"
        hero_caption = "App telemetry unavailable · install count not read"

    limitations = "".join(f"<li>{_esc(item)}</li>" for item in snapshot["limitations"])
    referrer_rows = _ranked_rows(gh["popular_referrers"], "No GitHub referrers reported")
    release_rows = "".join(
        f'<div class="release-row"><div><strong>{_esc(item["name"])}</strong><span>{_esc(item["tag"])}</span></div><div><strong>{_metric(item["requests"])}</strong><span>cumulative requests</span></div></div>'
        for item in gh["release_assets"][:6]
    ) or '<p class="empty">No downloadable release assets</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>OpenVoiceFlow Analytics</title>
<style>
:root{{--bg:#f7f5f0;--card:#fff;--ink:#26221b;--muted:#746c5f;--hair:rgba(38,34,27,.12);--fill:rgba(38,34,27,.045);--accent:#b4661f;--accent-soft:#f5e7d8;--green:#4e7a58;--green-soft:#e5eee7;--warn:#9b5b21;--warn-soft:#fbf3e7;--shadow:0 18px 50px rgba(38,34,27,.08);--sans:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",sans-serif;--mono:ui-monospace,"SF Mono",Menlo,monospace;color-scheme:light}}
@media(prefers-color-scheme:dark){{:root{{--bg:#131210;--card:#1d1b18;--ink:#ede9e0;--muted:#a69e8f;--hair:rgba(255,255,255,.11);--fill:rgba(255,255,255,.05);--accent:#e8974e;--accent-soft:#33261b;--green:#88b492;--green-soft:#1c2b21;--warn:#e3a263;--warn-soft:#2a2318;--shadow:0 18px 50px rgba(0,0,0,.22);color-scheme:dark}}}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.5;-webkit-font-smoothing:antialiased}}body:before{{content:"";position:fixed;inset:0;pointer-events:none;background:radial-gradient(circle at 88% 2%,rgba(180,102,31,.09),transparent 28%),radial-gradient(circle at 8% 42%,rgba(78,122,88,.06),transparent 22%)}}.shell{{position:relative;max-width:1180px;margin:auto;padding:28px 28px 72px}}header{{display:flex;justify-content:space-between;align-items:center;padding:4px 0 38px;border-bottom:1px solid var(--hair)}}.brand{{display:flex;align-items:center;gap:12px}}.glyph{{width:38px;height:38px;display:grid;place-items:center;border-radius:12px;background:var(--ink);color:var(--bg);font-family:var(--mono);font-weight:800;letter-spacing:-2px}}.brand strong{{display:block;font-size:15px}}.brand span,.stamp{{color:var(--muted);font-size:12px}}.stamp{{text-align:right;font-family:var(--mono)}}.hero{{padding:56px 0 34px;display:grid;grid-template-columns:1.3fr .7fr;gap:42px;align-items:end}}.eyebrow{{display:block;color:var(--accent);font:700 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;margin-bottom:10px}}h1{{font-size:clamp(36px,6vw,70px);line-height:.98;letter-spacing:-.055em;margin:0;max-width:820px}}.hero p{{font-size:18px;color:var(--muted);max-width:700px;margin:22px 0 0}}.answer{{border-left:3px solid var(--green);padding:4px 0 4px 20px}}.answer strong{{display:block;font-size:42px;line-height:1;letter-spacing:-.04em}}.answer span{{font-size:13px;color:var(--muted)}}.answer small{{display:block;margin-top:12px;color:var(--green);font-weight:650}}.metrics{{display:grid;grid-template-columns:repeat(6,1fr);border:1px solid var(--hair);border-radius:18px;overflow:hidden;background:var(--card);box-shadow:var(--shadow)}}.metric{{padding:20px;min-height:132px;border-right:1px solid var(--hair);display:flex;flex-direction:column}}.metric:last-child{{border:0}}.metric span{{font-size:12px;color:var(--muted)}}.metric strong{{font-size:30px;letter-spacing:-.04em;margin-top:auto}}.metric small{{font-size:11px;color:var(--muted);margin-top:4px}}.metric.muted strong{{color:var(--muted)}}.section{{padding:54px 0 0}}.section-head{{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:18px}}h2{{font-size:28px;line-height:1.1;letter-spacing:-.035em;margin:0}}h3{{font-size:14px;margin:0 0 20px}}.badge{{font:650 11px var(--mono);padding:7px 10px;border-radius:999px;white-space:nowrap}}.badge.good{{color:var(--green);background:var(--green-soft)}}.badge.warn{{color:var(--warn);background:var(--warn-soft)}}.grid{{display:grid;gap:16px}}.grid.two{{grid-template-columns:repeat(2,1fr)}}.grid.three{{grid-template-columns:repeat(3,1fr)}}.compact-top{{margin-top:16px}}.panel{{background:var(--card);border:1px solid var(--hair);border-radius:16px;padding:22px;min-width:0}}.panel p{{color:var(--muted);margin:0}}.panel code{{font-family:var(--mono);color:var(--ink);background:var(--fill);padding:2px 5px;border-radius:5px}}.chart-panel{{padding-bottom:10px}}.chart-head{{display:flex;justify-content:space-between;gap:20px;margin-bottom:20px}}.chart-head div:last-child{{text-align:right}}.chart-head strong{{font-size:24px;display:block}}.chart-head span{{font-size:12px;color:var(--muted)}}.spark{{display:block;width:100%;height:auto;overflow:visible}}.spark rect{{fill:var(--accent);opacity:.78}}.spark rect:hover{{opacity:1}}.chart-empty,.empty{{color:var(--muted);font-size:13px;padding:18px 0}}.signal-list{{list-style:none;margin:0;padding:0}}.signal-list li{{padding:16px 0;border-top:1px solid var(--hair);display:flex;justify-content:space-between;gap:16px}}.signal-list li:first-child{{border-top:0;padding-top:0}}.signal-list strong{{font-size:20px}}.signal-list span{{font-size:12px;color:var(--muted);max-width:70%}}.rank-row{{margin-top:15px}}.rank-row:first-of-type{{margin-top:0}}.rank-copy{{display:flex;justify-content:space-between;gap:12px;font-size:12px}}.rank-copy span{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted)}}.rank-copy strong{{font-size:11px;white-space:nowrap}}.rank-track{{height:5px;background:var(--fill);border-radius:99px;overflow:hidden;margin-top:7px}}.rank-track span{{display:block;height:100%;background:var(--accent);border-radius:99px}}.release-row{{display:flex;justify-content:space-between;gap:16px;padding:15px 0;border-top:1px solid var(--hair)}}.release-row:first-child{{padding-top:0;border:0}}.release-row>div:last-child{{text-align:right}}.release-row strong,.release-row span{{display:block}}.release-row strong{{font-size:13px}}.release-row span{{font-size:11px;color:var(--muted)}}.callout{{background:var(--warn-soft);border-color:rgba(180,102,31,.25)}}.callout h3{{font-size:20px}}.callout p{{font-size:14px}}.limits{{margin:0;padding-left:20px;color:var(--muted)}}.limits li{{padding:7px 0}}.footnote{{font-size:12px;color:var(--muted);margin:12px 2px 0}}footer{{margin-top:56px;padding-top:24px;border-top:1px solid var(--hair);font:12px var(--mono);color:var(--muted);display:flex;justify-content:space-between;gap:20px}}@media(max-width:900px){{.hero{{grid-template-columns:1fr}}.metrics{{grid-template-columns:repeat(3,1fr)}}.metric:nth-child(3){{border-right:0}}.metric:nth-child(-n+3){{border-bottom:1px solid var(--hair)}}.grid.three{{grid-template-columns:1fr}}}}@media(max-width:640px){{.shell{{padding:20px 16px 48px}}header{{align-items:flex-start}}.stamp{{max-width:150px}}.stamp-time{{display:none}}.hero{{padding-top:38px;gap:28px}}.hero p{{font-size:16px}}.metrics{{grid-template-columns:repeat(2,1fr)}}.metric{{border-bottom:1px solid var(--hair)}}.metric:nth-child(2n){{border-right:0}}.metric:nth-last-child(-n+2){{border-bottom:0}}.grid.two{{grid-template-columns:1fr}}.section-head{{align-items:flex-start;flex-direction:column}}footer{{flex-direction:column}}}}
</style>
</head>
<body><main class="shell">
<header><div class="brand"><div class="glyph">|||</div><div><strong>OpenVoiceFlow Analytics</strong><span>Private maintainer view</span></div></div><div class="stamp">Updated<br>{_esc(updated_date)}<span class="stamp-time"> · {_esc(updated_time)}</span></div></header>
<section class="hero"><div><span class="eyebrow">Adoption, without false precision</span><h1>{hero_headline}</h1><p>Repository, website and app signals in one place, with CI noise and low-signal activity kept separate from genuine adoption.</p></div><div class="answer"><strong>{_metric(hero_value)}</strong><span>{_esc(hero_label)}</span><small>{_esc(hero_caption)}</small></div></section>
<section class="metrics" aria-label="Key metrics">
<div class="metric"><span>Verified installs</span><strong>{_metric(adoption['verified_installs'])}</strong><small>{_esc(install_caption)}</small></div>
<div class="metric"><span>Active installs</span><strong>{_metric(adoption['active_users'])}</strong><small>{_esc(active_caption)}</small></div>
<div class="metric"><span>Release requests</span><strong>{_metric(asset_value)}</strong><small title="{_esc(asset_label)}">Latest DMG · cumulative</small></div>
{website_summary}
<div class="metric"><span>Repository views</span><strong>{_metric(gh['views']['operations'])}</strong><small>{_metric(gh['views']['unique_visitors'])} GitHub uniques</small></div>
<div class="metric"><span>Clone operations</span><strong>{_metric(gh['clones']['operations'])}</strong><small>{_metric(gh['clones']['unique_cloners'])} GitHub uniques</small></div>
</section>
<section class="section" id="github"><div class="section-head"><div><span class="eyebrow">GitHub</span><h2>Traffic and automation</h2></div><span class="badge warn">Rolling window</span></div>
<div class="grid two"><article class="panel chart-panel"><div class="chart-head"><div><h3>Clone operations</h3><span>Daily GitHub totals</span></div><div><strong>{_metric(gh['clones']['operations'])}</strong><span>operations</span></div></div>{_sparkline(gh['clones']['daily'])}</article>
<article class="panel chart-panel"><div class="chart-head"><div><h3>Repository views</h3><span>Daily GitHub totals</span></div><div><strong>{_metric(gh['views']['operations'])}</strong><span>views</span></div></div>{_sparkline(gh['views']['daily'])}</article></div>
<div class="grid three compact-top"><article class="panel"><h3>Noise accounting</h3><ul class="signal-list"><li><span>CI jobs that executed checkout</span><strong>{_metric(gh['automation']['checkout_jobs'])}</strong></li><li><span>Owner / external clone split</span><strong>{_metric(gh['automation']['owner_external_split'])}</strong></li><li><span>Low-signal recent stars</span><strong>{_metric(gh['stars']['low_signal_recent'])}</strong></li><li><span>High-confidence recent external stars</span><strong>{_metric(gh['stars']['high_confidence_recent_external'])}</strong></li></ul></article><article class="panel"><h3>GitHub referrers</h3>{referrer_rows}</article><article class="panel"><h3>Release assets</h3>{release_rows}</article></div>
<p class="footnote">{_esc(gh['automation']['note'])}</p></section>
{app_panels}
{website_panels}
<section class="section"><div class="section-head"><div><span class="eyebrow">Interpretation</span><h2>What “real users” means here</h2></div></div><div class="grid two"><article class="panel callout"><h3>The defensible answer</h3><p>There are <strong>{_metric(adoption['high_confidence_external_interest'])} high-confidence external GitHub accounts</strong> showing recent interest. That is a lower-bound engagement signal, not a count of app users. {_esc(defensible_install_sentence)}</p></article><article class="panel"><h3>Measurement limits</h3><ul class="limits">{limitations}</ul></article></div></section>
<footer><span>Generated locally · no analytics scripts · no credentials embedded</span><span>Schema v{_esc(snapshot['schema_version'])}</span></footer>
</main></body></html>"""


def write_private(path: Path, content: str) -> None:
    """Atomically write owner-readable output, including on replacement."""
    probe = path.parent
    while True:
        if probe.is_symlink():
            raise AnalyticsError("Refusing to write analytics output through a symlinked directory")
        if probe == probe.parent:
            break
        probe = probe.parent
    parent_existed = path.parent.exists()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not parent_existed or path.parent == DEFAULT_OUTPUT.parent:
        os.chmod(path.parent, 0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Private dashboard HTML path")
    parser.add_argument("--snapshot-output", type=Path, default=DEFAULT_SNAPSHOT, help="Private normalized JSON path")
    parser.add_argument("--days", type=int, default=30, help="Website analytics window (default: 30)")
    parser.add_argument("--no-vercel", action="store_true", help="Skip website analytics")
    parser.add_argument("--no-app", action="store_true", help="Skip app install/usage telemetry")
    parser.add_argument("--open", action="store_true", dest="open_dashboard", help="Open the local dashboard after building")
    args = parser.parse_args(argv)
    if args.days < 1 or args.days > 90:
        parser.error("--days must be between 1 and 90")

    now = datetime.now(timezone.utc)
    github = collect_github(now=now)
    if args.no_vercel:
        vercel = {"available": False, "error": "Website analytics unavailable"}
    else:
        try:
            vercel = collect_vercel(now=now, days=args.days)
        except AnalyticsError as exc:
            print(f"Warning: {exc}")
            vercel = {"available": False, "error": "Website analytics unavailable"}

    if args.no_app:
        app = {"available": False, "error": "App telemetry unavailable"}
    else:
        try:
            app = collect_app_telemetry(now=now, days=args.days)
        except AnalyticsError as exc:
            print(f"Warning: {exc}")
            app = {"available": False, "error": "App telemetry unavailable"}

    configured = os.environ.get("OVF_ANALYTICS_OWNER_LOGINS", "shimoverse")
    owner_logins = {item.strip().lower() for item in configured.split(",") if item.strip()}
    snapshot = build_snapshot(github, vercel, now=now, owner_logins=owner_logins, app=app)
    write_private(args.snapshot_output, json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    write_private(args.output, render_dashboard(snapshot))
    print(f"Dashboard: {args.output}")
    print(f"Snapshot:  {args.snapshot_output}")
    installs = snapshot["adoption"]["verified_installs"]
    install_line = (
        f"{installs} opted-in installs ({snapshot['adoption']['active_users']} active)"
        if installs is not None
        else "verified installs unavailable (no API token)"
    )
    print(
        "Answer: "
        f"{snapshot['adoption']['high_confidence_external_interest']} high-confidence external interest accounts; "
        f"{install_line}."
    )
    if args.open_dashboard:
        webbrowser.open(args.output.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
