#!/usr/bin/env python3
"""
HENU Campus Unified Functions (Skill Edition)
河南大学校园一体化助手 - OpenClaw Skill 版本
合并功能: 课表查看 + 图书馆座位预约
"""

from __future__ import annotations

import base64
import json
import math
import os
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from lxml import html

# ===== 配置路径 =====
BASE_DIR = Path(__file__).resolve().parent.parent  # skill/
OUTPUT_DIR = BASE_DIR / "output"
COOKIE_FILE = BASE_DIR / "henu_cookies.json"
LIBRARY_COOKIE_FILE = BASE_DIR / "henu_library_cookies.json"
PROFILE_FILE = BASE_DIR / "henu_profile.json"
PERIOD_TIME_FILE = BASE_DIR / "period_time_config.json"
PERIOD_CALIBRATION_STATE_FILE = BASE_DIR / "period_time_calibration_state.json"
XIQUEER_REQUEST_FILE = BASE_DIR / "xiqueer_period_time_request.json"

# ===== 图书馆核心模块查找 =====
LIBRARY_CORE_CANDIDATES = [
    BASE_DIR / "library_core",                          # skill/library_core/
    BASE_DIR.parent / "library_core",                   # 主项目同级 library_core/
    BASE_DIR.parent / "图书馆自动预约" / "web",          # 原项目结构
    BASE_DIR.parent.parent / "图书馆自动预约" / "web",   # 上两级
    Path.home() / ".config" / "henu" / "library_core",  # 全局配置
]
LIBRARY_CORE_DIR = None
for candidate in LIBRARY_CORE_CANDIDATES:
    if candidate.exists() and (candidate / "henu_core.py").exists():
        LIBRARY_CORE_DIR = candidate
        break

# 尝试导入图书馆模块
HenuLibraryBot = None
if LIBRARY_CORE_DIR and str(LIBRARY_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(LIBRARY_CORE_DIR))
    try:
        from henu_core import HenuLibraryBot  # type: ignore
    except Exception:
        pass

# ===== 常量定义 =====
WEEKDAY_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
DEFAULT_HOME_URL = "https://xk.henu.edu.cn/frame/homes.action?v=07364432695342088912561"
DEFAULT_PERIOD_TIMES: dict[str, dict[str, str]] = {
    "1": {"start": "08:00", "end": "08:45"},
    "2": {"start": "08:55", "end": "09:40"},
    "3": {"start": "10:00", "end": "10:45"},
    "4": {"start": "10:55", "end": "11:40"},
    "5": {"start": "11:45", "end": "12:30"},
    "6": {"start": "13:00", "end": "13:30"},
    "7": {"start": "13:30", "end": "14:00"},
    "8": {"start": "14:05", "end": "14:50"},
    "9": {"start": "15:00", "end": "15:45"},
    "10": {"start": "15:55", "end": "16:40"},
    "11": {"start": "17:00", "end": "17:45"},
    "12": {"start": "17:55", "end": "18:40"},
    "13": {"start": "19:10", "end": "19:55"},
    "14": {"start": "20:05", "end": "20:50"},
    "15": {"start": "20:55", "end": "21:40"},
}

# ===== 工具函数 =====
def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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


def _minutes_to_hhmm(value: int) -> str:
    hour = max(0, value) // 60
    minute = max(0, value) % 60
    return f"{hour:02d}:{minute:02d}"


def _decode_resp_text(resp: requests.Response) -> str:
    content = resp.content or b""
    for enc in ("utf-8", "gbk", "gb2312"):
        try:
            return content.decode(enc)
        except Exception:
            continue
    return content.decode("utf-8", errors="ignore")


