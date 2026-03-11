from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from mcp.server.fastmcp import FastMCP

from course_schedule import (
    COOKIE_FILE,
    DEFAULT_HOME_URL,
    OUTPUT_DIR,
    PROFILE_FILE,
    HenuXkClient,
    load_json,
    run_fetch,
    save_json,
)
from schedule_cleaner import clean_schedule_grid_file, load_latest_clean_schedule

mcp = FastMCP("henu-campus-unified")
BASE_DIR = Path(__file__).resolve().parent
PERIOD_TIME_FILE = BASE_DIR / "period_time_config.json"
PERIOD_CALIBRATION_STATE_FILE = BASE_DIR / "period_time_calibration_state.json"
XIQUEER_REQUEST_FILE = BASE_DIR / "xiqueer_period_time_request.json"

# 图书馆核心模块路径 - 支持多种可能的位置
LIBRARY_CORE_CANDIDATES = [
    BASE_DIR / "library_core",  # 同级目录
    BASE_DIR.parent / "图书馆自动预约" / "web",  # 原始位置
    BASE_DIR.parent / "library_core",  # 父级目录
]
LIBRARY_CORE_DIR = None
for candidate in LIBRARY_CORE_CANDIDATES:
    if candidate.exists() and (candidate / "henu_core.py").exists():
        LIBRARY_CORE_DIR = candidate
        break

LIBRARY_COOKIE_FILE = BASE_DIR / "henu_library_cookies.json"
WEEKDAY_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
DEFAULT_PERIOD_TIMES: dict[str, dict[str, str]] = {
    "1": {"start": "08:00", "end": "08:45"},
    "2": {"start": "08:55", "end": "09:40"},
    "3": {"start": "10:00", "end": "10:45"},
    "4": {"start": "10:55", "end": "11:40"},
    "5": {"start": "11:50", "end": "12:35"},
    "6": {"start": "14:30", "end": "15:15"},
    "7": {"start": "15:25", "end": "16:10"},
    "8": {"start": "16:20", "end": "17:05"},
    "9": {"start": "17:15", "end": "18:00"},
    "10": {"start": "18:10", "end": "18:55"},
    "11": {"start": "19:00", "end": "19:45"},
    "12": {"start": "19:55", "end": "20:40"},
}

# 尝试导入图书馆模块
HenuLibraryBot = None
if LIBRARY_CORE_DIR and str(LIBRARY_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(LIBRARY_CORE_DIR))
    try:
        from henu_core import HenuLibraryBot  # type: ignore
    except Exception:
        pass


def _now_dt(timezone: str = "Asia/Shanghai") -> datetime:
    try:
        return datetime.now(ZoneInfo(timezone))
    except Exception:
        return datetime.now(ZoneInfo("Asia/Shanghai"))


def _is_hhmm(text: str) -> bool:
    return bool(re.fullmatch(r"[0-2]\d:[0-5]\d", text or ""))


def _to_minutes(hhmm: str) -> int:
    hour, minute = hhmm.split(":")
    return int(hour) * 60 + int(minute)


def _normalize_teaching_period_times(
    period_times: dict[str, dict[str, str]],
) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    """
    规范化节次配置：
    1) 按开始时间排序
    2) 当节次数较多(>=13)时，剔除中午短节次(12:00-14:10 且时长 20-35 分钟)
    3) 重新连续编号为 1..N，避免中午插入导致后续节次错位
    """
    items: list[tuple[int, str, str]] = []
    for key, cfg in (period_times or {}).items():
        if not isinstance(cfg, dict):
            continue
        start = str(cfg.get("start", "")).strip()
        end = str(cfg.get("end", "")).strip()
        if not (_is_hhmm(start) and _is_hhmm(end)):
            continue
        if _to_minutes(start) >= _to_minutes(end):
            continue
        try:
            period_no = int(str(key))
        except Exception:
            period_no = 999
        items.append((period_no, start, end))

    if not items:
        return {}, {"applied": False, "removed_midday_count": 0}

    items.sort(key=lambda x: (_to_minutes(x[1]), x[0]))
    removed_midday: list[tuple[int, str, str]] = []

    if len(items) >= 13:
        for period_no, start, end in items:
            start_min = _to_minutes(start)
            duration = _to_minutes(end) - start_min
            if 12 * 60 <= start_min <= (14 * 60 + 10) and 20 <= duration <= 35:
                removed_midday.append((period_no, start, end))
        if removed_midday and (len(items) - len(removed_midday) >= 12):
            removed_set = {(x[0], x[1], x[2]) for x in removed_midday}
            items = [it for it in items if it not in removed_set]
        else:
            removed_midday = []

    normalized: dict[str, dict[str, str]] = {}
    for idx, (_, start, end) in enumerate(items, start=1):
        normalized[str(idx)] = {"start": start, "end": end}

    return normalized, {
        "applied": True,
        "removed_midday_count": len(removed_midday),
        "removed_midday_periods": [
            {"period": p, "start": s, "end": e} for p, s, e in removed_midday
        ],
    }


