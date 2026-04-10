import collections
import json
import os
import random
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:5000")
TARGET_RPS = int(os.environ.get("TARGET_RPS", "1000"))
DURATION_SECONDS = int(os.environ.get("DURATION_SECONDS", "5"))
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "300"))
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "5"))

ENDPOINT_WEIGHTS = [
    ("home", 0.15),
    ("ping", 0.15),
    ("announce", 0.30),
    ("search", 0.20),
    ("view", 0.20),
]


seen_users = []
seen_users_lock = threading.Lock()
announce_counter = 0
announce_counter_lock = threading.Lock()


def choose_endpoint():
    roll = random.random()
    cumulative = 0.0
    for name, weight in ENDPOINT_WEIGHTS:
        cumulative += weight
        if roll <= cumulative:
            return name
    return ENDPOINT_WEIGHTS[-1][0]


def next_user_id():
    global announce_counter
    with announce_counter_lock:
        announce_counter += 1
        return f"load-user-{int(time.time() * 1000)}-{announce_counter}"


def remember_user(user_id):
    with seen_users_lock:
        seen_users.append(user_id)
        if len(seen_users) > 5000:
            del seen_users[:1000]


def sample_user():
    with seen_users_lock:
        if not seen_users:
            return None
        return random.choice(seen_users)


def perform_request(session, endpoint_name):
    start = time.perf_counter()
    status_code = None
    ok = False
    error = None

    try:
        if endpoint_name == "home":
            resp = session.get(f"{BASE_URL}/", timeout=REQUEST_TIMEOUT)
        elif endpoint_name == "ping":
            resp = session.get(f"{BASE_URL}/ping", timeout=REQUEST_TIMEOUT)
        elif endpoint_name == "announce":
            user_id = next_user_id()
            payload = {
                "user-id": user_id,
                "access-link": f"https://example.test/{user_id}",
                "visible": "True",
                "expire": "120",
            }
            resp = session.post(
                f"{BASE_URL}/contacts/announce",
                data=payload,
                timeout=REQUEST_TIMEOUT,
            )
            if resp.ok:
                remember_user(user_id)
        elif endpoint_name == "search":
            user_id = sample_user()
            if user_id is None:
                user_id = next_user_id()
                remember_user(user_id)
            resp = session.get(
                f"{BASE_URL}/contacts/search",
                data={"user-id": user_id},
                timeout=REQUEST_TIMEOUT,
            )
        elif endpoint_name == "view":
            resp = session.get(
                f"{BASE_URL}/contacts/view",
                params={"page": 1, "limit": 50},
                timeout=REQUEST_TIMEOUT,
            )
        else:
            raise ValueError(f"unknown endpoint {endpoint_name}")

        status_code = resp.status_code
        ok = 200 <= resp.status_code < 400
    except Exception as exc:
        error = str(exc)

    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "endpoint": endpoint_name,
        "ok": ok,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "error": error,
    }


def summarize(results, wall_seconds):
    endpoint_stats = collections.defaultdict(lambda: {
        "total": 0,
        "success": 0,
        "fail": 0,
        "latencies": [],
        "status_codes": collections.Counter(),
        "errors": collections.Counter(),
    })

    success = 0
    failures = 0

    for result in results:
        stat = endpoint_stats[result["endpoint"]]
        stat["total"] += 1
        stat["latencies"].append(result["latency_ms"])
        if result["status_code"] is not None:
            stat["status_codes"][str(result["status_code"])] += 1
        if result["ok"]:
            stat["success"] += 1
            success += 1
        else:
            stat["fail"] += 1
            failures += 1
            if result["error"]:
                stat["errors"][result["error"]] += 1

    summary = {
        "base_url": BASE_URL,
        "target_rps": TARGET_RPS,
        "duration_seconds": DURATION_SECONDS,
        "planned_requests": TARGET_RPS * DURATION_SECONDS,
        "completed_requests": len(results),
        "successes": success,
        "failures": failures,
        "wall_time_seconds": round(wall_seconds, 3),
        "achieved_rps": round(len(results) / wall_seconds, 2) if wall_seconds else 0,
        "endpoint_stats": {},
    }

    for endpoint, stat in endpoint_stats.items():
        latencies = stat["latencies"]
        stat_summary = {
            "total": stat["total"],
            "success": stat["success"],
            "fail": stat["fail"],
            "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95) - 1], 2) if latencies else None,
            "max_latency_ms": round(max(latencies), 2) if latencies else None,
            "status_codes": dict(stat["status_codes"]),
        }
        if stat["errors"]:
            stat_summary["top_errors"] = dict(stat["errors"].most_common(3))
        summary["endpoint_stats"][endpoint] = stat_summary

    return summary


def main():
    total_requests = TARGET_RPS * DURATION_SECONDS
    results = []
    wall_start = time.perf_counter()

    with requests.Session() as session:
        adapter = requests.adapters.HTTPAdapter(pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            start_time = time.perf_counter()

            for i in range(total_requests):
                scheduled_at = start_time + (i / TARGET_RPS)
                now = time.perf_counter()
                if scheduled_at > now:
                    time.sleep(scheduled_at - now)
                endpoint_name = choose_endpoint()
                futures.append(executor.submit(perform_request, session, endpoint_name))

            for future in as_completed(futures):
                results.append(future.result())

    wall_seconds = time.perf_counter() - wall_start
    print(json.dumps(summarize(results, wall_seconds), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