# ===== 课表客户端 =====
class HenuXkClient:
    AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
    PERSIST_COOKIE_NAMES = {"CASTGC", "happyVoyage", "platformMultilingual"}

    def __init__(self, username: str, password: str, saved_cookies: dict[str, Any] | None = None):
        self.username = str(username).strip()
        self.password = password or ""
        self.base_url = "https://xk.henu.edu.cn"
        self.cas_login_url = "https://ids.henu.edu.cn/authserver/login"
        
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        if saved_cookies:
            self.session.cookies.update(saved_cookies)

    def get_cookies(self) -> dict[str, Any]:
        return {cookie.name: cookie.value for cookie in self.session.cookies 
                if cookie.name in self.PERSIST_COOKIE_NAMES}

    def _decode_text(self, resp: requests.Response) -> str:
        return _decode_resp_text(resp)

    def _extract_title(self, text: str) -> str:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
        return re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""

    def _is_auth_invalid_page(self, text: str) -> bool:
        compact = re.sub(r"\s+", "", text).lower()
        markers = ["window.top.location.href='/'", 'window.top.location.href="/"', "凭证已失效", "请重新登录"]
        return any(marker in compact for marker in markers)

    def _random_string(self, length: int) -> str:
        return "".join(self.AES_CHARS[math.floor(random.random() * len(self.AES_CHARS))] for _ in range(length))

    def _encrypt_password(self, password: str, salt: str) -> str:
        random_prefix = self._random_string(64)
        iv_str = self._random_string(16)
        text = random_prefix + password
        key_bytes = salt.encode("utf-8")
        iv_bytes = iv_str.encode("utf-8")
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        return base64.b64encode(cipher.encrypt(pad(text.encode("utf-8"), AES.block_size))).decode("utf-8")

    def fetch_page(self, url: str, referer: str | None = None) -> dict[str, Any]:
        headers: dict[str, str] = {"Referer": referer} if referer else {}
        resp = self.session.get(url, headers=headers or None, allow_redirects=True, timeout=30)
        text = self._decode_text(resp)
        title = self._extract_title(text)
        return {
            "url": url, "final_url": resp.url, "status_code": resp.status_code,
            "title": title, "invalid_auth": self._is_auth_invalid_page(text), "text": text,
        }

    def _extract_var(self, text: str, name: str) -> str:
        pattern = rf"var\s+{re.escape(name)}\s*=\s*'(.*?)';"
        m = re.search(pattern, text)
        return m.group(1).strip() if m else ""

    def fetch_user_context(self) -> dict[str, Any]:
        url = f"{self.base_url}/frame/home/js/SetMainInfo.jsp?v={int(datetime.now().timestamp())}"
        result = self.fetch_page(url)
        text = result["text"]
        login_id = self._extract_var(text, "_loginid") or self._extract_var(text, "G_LOGIN_ID")
        is_guest = login_id.lower() in {"", "guest", "kingo.guest"}
        return {
            "authenticated": bool(login_id) and not is_guest and not result["invalid_auth"],
            "login_id": login_id,
            "user_type": self._extract_var(text, "_usertype") or self._extract_var(text, "G_USER_TYPE"),
            "current_xn": self._extract_var(text, "_currentXn"),
            "current_xq": self._extract_var(text, "_currentXq"),
            "school_code": self._extract_var(text, "_schoolCode") or self._extract_var(text, "G_SCHOOL_CODE"),
        }

    def _check_logged_in(self) -> bool:
        return bool(self.fetch_user_context().get("authenticated"))

    def login(self) -> bool:
        if self._check_logged_in():
            return True
        
        cas_auth_url = f"{self.cas_login_url}?service={self.base_url}/caslogin"
        try:
            self.session.get(cas_auth_url, allow_redirects=True, timeout=30)
            if self._check_logged_in():
                return True
        except Exception:
            pass
        
        if not self.password:
            return False
        
        try:
            self.session.cookies.clear()
            login_page = self.session.get(cas_auth_url, timeout=30)
            login_text = self._decode_text(login_page)
            execution_match = re.search(r'name="execution" value="(.*?)"', login_text)
            salt_match = re.search(r'id="pwdEncryptSalt" value="(.*?)"', login_text)
            if not execution_match or not salt_match:
                return False
            
            form_data = {
                "username": self.username,
                "password": self._encrypt_password(self.password, salt_match.group(1)),
                "captcha": "", "_eventId": "submit", "cllt": "userNameLogin",
                "dllt": "generalLogin", "lt": "", "execution": execution_match.group(1),
            }
            self.session.post(login_page.url, data=form_data, allow_redirects=True, timeout=35)
            return self._check_logged_in()
        except Exception:
            return False