def _load_period_times() -> dict[str, dict[str, str]]:
    if PERIOD_TIME_FILE.exists():
        try:
            data = json.loads(PERIOD_TIME_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cleaned: dict[str, dict[str, str]] = {}
                for k, v in data.items():
                    if not isinstance(v, dict):
                        continue
                    start = str(v.get("start", "")).strip()
                    end = str(v.get("end", "")).strip()
                    if _is_hhmm(start) and _is_hhmm(end):
                        cleaned[str(k)] = {"start": start, "end": end}
                if cleaned:
                    normalized, meta = _normalize_teaching_period_times(cleaned)
                    if normalized and normalized != cleaned and meta.get("removed_midday_count", 0) > 0:
                        _save_period_times(normalized)
                    return normalized or cleaned
        except Exception:
            pass

    PERIOD_TIME_FILE.write_text(
        json.dumps(DEFAULT_PERIOD_TIMES, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return dict(DEFAULT_PERIOD_TIMES)


def _save_period_times(period_times: dict[str, dict[str, str]]) -> None:
    PERIOD_TIME_FILE.write_text(
        json.dumps(period_times, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _load_calibration_state() -> dict[str, Any]:
    if not PERIOD_CALIBRATION_STATE_FILE.exists():
        return {}
    try:
        data = json.loads(PERIOD_CALIBRATION_STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_calibration_state(state: dict[str, Any]) -> None:
    PERIOD_CALIBRATION_STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _decode_resp_text(resp: requests.Response) -> str:
    content = resp.content or b""
    for enc in ("utf-8", "gbk", "gb2312"):
        try:
            return content.decode(enc)
        except Exception:
            continue
    return content.decode("utf-8", errors="ignore")


def _minutes_to_hhmm(value: int) -> str:
    hour = max(0, value) // 60
    minute = max(0, value) % 60
    return f"{hour:02d}:{minute:02d}"


def _load_xiqueer_request_config() -> dict[str, Any]:
    if not XIQUEER_REQUEST_FILE.exists():
        return {}
    try:
        data = json.loads(XIQUEER_REQUEST_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_xiqueer_request_config(config: dict[str, Any]) -> None:
    XIQUEER_REQUEST_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _xiqueer_config_summary(config: dict[str, Any]) -> dict[str, Any]:
    headers = config.get("headers") if isinstance(config.get("headers"), dict) else {}
    data_text = str(config.get("data", "") or "")
    return {
        "exists": bool(config),
        "config_file": str(XIQUEER_REQUEST_FILE),
        "url": str(config.get("url", "") or ""),
        "header_keys": sorted(list(headers.keys())),
        "has_cookie": "Cookie" in headers or "cookie" in headers,
        "data_length": len(data_text),
    }


def _extract_period_times_from_xiqueer_json(text: str) -> dict[str, dict[str, str]]:
    try:
        payload = json.loads(text)
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}

    rows = payload.get("sksj")
    if not isinstance(rows, list):
        return {}

    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        jieci = str(row.get("jieci", "") or "")
        start_raw = str(row.get("time", "") or "").strip()
        duration_raw = str(row.get("shichang", "") or "").strip()

        m = re.search(r"第\s*(\d+)\s*节", jieci)
        if not m:
            continue
        period = str(int(m.group(1)))

        if not _is_hhmm(start_raw.zfill(5)):
            continue
        start_hhmm = start_raw.zfill(5)

        try:
            duration = int(duration_raw)
        except Exception:
            continue
        if duration <= 0 or duration > 180:
            continue

        end_hhmm = _minutes_to_hhmm(_to_minutes(start_hhmm) + duration)
        if not _is_hhmm(end_hhmm):
            continue

        result[period] = {"start": start_hhmm, "end": end_hhmm}
    return result


def _fetch_xiqueer_period_times() -> dict[str, Any]:
    config = _load_xiqueer_request_config()
    if not config:
        return {"success": False, "msg": f"未配置 {XIQUEER_REQUEST_FILE}"}

    url = str(config.get("url", "") or "").strip()
    data_text = str(config.get("data", "") or "")
    headers = config.get("headers") if isinstance(config.get("headers"), dict) else {}
    timeout = int(config.get("timeout", 25) or 25)

    if not url:
        return {"success": False, "msg": "xiqueer 配置缺少 url"}
    if not data_text:
        return {"success": False, "msg": "xiqueer 配置缺少 data"}

    # 交给 requests 自动处理 Content-Length / Connection
    filtered_headers = {k: str(v) for k, v in headers.items() if k.lower() not in {"content-length", "connection"}}

    session = requests.Session()
    session.trust_env = False
    try:
        resp = session.post(url, headers=filtered_headers or None, data=data_text, timeout=timeout)
        text = _decode_resp_text(resp)
        period_times = _extract_period_times_from_xiqueer_json(text)
        return {
            "success": len(period_times) >= 4,
            "status_code": resp.status_code,
            "url": str(resp.url),
            "matched_period_count": len(period_times),
            "period_times": period_times,
            "raw_text": text,
            "msg": "xiqueer 节次时间获取成功" if len(period_times) >= 4 else "xiqueer 返回中未解析到足够节次时间",
        }
    except Exception as exc:
        return {"success": False, "msg": f"xiqueer 请求失败: {exc}"}


def _extract_period_times_from_text(text: str) -> dict[str, dict[str, str]]:
    clean = text or ""
    candidates: dict[str, dict[str, str]] = {}

    # 形如：第3节 10:00-10:45
    p1 = re.compile(
        r"第?\s*(\d{1,2})\s*节[^0-9]{0,30}([0-2]?\d:[0-5]\d)\s*(?:-|~|—|–|至)\s*([0-2]?\d:[0-5]\d)",
        re.I,
    )
    for m in p1.finditer(clean):
        period = str(int(m.group(1)))
        start = m.group(2).zfill(5)
        end = m.group(3).zfill(5)
        if _is_hhmm(start) and _is_hhmm(end) and _to_minutes(start) < _to_minutes(end):
            candidates[period] = {"start": start, "end": end}

    # 形如：10:00-10:45 第3节
    p2 = re.compile(
        r"([0-2]?\d:[0-5]\d)\s*(?:-|~|—|–|至)\s*([0-2]?\d:[0-5]\d)[^第]{0,30}第?\s*(\d{1,2})\s*节",
        re.I,
    )
    for m in p2.finditer(clean):
        period = str(int(m.group(3)))
        start = m.group(1).zfill(5)
        end = m.group(2).zfill(5)
        if _is_hhmm(start) and _is_hhmm(end) and _to_minutes(start) < _to_minutes(end):
            candidates[period] = {"start": start, "end": end}

    return candidates


def _fetch_timetable_text_candidates(sid: str, pwd: str) -> list[tuple[str, str]]:
    """
    返回 [(source_url, text)] 候选列表。
    """
    candidates: list[tuple[str, str]] = []
    ts = int(_now_dt().timestamp())
    urls = [
        f"https://xk.henu.edu.cn/public/SchoolTimetable.jsp?t={ts}",
        "https://xk.henu.edu.cn/public/SchoolTimetable.jsp",
        "http://xk.henu.edu.cn/public/SchoolTimetable.jsp",
    ]

    # 1) 用课表登录会话尝试
    if sid and pwd:
        try:
            client = HenuXkClient(sid, pwd, saved_cookies=load_json(COOKIE_FILE) or None)
            if client.login():
                save_json(COOKIE_FILE, client.get_cookies())
                home = client.fetch_page(DEFAULT_HOME_URL)
                referers = [home.get("final_url", ""), "https://xk.henu.edu.cn/cas/login.action", ""]
                for u in urls:
                    for ref in referers:
                        try:
                            page = client.fetch_page(u, referer=ref or None)
                            candidates.append((str(page.get("final_url", u)), str(page.get("text", ""))))
                        except Exception:
                            continue
        except Exception:
            pass

    # 2) 用公开登录页会话尝试
    try:
        session = requests.Session()
        session.trust_env = False
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )
        session.get("https://xk.henu.edu.cn/cas/login.action", timeout=20)
        for u in urls:
            try:
                resp = session.get(
                    u,
                    headers={"Referer": "https://xk.henu.edu.cn/cas/login.action"},
                    allow_redirects=True,
                    timeout=20,
                )
                candidates.append((str(resp.url), _decode_resp_text(resp)))
            except Exception:
                continue
    except Exception:
        pass

    return candidates


def _auto_calibrate_period_time_impl(force: bool = False) -> dict[str, Any]:
    now = _now_dt()
    state = _load_calibration_state()
    if not force and state.get("last_attempt_at"):
        try:
            last = datetime.fromisoformat(str(state["last_attempt_at"]))
            if now - last < timedelta(hours=6):
                return {
                    "success": bool(state.get("success")),
                    "skipped": True,
                    "reason": "最近 6 小时内已尝试校准",
                    "state": state,
                }
        except Exception:
            pass

    period_times = _load_period_times()
    updated_count = 0
    best_source = ""
    best_matches: dict[str, dict[str, str]] = {}
    normalization_meta: dict[str, Any] = {"applied": False, "removed_midday_count": 0}
    xiqueer_result = _fetch_xiqueer_period_times()

    # 1) 优先 xiqueer API
    if xiqueer_result.get("success"):
        matches = xiqueer_result.get("period_times") or {}
        if isinstance(matches, dict):
            best_matches = {str(k): v for k, v in matches.items() if isinstance(v, dict)}
            best_source = f"xiqueer_api:{xiqueer_result.get('url', '')}"

    # 2) 回退网页解析
    if len(best_matches) < 4:
        sid, pwd = _resolve_account("", "", use_saved_account=True)
        text_candidates = _fetch_timetable_text_candidates(sid, pwd)
        for source, text in text_candidates:
            matches = _extract_period_times_from_text(text)
            if len(matches) > len(best_matches):
                best_matches = matches
                best_source = source

    if len(best_matches) >= 4:
        normalized_matches, normalization_meta = _normalize_teaching_period_times(best_matches)
        if normalized_matches:
            best_matches = normalized_matches

    if len(best_matches) >= 4:
        for period, cfg in best_matches.items():
            old = period_times.get(period)
            if old != cfg:
                period_times[period] = cfg
                updated_count += 1
        if updated_count > 0:
            _save_period_times(period_times)

    success = len(best_matches) >= 4
    if success and best_source.startswith("xiqueer_api:"):
        message = "已从 xiqueer 接口自动校准"
    elif success:
        message = "已从教务作息页面自动校准"
    else:
        message = "未抓取到可用节次时间，保留现有配置"
    if success and int(normalization_meta.get("removed_midday_count", 0) or 0) > 0:
        message += f"，已剔除中午短节次 {int(normalization_meta.get('removed_midday_count', 0) or 0)} 个"

    new_state = {
        "last_attempt_at": now.isoformat(timespec="seconds"),
        "success": success,
        "matched_period_count": len(best_matches),
        "updated_period_count": updated_count,
        "source": best_source,
        "message": message,
        "xiqueer_success": bool(xiqueer_result.get("success")),
        "xiqueer_msg": str(xiqueer_result.get("msg", "")),
        "xiqueer_matched_period_count": int(xiqueer_result.get("matched_period_count", 0) or 0),
        "normalization": normalization_meta,
    }
    _save_calibration_state(new_state)

    return {
        "success": success,
        "skipped": False,
        "matched_period_count": len(best_matches),
        "updated_period_count": updated_count,
        "source": best_source,
        "period_times_matched": best_matches,
        "current_period_times": period_times,
        "normalization": normalization_meta,
        "xiqueer_result": {
            "success": bool(xiqueer_result.get("success")),
            "msg": str(xiqueer_result.get("msg", "")),
            "matched_period_count": int(xiqueer_result.get("matched_period_count", 0) or 0),
            "url": str(xiqueer_result.get("url", "")),
            "status_code": xiqueer_result.get("status_code"),
        },
        "msg": new_state["message"],
    }


def _extract_period_range(course_item: dict[str, Any]) -> tuple[int, int] | None:
    period_text = str(course_item.get("period", "") or "")
    m = re.search(r"第(\d+)(?:-(\d+))?节", period_text)
    if m:
        start = int(m.group(1))
        end = int(m.group(2) or m.group(1))
        return (start, end)

    time_text = str(course_item.get("time", "") or "")
    m2 = re.search(r"\[(\d+)-(\d+)\]", time_text)
    if m2:
        return (int(m2.group(1)), int(m2.group(2)))
    return None


def _course_with_clock(
    course_item: dict[str, Any],
    period_times: dict[str, dict[str, str]],
) -> dict[str, Any] | None:
    period_range = _extract_period_range(course_item)
    if not period_range:
        return None
    start_idx, end_idx = period_range
    start_cfg = period_times.get(str(start_idx))
    end_cfg = period_times.get(str(end_idx))
    if not start_cfg or not end_cfg:
        return None

    start_hhmm = start_cfg["start"]
    end_hhmm = end_cfg["end"]
    return {
        **course_item,
        "period_start": start_idx,
        "period_end": end_idx,
        "clock_start": start_hhmm,
        "clock_end": end_hhmm,
        "clock_start_minutes": _to_minutes(start_hhmm),
        "clock_end_minutes": _to_minutes(end_hhmm),
    }


def _effective_profile() -> dict[str, Any]:
    return load_json(PROFILE_FILE)


def _mask_profile(profile: dict[str, Any]) -> dict[str, Any]:
    location, seat_no = _resolve_library_defaults()
    return {
        "student_id": str(profile.get("student_id", "") or ""),
        "has_password": bool(profile.get("password")),
        "library_default_location": location,
        "library_default_seat_no": seat_no,
        "profile_file": str(PROFILE_FILE),
        "cookie_file": str(COOKIE_FILE),
        "library_cookie_file": str(LIBRARY_COOKIE_FILE),
    }


def _resolve_account(student_id: str, password: str, use_saved_account: bool = True) -> tuple[str, str]:
    sid = str(student_id or "").strip()
    pwd = str(password or "")
    if not use_saved_account:
        return sid, pwd

    profile = _effective_profile()
    sid = sid or str(profile.get("student_id", "") or "")
    pwd = pwd or str(profile.get("password", "") or "")
    return sid, pwd


def _save_profile_fields(fields: dict[str, Any]) -> None:
    profile = load_json(PROFILE_FILE)
    profile.update(fields)
    save_json(PROFILE_FILE, profile)


def _resolve_library_defaults() -> tuple[str, str]:
    local_profile = load_json(PROFILE_FILE)
    location = str(
        local_profile.get("library_location")
        or local_profile.get("location")
        or ""
    ).strip()
    seat_no = str(
        local_profile.get("library_seat_no")
        or local_profile.get("seat_no")
        or ""
    ).strip()
    return location, seat_no


def _target_library_date(target_date: str | None = None) -> str:
    if not target_date:
        return (_now_dt().date() + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        datetime.strptime(str(target_date), "%Y-%m-%d")
    except ValueError:
        raise ValueError("target_date 格式必须为 YYYY-MM-DD")
    return str(target_date)


def _load_library_cookies() -> dict[str, Any]:
    return load_json(LIBRARY_COOKIE_FILE)


def _save_library_cookies(cookies: dict[str, Any]) -> None:
    save_json(LIBRARY_COOKIE_FILE, cookies)


def _build_library_bot(student_id: str, password: str):
    if HenuLibraryBot is None:
        raise RuntimeError(f"图书馆核心模块不可用: {LIBRARY_CORE_DIR}/henu_core.py")

    stored = _load_library_cookies()
    bot = HenuLibraryBot(student_id, password, stored or None)  # type: ignore
    if bot.login():
        _save_library_cookies(bot.get_cookies())
        return bot

    if stored:
        fresh_bot = HenuLibraryBot(student_id, password, None)  # type: ignore
        if fresh_bot.login():
            _save_library_cookies(fresh_bot.get_cookies())
            return fresh_bot

    return None


def _latest_grid_file() -> Path | None:
    files = sorted(Path(OUTPUT_DIR).glob("schedule_grid_*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def get_server_time(timezone: str = "Asia/Shanghai") -> dict[str, Any]:
    """获取服务器当前时间（用于判断当前正在上的课）。"""
    now = _now_dt(timezone)
    return {
        "success": True,
        "timezone": timezone,
        "now_iso": now.isoformat(timespec="seconds"),
        "now_text": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday_index": now.weekday(),
        "weekday_cn": WEEKDAY_CN[now.weekday()],
    }


def get_period_time_config() -> dict[str, Any]:
    """读取节次时间映射配置（第几节 -> 开始/结束时间）。"""
    period_times = _load_period_times()
    return {
        "success": True,
        "config_file": str(PERIOD_TIME_FILE),
        "calibration_state_file": str(PERIOD_CALIBRATION_STATE_FILE),
        "calibration_state": _load_calibration_state(),
        "xiqueer_request": _xiqueer_config_summary(_load_xiqueer_request_config()),
        "period_times": period_times,
    }


def get_xiqueer_calibration_request() -> dict[str, Any]:
    """查看 xiqueer 自动校准请求配置（不回传完整 data）。"""
    return {"success": True, **_xiqueer_config_summary(_load_xiqueer_request_config())}


def set_xiqueer_calibration_request(
    data: str,
    cookie: str,
    user_agent: str = "KingoPalm/2.6.449 (iPhone; iOS 26.3; Scale/3.00)",
    url: str = "http://api.xiqueer.com/manager/wap/wapController.jsp",
) -> dict[str, Any]:
    """
    设置 xiqueer 节次时间请求参数（使用抓包得到的 data/cookie）。
    """
    data_text = str(data or "")
    cookie_text = str(cookie or "")
    ua = str(user_agent or "").strip()
    u = str(url or "").strip()
    if not data_text:
        return {"success": False, "msg": "data 不能为空"}
    if not cookie_text:
        return {"success": False, "msg": "cookie 不能为空"}
    if not u:
        return {"success": False, "msg": "url 不能为空"}

    headers: dict[str, str] = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Accept-Language": "zh-Hans-CN;q=1",
        "Cookie": cookie_text,
    }
    if ua:
        headers["User-Agent"] = ua

    config = {"url": u, "headers": headers, "data": data_text, "timeout": 25}
    _save_xiqueer_request_config(config)
    return {
        "success": True,
        "msg": "xiqueer 请求配置已保存",
        **_xiqueer_config_summary(config),
    }


def test_xiqueer_period_time_request() -> dict[str, Any]:
    """测试 xiqueer 请求并解析节次时间。"""
    result = _fetch_xiqueer_period_times()
    return {
        "success": bool(result.get("success")),
        "msg": str(result.get("msg", "")),
        "url": str(result.get("url", "")),
        "status_code": result.get("status_code"),
        "matched_period_count": int(result.get("matched_period_count", 0) or 0),
        "period_times": result.get("period_times", {}),
        "request_summary": _xiqueer_config_summary(_load_xiqueer_request_config()),
    }


def auto_calibrate_period_time(force: bool = False) -> dict[str, Any]:
    """尝试从教务作息页面自动校准节次时间。"""
    result = _auto_calibrate_period_time_impl(force=force)
    result["config_file"] = str(PERIOD_TIME_FILE)
    result["calibration_state_file"] = str(PERIOD_CALIBRATION_STATE_FILE)
    return result


def set_period_time(period: int, start_time: str, end_time: str) -> dict[str, Any]:
    """设置某一节次的开始/结束时间。示例: set_period_time(3, '10:00', '10:45')"""
    if period <= 0:
        return {"success": False, "msg": "period 必须大于 0"}
    start = str(start_time or "").strip()
    end = str(end_time or "").strip()
    if not _is_hhmm(start) or not _is_hhmm(end):
        return {"success": False, "msg": "start_time/end_time 格式必须为 HH:MM"}
    if _to_minutes(start) >= _to_minutes(end):
        return {"success": False, "msg": "开始时间必须早于结束时间"}

    period_times = _load_period_times()
    period_times[str(period)] = {"start": start, "end": end}
    _save_period_times(period_times)
    return {
        "success": True,
        "msg": "已更新节次时间",
        "period": period,
        "start": start,
        "end": end,
        "config_file": str(PERIOD_TIME_FILE),
    }


def show_account() -> dict[str, Any]:
    """显示当前课表账号配置（密码不明文返回）。"""
    return {"success": True, "account": _mask_profile(_effective_profile())}


def save_account(
    student_id: str,
    password: str,
    verify_login: bool = True,
    home_url: str = DEFAULT_HOME_URL,
    library_location: str = "",
    library_seat_no: str = "",
) -> dict[str, Any]:
    """保存课表账号；可选立即验证统一认证登录。"""
    sid = str(student_id or "").strip()
    pwd = str(password or "")
    if not sid or not pwd:
        return {"success": False, "msg": "student_id/password 不能为空"}

    context: dict[str, Any] = {}
    if verify_login:
        client = HenuXkClient(sid, pwd, saved_cookies=load_json(COOKIE_FILE) or None)
        if not client.login():
            return {"success": False, "msg": "登录失败，账号或密码可能错误"}
        save_json(COOKIE_FILE, client.get_cookies())
        context = client.fetch_user_context()

    fields: dict[str, Any] = {"student_id": sid, "password": pwd}
    if str(library_location or "").strip():
        fields["library_location"] = str(library_location).strip()
    if str(library_seat_no or "").strip():
        fields["library_seat_no"] = str(library_seat_no).strip()
    _save_profile_fields(fields)
    return {
        "success": True,
        "msg": "账号已保存",
        "account": _mask_profile(_effective_profile()),
        "context": {
            "login_id": context.get("login_id", ""),
            "user_type": context.get("user_type", ""),
            "current_xn": context.get("current_xn", ""),
            "current_xq": context.get("current_xq", ""),
        }
        if context
        else {},
    }


def check_login(
    student_id: str = "",
    password: str = "",
    use_saved_account: bool = True,
) -> dict[str, Any]:
    """检查账号当前是否可登录课表系统。"""
    sid, pwd = _resolve_account(student_id, password, use_saved_account=use_saved_account)
    if not sid:
        return {"success": False, "msg": "缺少学号，请先 save_account 或传入 student_id"}
    if not pwd:
        return {"success": False, "msg": "缺少密码，请先 save_account 或传入 password"}

    client = HenuXkClient(sid, pwd, saved_cookies=load_json(COOKIE_FILE) or None)
    ok = client.login()
    context = client.fetch_user_context()
    if ok:
        save_json(COOKIE_FILE, client.get_cookies())

    return {
        "success": ok,
        "msg": "登录成功" if ok else "登录失败",
        "login_id": context.get("login_id", ""),
        "user_type": context.get("user_type", ""),
        "current_xn": context.get("current_xn", ""),
        "current_xq": context.get("current_xq", ""),
        "school_code": context.get("school_code", ""),
    }


def fetch_schedule(
    student_id: str = "",
    password: str = "",
    xn: str | None = None,
    xq: str | None = None,
    schedule_url: str | None = None,
    home_url: str = DEFAULT_HOME_URL,
    use_saved_account: bool = True,
    save_account_after_success: bool = False,
) -> dict[str, Any]:
    """登录并抓取课表，同时自动输出 clean json/md。"""
    sid, pwd = _resolve_account(student_id, password, use_saved_account=use_saved_account)
    if not sid:
        return {"success": False, "msg": "缺少学号，请先 save_account 或传入 student_id"}
    if not pwd:
        return {"success": False, "msg": "缺少密码，请先 save_account 或传入 password"}

    result = run_fetch(
        student_id=sid,
        password=pwd,
        home_url=home_url,
        schedule_url=schedule_url,
        xn=xn,
        xq=xq,
    )

    if result.get("success") and save_account_after_success:
        _save_profile_fields({"student_id": sid, "password": pwd})

    # 兜底：若 clean 文件未生成，尝试从最新 schedule_grid 手工重建
    if result.get("success") and not result.get("clean_schedule_file_json"):
        grid_file = (result.get("generated_files") or {}).get("schedule_grid_file")
        if not grid_file:
            latest = _latest_grid_file()
            grid_file = str(latest) if latest else ""
        if grid_file:
            try:
                cleaned = clean_schedule_grid_file(grid_file, OUTPUT_DIR)
                result["clean_schedule_file_json"] = cleaned["files"].get("clean_schedule_json", "")
                result["clean_schedule_file_md"] = cleaned["files"].get("clean_schedule_md", "")
                result.setdefault("generated_files", {}).update(cleaned["files"])
            except Exception as exc:
                result["clean_schedule_error"] = str(exc)

    return result


def get_latest_schedule() -> dict[str, Any]:
    """读取最新结构化课表（schedule_clean_latest.json）。"""
    try:
        data = load_latest_clean_schedule(OUTPUT_DIR)
    except Exception as exc:
        return {"success": False, "msg": str(exc)}

    day_count = {day: len(items) for day, items in (data.get("schedule") or {}).items()}
    return {
        "success": True,
        "meta": data.get("meta", {}),
        "day_count": day_count,
        "schedule": data.get("schedule", {}),
        "source_file": data.get("source_file", ""),
    }


def get_current_course_status(
    timezone: str = "Asia/Shanghai",
    date_override: str = "",
    time_override: str = "",
    auto_calibrate: bool = True,
) -> dict[str, Any]:
    """
    判断当前是否在上课，并返回下一节课。
    - date_override: YYYY-MM-DD（可选）
    - time_override: HH:MM（可选）
    """
    try:
        data = load_latest_clean_schedule(OUTPUT_DIR)
    except Exception:
        return {
            "success": False,
            "msg": "未找到最新课表，请先执行 fetch_schedule()",
        }

    calibration_result: dict[str, Any] = {}
    if auto_calibrate:
        calibration_result = _auto_calibrate_period_time_impl(force=False)

    period_times = _load_period_times()
    now = _now_dt(timezone)
    if date_override:
        try:
            d = datetime.strptime(date_override, "%Y-%m-%d").date()
            now = now.replace(year=d.year, month=d.month, day=d.day)
        except ValueError:
            return {"success": False, "msg": "date_override 格式必须为 YYYY-MM-DD"}
    if time_override:
        if not _is_hhmm(time_override):
            return {"success": False, "msg": "time_override 格式必须为 HH:MM"}
        hh, mm = time_override.split(":")
        now = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)

    weekday_cn = WEEKDAY_CN[now.weekday()]
    day_courses = (data.get("schedule") or {}).get(weekday_cn, [])
    now_minutes = now.hour * 60 + now.minute

    current_courses: list[dict[str, Any]] = []
    future_courses: list[dict[str, Any]] = []
    unresolved_courses: list[dict[str, Any]] = []

    for row in day_courses:
        course = _course_with_clock(row, period_times)
        if not course:
            unresolved_courses.append(row)
            continue
        if course["clock_start_minutes"] <= now_minutes <= course["clock_end_minutes"]:
            current_courses.append(course)
        elif now_minutes < course["clock_start_minutes"]:
            future_courses.append(course)

    future_courses.sort(key=lambda x: x["clock_start_minutes"])
    next_course = future_courses[0] if future_courses else {}

    return {
        "success": True,
        "timezone": timezone,
        "now_text": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday_cn": weekday_cn,
        "current_course_count": len(current_courses),
        "current_courses": current_courses,
        "next_course": next_course,
        "unresolved_course_count": len(unresolved_courses),
        "unresolved_courses": unresolved_courses,
        "auto_calibration": calibration_result,
        "period_time_config_file": str(PERIOD_TIME_FILE),
        "period_times": period_times,
    }


def rebuild_clean_schedule_from_latest_grid() -> dict[str, Any]:
    """用最新 schedule_grid_*.html 重新生成 clean json/md。"""
    grid_file = _latest_grid_file()
    if not grid_file:
        return {"success": False, "msg": f"未找到 {OUTPUT_DIR}/schedule_grid_*.html"}
    try:
        cleaned = clean_schedule_grid_file(grid_file, OUTPUT_DIR)
    except Exception as exc:
        return {"success": False, "msg": f"重建失败: {exc}"}
    return {
        "success": True,
        "msg": "重建完成",
        "grid_file": str(grid_file),
        "files": cleaned.get("files", {}),
    }


def list_output_files(limit: int = 20) -> list[dict[str, Any]]:
    """列出 output 目录下的结果文件。"""
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[: max(1, limit)]
    return [
        {
            "name": p.name,
            "path": str(p),
            "size": p.stat().st_size,
            "mtime": int(p.stat().st_mtime),
        }
        for p in files
        if p.is_file()
    ]


def _library_locations() -> list[dict[str, str]]:
    if HenuLibraryBot is None:
        return []
    return [{"location": name, "area_id": str(area_id)} for name, area_id in HenuLibraryBot.LOCATIONS.items()]  # type: ignore


def _library_reserve(
    location: str = "",
    seat_no: str = "",
    target_date: str | None = None,
    preferred_time: str | None = None,
    save_as_default: bool = True,
) -> dict[str, Any]:
    sid, pwd = _resolve_account("", "", use_saved_account=True)
    if not sid:
        return {"success": False, "msg": "缺少学号，请先 setup_account"}
    if not pwd:
        return {"success": False, "msg": "缺少密码，请先 setup_account"}

    default_location, default_seat = _resolve_library_defaults()
    target_location = str(location or default_location).strip()
    target_seat = str(seat_no or default_seat).strip()
    if not target_location or not target_seat:
        return {
            "success": False,
            "msg": "请提供 location/seat_no，或先在 setup_account 里设置图书馆默认区域和座位",
            "library_defaults": {"location": default_location, "seat_no": default_seat},
            "locations": _library_locations(),
        }

    try:
        date_text = _target_library_date(target_date)
    except ValueError as exc:
        return {"success": False, "msg": str(exc)}

    bot = _build_library_bot(sid, pwd)
    if bot is None:
        return {"success": False, "msg": "图书馆登录失败，请检查账号密码或会话状态"}

    result = bot.reserve(target_location, target_seat, date_text, preferred_time=preferred_time)
    _save_library_cookies(bot.get_cookies())

    if result.get("success") and save_as_default:
        _save_profile_fields({"library_location": target_location, "library_seat_no": target_seat})

    return {
        "success": bool(result.get("success")),
        "msg": str(result.get("msg", "")),
        "student_id": sid,
        "target_date": date_text,
        "location": target_location,
        "seat_no": target_seat,
        "library_cookie_file": str(LIBRARY_COOKIE_FILE),
    }


def _library_records(record_type: str = "1", page: int = 1, limit: int = 20) -> dict[str, Any]:
    sid, pwd = _resolve_account("", "", use_saved_account=True)
    if not sid:
        return {"success": False, "msg": "缺少学号，请先 setup_account"}
    if not pwd:
        return {"success": False, "msg": "缺少密码，请先 setup_account"}

    bot = _build_library_bot(sid, pwd)
    if bot is None:
        return {"success": False, "msg": "图书馆登录失败，请检查账号密码或会话状态", "records": []}

    result = bot.list_seat_records(record_type=record_type, page=page, limit=limit)
    _save_library_cookies(bot.get_cookies())
    result["student_id"] = sid
    return result


def _library_cancel(record_id: str, record_type: str = "auto") -> dict[str, Any]:
    sid, pwd = _resolve_account("", "", use_saved_account=True)
    if not sid:
        return {"success": False, "msg": "缺少学号，请先 setup_account"}
    if not pwd:
        return {"success": False, "msg": "缺少密码，请先 setup_account"}
    if not str(record_id or "").strip():
        return {"success": False, "msg": "record_id 不能为空"}

    bot = _build_library_bot(sid, pwd)
    if bot is None:
        return {"success": False, "msg": "图书馆登录失败，请检查账号密码或会话状态"}

    rt = str(record_type or "auto").strip().lower()
    if rt in {"", "auto"}:
        resolved = None
        for candidate in ("1", "3", "4"):
            records = bot.list_seat_records(record_type=candidate, page=1, limit=100)
            for row in records.get("records") or []:
                if str(row.get("id")) == str(record_id):
                    resolved = candidate
                    break
            if resolved:
                break
        rt = resolved or "1"

    result = bot.cancel_seat_record(record_id=record_id, record_type=rt)
    _save_library_cookies(bot.get_cookies())
    result["student_id"] = sid
    result["record_type_resolved"] = rt
    return result


# ===== MCP 精简对外工具 =====


@mcp.tool()
def setup_account(
    student_id: str,
    password: str,
    library_location: str = "",
    library_seat_no: str = "",
    verify_login: bool = True,
    calibrate_period_time: bool = True,
) -> dict[str, Any]:
    """
    一站式初始化账号：
    1) 保存账号
    2) 可选验证登录
    3) 可选立即校准节次时间
    """
    result = save_account(
        student_id=student_id,
        password=password,
        verify_login=verify_login,
        home_url=DEFAULT_HOME_URL,
        library_location=library_location,
        library_seat_no=library_seat_no,
    )
    if not result.get("success"):
        return result

    calibration: dict[str, Any] = {}
    if calibrate_period_time:
        calibration = auto_calibrate_period_time(force=True)

    return {
        "success": True,
        "msg": "账号初始化完成",
        "account": result.get("account", {}),
        "login_context": result.get("context", {}),
        "period_time_calibration": calibration,
    }


@mcp.tool()
def sync_schedule(
    xn: str | None = None,
    xq: str | None = None,
    auto_calibrate: bool = True,
) -> dict[str, Any]:
    """
    同步课表（使用已保存账号）并生成 clean 结构化结果。
    """
    calibration: dict[str, Any] = {}
    if auto_calibrate:
        calibration = auto_calibrate_period_time(force=False)

    result = fetch_schedule(
        student_id="",
        password="",
        xn=xn,
        xq=xq,
        use_saved_account=True,
        save_account_after_success=False,
    )
    result["period_time_calibration"] = calibration
    return result


@mcp.tool()
def library_locations() -> dict[str, Any]:
    """
    查看图书馆可预约区域列表。
    """
    if HenuLibraryBot is None:
        return {"success": False, "msg": f"图书馆核心模块不可用: {LIBRARY_CORE_DIR}/henu_core.py", "locations": []}
    return {"success": True, "locations": _library_locations()}


@mcp.tool()
def library_reserve(
    location: str = "",
    seat_no: str = "",
    target_date: str = "",
    preferred_time: str = "08:00",
    save_as_default: bool = True,
) -> dict[str, Any]:
    """
    预约图书馆座位（默认用 setup_account 保存的图书馆区域/座位）。
    """
    date_text = str(target_date).strip() or None
    pref = str(preferred_time).strip() or None
    return _library_reserve(
        location=location,
        seat_no=seat_no,
        target_date=date_text,
        preferred_time=pref,
        save_as_default=save_as_default,
    )


@mcp.tool()
def library_records(record_type: str = "1", page: int = 1, limit: int = 20) -> dict[str, Any]:
    """
    查询图书馆预约记录。record_type: 1(普通) / 3(研习) / 4(考研)
    """
    return _library_records(record_type=record_type, page=page, limit=limit)


@mcp.tool()
def library_cancel(record_id: str, record_type: str = "auto") -> dict[str, Any]:
    """
    取消图书馆预约。record_type 支持 auto 自动识别。
    """
    return _library_cancel(record_id=record_id, record_type=record_type)


@mcp.tool()
def current_course(
    timezone: str = "Asia/Shanghai",
    auto_calibrate: bool = True,
) -> dict[str, Any]:
    """
    获取“当前正在上的课 + 下一节课”。
    """
    return get_current_course_status(
        timezone=timezone,
        auto_calibrate=auto_calibrate,
    )


@mcp.tool()
def latest_schedule() -> dict[str, Any]:
    """
    获取最新结构化课表。
    """
    return get_latest_schedule()


@mcp.tool()
def set_calibration_source(
    data: str,
    cookie: str,
    user_agent: str = "KingoPalm/2.6.449 (iPhone; iOS 26.3; Scale/3.00)",
) -> dict[str, Any]:
    """
    更新 xiqueer 校准源（抓包得到的 data/cookie）。
    """
    save_result = set_xiqueer_calibration_request(
        data=data,
        cookie=cookie,
        user_agent=user_agent,
    )
    if not save_result.get("success"):
        return save_result

    test_result = test_xiqueer_period_time_request()
    return {
        "success": bool(test_result.get("success")),
        "msg": "校准源已更新",
        "config": save_result,
        "test": test_result,
    }


@mcp.tool()
def system_status(timezone: str = "Asia/Shanghai") -> dict[str, Any]:
    """
    查看系统状态：账号、时间、节次配置、最近校准状态、输出文件。
    """
    return {
        "success": True,
        "server_time": get_server_time(timezone=timezone),
        "account": show_account(),
        "period_time_config": get_period_time_config(),
        "library_defaults": {
            "location": _resolve_library_defaults()[0],
            "seat_no": _resolve_library_defaults()[1],
        },
        "library_cookie_file": str(LIBRARY_COOKIE_FILE),
        "recent_output_files": list_output_files(limit=10),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HENU unified MCP server (schedule + library)")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="MCP transport type",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transports")
    parser.add_argument("--port", type=int, default=8001, help="Port for HTTP transports")
    parser.add_argument("--path", default="/mcp", help="HTTP endpoint path for streamable-http transport")
    parser.add_argument(
        "--stateless-http",
        action="store_true",
        help="Enable stateless HTTP mode for streamable-http transport",
    )
    parser.add_argument(
        "--json-response",
        action="store_true",
        help="Enable JSON response mode for streamable-http transport",
    )
    args = parser.parse_args()

    if args.transport in ("streamable-http", "sse"):
        mcp.settings.host = args.host
        mcp.settings.port = args.port
    if args.transport == "streamable-http":
        mcp.settings.streamable_http_path = args.path
        mcp.settings.stateless_http = args.stateless_http
        mcp.settings.json_response = args.json_response

    mcp.run(transport=args.transport)