# ===== 课表解析 =====
def parse_schedule_grid(html_text: str) -> dict[str, Any]:
    """解析课表HTML，支持两种格式：网格格式和列表格式。"""
    doc = html.fromstring(html_text)
    
    # 先尝试解析列表格式（新接口返回的格式）
    tbody = doc.xpath("//tbody")
    if tbody:
        rows = tbody[0].xpath("./tr")
        if rows and len(rows) > 0:
            # 检查是否是列表格式（有课程名称列）
            first_row_tds = rows[0].xpath("./td")
            if len(first_row_tds) >= 10:
                # 可能是列表格式，尝试解析
                try:
                    return parse_schedule_list(html_text)
                except Exception:
                    pass  # 失败则尝试网格格式
    
    # 尝试解析网格格式（旧格式）
    tables = doc.xpath("//table[@id='mytable']")
    if not tables:
        raise ValueError("未找到课表主表格")
    
    table = tables[0]
    rows = table.xpath(".//tr")
    
    # 提取星期表头
    header_cells = rows[0].xpath("./td")[1:] if rows else []
    weekdays = [re.sub(r"\s+", "", "".join(td.xpath(".//text()"))).strip() for td in header_cells]
    weekdays = [w for w in weekdays if w]
    
    schedule: dict[str, list[dict[str, str]]] = {day: [] for day in weekdays}
    slot_fallback = {"一": "第1-2节", "二": "第3-4节", "三": "第6-7节", "四": "第9-10节", "五": "第11-12节"}
    slot_order = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5}
    section_map = {"一": "上午", "二": "上午", "三": "下午", "四": "下午", "五": "晚上"}
    
    for row in rows[1:]:
        tds = row.xpath("./td")
        if not tds:
            continue
        
        cell0 = re.sub(r"\s+", "", "".join(tds[0].xpath(".//text()"))).strip()
        if cell0 == "中午":
            continue
        
        if cell0 in ("上午", "下午", "晚上"):
            slot_key = re.sub(r"\s+", "", "".join(tds[1].xpath(".//text()"))).strip() if len(tds) > 1 else ""
            start_idx = 2
        else:
            slot_key = cell0
            start_idx = 1
        
        if slot_key not in slot_fallback:
            continue
        
        weekday_cells = tds[start_idx:start_idx + len(weekdays)]
        for idx, td in enumerate(weekday_cells):
            day = weekdays[idx]
            blocks = td.xpath(".//div[.//font]")
            for block in blocks:
                parts = [re.sub(r"\s+", " ", x).strip() for x in block.xpath(".//text()")]
                parts = [p for p in parts if p]
                if not parts:
                    continue
                
                week_time = parts[2] if len(parts) > 2 else ""
                period_match = re.search(r"\[(\d+-\d+)\]", week_time)
                period = f"第{period_match.group(1)}节" if period_match else slot_fallback.get(slot_key, "")
                
                schedule[day].append({
                    "section": section_map.get(slot_key, ""),
                    "period": period,
                    "course": parts[0],
                    "teacher": parts[1] if len(parts) > 1 else "",
                    "time": week_time,
                    "location": parts[3] if len(parts) > 3 and parts[3] else "未标注",
                })
    
    for day, items in schedule.items():
        items.sort(key=lambda r: slot_order.get(r.get("period", "")[1] if len(r.get("period", "")) > 1 else "", 99))
    
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "schedule": schedule}


def parse_schedule_list(html_text: str) -> dict[str, Any]:
    """解析列表格式的课表（新接口返回的格式）。"""
    doc = html.fromstring(html_text)
    
    rows = doc.xpath("//tbody/tr")
    if not rows:
        raise ValueError("未找到课程数据")
    
    # 按星期整理课程
    schedule: dict[str, list[dict[str, str]]] = {day: [] for day in WEEKDAY_CN}
    
    for row in rows:
        tds = row.xpath("./td")
        if len(tds) < 11:
            continue
        
        # 提取课程信息
        course_name = re.sub(r'\[.*?\]', '', tds[2].text_content()).strip()
        teacher = re.sub(r'\[.*?\]', '', tds[6].text_content()).strip()
        time_location = tds[10].text_content().strip()
        
        # 解析时间，提取星期和节次
        # 格式: "1-18周 三[6-8] 7号教学楼7103(154)" 或 "1-18周 一[1-2] 金明综合楼6101(178)；1-18周 三[3-4]"
        time_parts = time_location.split('；')  # 可能有多个时间段
        
        for part in time_parts:
            # 匹配 "周 X[节次]" 格式
            match = re.search(r'周\s*([一二三四五六日])\[(\d+-?\d*)\]', part)
            if match:
                day_map = {"一": "星期一", "二": "星期二", "三": "星期三", "四": "星期四", "五": "星期五", "六": "星期六", "日": "星期日"}
                day_cn = day_map.get(match.group(1), "")
                period = match.group(2)
                
                # 提取地点（在]之后）
                location = ""
                if ']' in part:
                    after_bracket = part.split(']')[-1].strip()
                    # 去除周次信息
                    location = re.sub(r'^\d+-\d+周\s*', '', after_bracket).strip()
                
                if day_cn and day_cn in schedule:
                    schedule[day_cn].append({
                        "section": "",
                        "period": f"第{period}节",
                        "course": course_name,
                        "teacher": teacher,
                        "time": part.strip(),
                        "location": location if location else "未标注",
                    })
    
    # 按节次排序
    def period_key(item):
        period = item.get("period", "")
        match = re.search(r'(\d+)', period)
        return int(match.group(1)) if match else 99
    
    for day in schedule:
        schedule[day].sort(key=period_key)
    
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "schedule": schedule}


def save_clean_schedule(data: dict[str, Any]) -> dict[str, str]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    latest_json = OUTPUT_DIR / "schedule_clean_latest.json"
    latest_md = OUTPUT_DIR / "schedule_clean_latest.md"
    
    # 生成 Markdown
    lines = [f"# 课表整理（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）", ""]
    for day in WEEKDAY_CN:
        lines.append(f"### {day}")
        day_items = data.get("schedule", {}).get(day, [])
        if not day_items:
            lines.append("- 当天无课程安排。")
        for item in day_items:
            lines.append(f"- {item.get('section', '')}（{item.get('period', '')}）")
            lines.append(f"  - 课程：{item.get('course', '')}")
            lines.append(f"  - 老师：{item.get('teacher', '')}")
            lines.append(f"  - 时间：{item.get('time', '')}")
            lines.append(f"  - 地点：{item.get('location', '')}")
    
    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    md_text = "\n".join(lines)
    
    latest_json.write_text(json_text, encoding="utf-8")
    latest_md.write_text(md_text, encoding="utf-8")
    
    return {"json": str(latest_json), "md": str(latest_md)}


# ===== 节次时间管理 =====
def load_period_times() -> dict[str, dict[str, str]]:
    if PERIOD_TIME_FILE.exists():
        try:
            data = json.loads(PERIOD_TIME_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cleaned = {}
                for k, v in data.items():
                    if isinstance(v, dict):
                        start, end = str(v.get("start", "")).strip(), str(v.get("end", "")).strip()
                        if _is_hhmm(start) and _is_hhmm(end):
                            cleaned[str(k)] = {"start": start, "end": end}
                if cleaned:
                    return cleaned
        except Exception:
            pass
    
    PERIOD_TIME_FILE.write_text(json.dumps(DEFAULT_PERIOD_TIMES, ensure_ascii=False, indent=2), encoding="utf-8")
    return dict(DEFAULT_PERIOD_TIMES)


def save_period_times(period_times: dict[str, dict[str, str]]) -> None:
    PERIOD_TIME_FILE.write_text(json.dumps(period_times, ensure_ascii=False, indent=2), encoding="utf-8")


# ===== 功能函数 =====

def setup_account(student_id: str, password: str, library_location: str = "", library_seat_no: str = "") -> dict[str, Any]:
    """保存账号配置并验证登录。"""
    sid, pwd = str(student_id).strip(), str(password)
    if not sid or not pwd:
        return {"success": False, "msg": "student_id/password 不能为空"}
    
    client = HenuXkClient(sid, pwd, load_json(COOKIE_FILE) or None)
    if not client.login():
        return {"success": False, "msg": "登录失败，账号或密码可能错误"}
    
    save_json(COOKIE_FILE, client.get_cookies())
    
    profile = {"student_id": sid, "password": pwd}
    if library_location:
        profile["library_location"] = str(library_location).strip()
    if library_seat_no:
        profile["library_seat_no"] = str(library_seat_no).strip()
    save_json(PROFILE_FILE, profile)
    
    return {"success": True, "msg": "账号已保存", "student_id": sid}


def sync_schedule(xn: str | None = None, xq: str | None = None) -> dict[str, Any]:
    """同步课表（使用已保存账号）。"""
    import base64
    
    profile = load_json(PROFILE_FILE)
    sid, pwd = str(profile.get("student_id", "")), str(profile.get("password", ""))
    if not sid or not pwd:
        return {"success": False, "msg": "缺少账号，请先执行 setup_account"}
    
    client = HenuXkClient(sid, pwd, load_json(COOKIE_FILE) or None)
    if not client.login():
        return {"success": False, "msg": "登录失败"}
    
    save_json(COOKIE_FILE, client.get_cookies())
    context = client.fetch_user_context()
    
    # 获取目标学年学期
    target_xn = str(xn or context.get("current_xn") or "").strip()
    target_xq = str(xq or context.get("current_xq") or "").strip()
    
    if not target_xn or not target_xq:
        return {"success": False, "msg": "无法获取当前学年学期，请手动指定"}
    
    # 使用正确的课表数据接口
    params = f"xn={target_xn}&xq={target_xq}&xh={sid}"
    params_b64 = base64.b64encode(params.encode()).decode()
    schedule_url = f"{client.base_url}/wsxk/xkjg.ckdgxsxdkchj_data10319.jsp?params={params_b64}"
    
    referer = f"{client.base_url}/student/xkjg.wdkb.jsp?menucode=S20301"
    schedule_entry = client.fetch_page(schedule_url, referer=referer)
    
    if schedule_entry["invalid_auth"]:
        return {"success": False, "msg": "会话失效"}
    
    # 尝试解析并抓取课表数据
    try:
        # 保存原始页面
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        grid_file = OUTPUT_DIR / f"schedule_grid_{ts}.html"
        grid_file.write_text(schedule_entry["text"], encoding="utf-8")
        
        # 解析课表
        parsed = parse_schedule_grid(schedule_entry["text"])
        files = save_clean_schedule(parsed)
        
        return {
            "success": True,
            "msg": "课表同步完成",
            "term": {"xn": target_xn, "xq": target_xq},
            "files": files,
            "course_count": sum(len(items) for items in parsed.get("schedule", {}).values()),
        }
    except Exception as e:
        return {"success": False, "msg": f"解析课表失败: {e}", "raw_file": str(grid_file) if 'grid_file' in dir() else None}


def current_course(timezone: str = "Asia/Shanghai") -> dict[str, Any]:
    """获取当前正在上的课和下一节课。"""
    try:
        data = json.loads((OUTPUT_DIR / "schedule_clean_latest.json").read_text(encoding="utf-8"))
    except Exception:
        return {"success": False, "msg": "未找到课表，请先执行 sync_schedule"}
    
    period_times = load_period_times()
    now = _now_dt(timezone)
    weekday_cn = WEEKDAY_CN[now.weekday()]
    day_courses = data.get("schedule", {}).get(weekday_cn, [])
    now_minutes = now.hour * 60 + now.minute
    
    current, future = [], []
    for row in day_courses:
        period_text = str(row.get("period", ""))
        m = re.search(r"第(\d+)(?:-(\d+))?节", period_text)
        if not m:
            continue
        start_idx, end_idx = int(m.group(1)), int(m.group(2) or m.group(1))
        
        start_cfg, end_cfg = period_times.get(str(start_idx)), period_times.get(str(end_idx))
        if not start_cfg or not end_cfg:
            continue
        
        start_min = _to_minutes(start_cfg["start"])
        end_min = _to_minutes(end_cfg["end"])
        
        course_info = {**row, "clock_start": start_cfg["start"], "clock_end": end_cfg["end"]}
        
        if start_min <= now_minutes <= end_min:
            current.append(course_info)
        elif now_minutes < start_min:
            future.append((start_min, course_info))
    
    future.sort()
    next_course = future[0][1] if future else None
    
    return {
        "success": True,
        "now": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": weekday_cn,
        "current_courses": current,
        "next_course": next_course,
    }


def latest_schedule() -> dict[str, Any]:
    """获取最新结构化课表。"""
    try:
        data = json.loads((OUTPUT_DIR / "schedule_clean_latest.json").read_text(encoding="utf-8"))
        return {"success": True, "schedule": data.get("schedule", {})}
    except Exception as e:
        return {"success": False, "msg": str(e)}


def library_locations() -> dict[str, Any]:
    """查看图书馆可预约区域列表。"""
    if HenuLibraryBot is None:
        return {"success": False, "msg": "图书馆模块不可用", "locations": []}
    return {"success": True, "locations": [
        {"location": name, "area_id": str(area_id)} 
        for name, area_id in HenuLibraryBot.LOCATIONS.items()
    ]}


def library_reserve(location: str = "", seat_no: str = "", target_date: str = "", preferred_time: str = "08:00") -> dict[str, Any]:
    """预约图书馆座位。"""
    if HenuLibraryBot is None:
        return {"success": False, "msg": "图书馆模块不可用"}
    
    profile = load_json(PROFILE_FILE)
    sid, pwd = str(profile.get("student_id", "")), str(profile.get("password", ""))
    if not sid or not pwd:
        return {"success": False, "msg": "缺少账号"}
    
    # 使用默认值
    target_location = str(location or profile.get("library_location", "")).strip()
    target_seat = str(seat_no or profile.get("library_seat_no", "")).strip()
    
    if not target_location or not target_seat:
        return {"success": False, "msg": "请提供 location/seat_no 或在 setup_account 中设置默认值"}
    
    # 日期默认为明天
    if not target_date:
        target_date = (_now_dt().date() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 构建 bot 并预约
    stored = load_json(LIBRARY_COOKIE_FILE)
    bot = HenuLibraryBot(sid, pwd, stored or None)
    
    if not bot.login():
        return {"success": False, "msg": "图书馆登录失败"}
    
    save_json(LIBRARY_COOKIE_FILE, bot.get_cookies())
    result = bot.reserve(target_location, target_seat, target_date, preferred_time=str(preferred_time or "08:00"))
    save_json(LIBRARY_COOKIE_FILE, bot.get_cookies())
    
    return {"success": result.get("success"), "msg": result.get("msg", ""), "date": target_date}


def library_records(record_type: str = "1", page: int = 1, limit: int = 20) -> dict[str, Any]:
    """查询图书馆预约记录。"""
    if HenuLibraryBot is None:
        return {"success": False, "msg": "图书馆模块不可用", "records": []}
    
    profile = load_json(PROFILE_FILE)
    sid, pwd = str(profile.get("student_id", "")), str(profile.get("password", ""))
    if not sid or not pwd:
        return {"success": False, "msg": "缺少账号", "records": []}
    
    stored = load_json(LIBRARY_COOKIE_FILE)
    bot = HenuLibraryBot(sid, pwd, stored or None)
    if not bot.login():
        return {"success": False, "msg": "图书馆登录失败", "records": []}
    
    save_json(LIBRARY_COOKIE_FILE, bot.get_cookies())
    return bot.list_seat_records(record_type=record_type, page=page, limit=limit)


def library_cancel(record_id: str, record_type: str = "1") -> dict[str, Any]:
    """取消图书馆预约。record_type: 1(普通)/3(研习)/4(考研)，默认1"""
    if HenuLibraryBot is None:
        return {"success": False, "msg": "图书馆模块不可用"}
    
    profile = load_json(PROFILE_FILE)
    sid, pwd = str(profile.get("student_id", "")), str(profile.get("password", ""))
    if not sid or not pwd:
        return {"success": False, "msg": "缺少账号"}
    
    stored = load_json(LIBRARY_COOKIE_FILE)
    bot = HenuLibraryBot(sid, pwd, stored or None)
    if not bot.login():
        return {"success": False, "msg": "图书馆登录失败"}
    
    save_json(LIBRARY_COOKIE_FILE, bot.get_cookies())
    result = bot.cancel_seat_record(record_id=str(record_id), record_type=str(record_type or "1"))
    save_json(LIBRARY_COOKIE_FILE, bot.get_cookies())
    return result


def system_status() -> dict[str, Any]:
    """查看系统状态。"""
    profile = load_json(PROFILE_FILE)
    return {
        "success": True,
        "account": {
            "student_id": profile.get("student_id", ""),
            "has_password": bool(profile.get("password")),
            "library_location": profile.get("library_location", ""),
            "library_seat_no": profile.get("library_seat_no", ""),
        },
        "library_available": HenuLibraryBot is not None,
        "output_dir": str(OUTPUT_DIR),
    }


if __name__ == "__main__":
    # 这个文件现在作为模块被CLI调用，不再直接运行MCP服务器
    print("请使用 henu_cli.py 来调用功能")

