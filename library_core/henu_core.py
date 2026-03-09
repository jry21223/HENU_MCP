import base64
import datetime as dt
import json
import math
import random
import re
from typing import Any

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


class HenuLibraryBot:
    # 常用区域映射（可继续补充）；不在映射内时会尝试按当天区域列表模糊匹配
    LOCATIONS = {
        "二楼南附楼走廊": "8",
        "二楼北附楼走廊": "9",
        "二楼大厅走廊": "10",
        "201经管教外文阅览室": "11",
        "202自然科学阅览室": "12",
        "208过刊阅览室": "13",
        "209报纸阅览室": "14",
        "三层南附楼走廊": "15",
        "三层北附楼走廊": "16",
        "三楼北附楼走廊": "16",
        "三楼大厅走廊": "17",
        "读书室": "18",
        "四层南附楼走廊": "22",
        "四楼大厅走廊": "22",
        "四层北附楼走廊": "23",
        "401医学生物数理化书库": "23",
        "501经管教外文书库": "24",
        "502科学技术书库": "25",
        "五层走廊": "26",
        "五楼大厅走廊": "26",
        "601社会科学书库": "27",
        "602文学语言艺术书库": "28",
        "701七层南自习室": "30",
        "702七层北自习室": "31",
        "东馆社会科学阅览室": "38",
        "东馆文学艺术阅览室": "42",
        "东馆素质教育阅览室": "45",
        "103期刊阅览室": "62",
        "104期刊阅览室": "63",
        "109期刊阅览室": "64",
        "金明三楼南走廊": "15",
        "金明三楼北走廊": "16",
        "金明三楼走廊": "17",
        "金明四楼走廊": "22",
        "金明四楼书库": "23",
        "金明五楼走廊": "26",
        "金明七层南自习": "30",
        "金明七层北自习": "31",
        "明伦二层借书": "67",
        "明伦三层现刊": "41",
        "明伦三层报纸": "40",
        "明伦三层借书": "39",
        "明伦四层第一": "43",
        "明伦四层第二": "44",
        "明伦四层第三": "47",
    }

    AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
    API_IV = "ZZWBKJ_ZHIHUAWEI"
    RECORD_TYPE_ALIASES = {
        "1": "1",
        "normal": "1",
        "seat": "1",
        "普通": "1",
        "普通座位": "1",
        "3": "3",
        "study": "3",
        "研习": "3",
        "研习座位": "3",
        "4": "4",
        "exam": "4",
        "考研": "4",
        "考研座位": "4",
    }

    def __init__(self, username: str, password: str, saved_cookies: dict[str, Any] | None = None):
        self.username = str(username).strip()
        self.password = password or ""
        self.base_url = "https://zwyy.henu.edu.cn"
        self.cas_login_url = "https://ids.henu.edu.cn/authserver/login"
        self.token = ""

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.base_url}/h5/index.html#/home",
            }
        )

        if saved_cookies:
            cookie_data = dict(saved_cookies)
            self.token = str(cookie_data.pop("_v4_token", "") or "")
            if cookie_data:
                self.session.cookies.update(cookie_data)

        self._set_auth_header()

    def get_cookies(self) -> dict[str, Any]:
        cookies = self.session.cookies.get_dict()
        if self.token:
            cookies["_v4_token"] = self.token
        return cookies

    def _random_string(self, length: int) -> str:
        return "".join(
            self.AES_CHARS[math.floor(random.random() * len(self.AES_CHARS))]
            for _ in range(length)
        )

    def _encrypt_password(self, password: str, salt: str) -> str:
        random_prefix = self._random_string(64)
        iv_str = self._random_string(16)
        text = random_prefix + password
        key_bytes = salt.encode("utf-8")
        iv_bytes = iv_str.encode("utf-8")
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        return base64.b64encode(cipher.encrypt(pad(text.encode("utf-8"), AES.block_size))).decode("utf-8")

    def _api_aes_key(self) -> bytes:
        date_text = dt.datetime.now().strftime("%Y%m%d")
        return f"{date_text}{date_text[::-1]}".encode("utf-8")

    def _encrypt_api_payload(self, data: dict[str, Any]) -> str:
        plain = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        cipher = AES.new(self._api_aes_key(), AES.MODE_CBC, self.API_IV.encode("utf-8"))
        encrypted = cipher.encrypt(pad(plain, AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    def _set_auth_header(self) -> None:
        if self.token:
            self.session.headers["authorization"] = f"bearer{self.token}"
        else:
            self.session.headers.pop("authorization", None)

    @staticmethod
    def _resp_msg(resp: dict[str, Any], fallback: str = "未知返回结果") -> str:
        return str(resp.get("message") or resp.get("msg") or fallback)

    @staticmethod
    def _extract_cas_ticket(url: str) -> str:
        if "#/cas/?cas=" in url:
            return url.split("#/cas/?cas=", 1)[1].split("&", 1)[0]
        match = re.search(r"[?&]cas=([^&#]+)", url)
        return match.group(1) if match else ""

    def _post_json(
        self,
        path: str,
        data: dict[str, Any],
        is_crypto: bool = False,
        allow_reauth: bool = True,
    ) -> dict[str, Any]:
        payload = {"aesjson": self._encrypt_api_payload(data)} if is_crypto else data
        resp = self.session.post(f"{self.base_url}{path}", json=payload, timeout=25)
        result = resp.json()

        if (
            allow_reauth
            and result.get("code") == 10001
            and self.password
            and not path.startswith("/v4/login/")
        ):
            # token 过期时自动重登一次并重试原请求
            if self.login():
                retry_payload = {"aesjson": self._encrypt_api_payload(data)} if is_crypto else data
                retry_resp = self.session.post(f"{self.base_url}{path}", json=retry_payload, timeout=25)
                return retry_resp.json()
        return result

    def _exchange_cas_ticket(self, cas_ticket: str) -> bool:
        if not cas_ticket:
            return False
        try:
            resp = self._post_json("/v4/login/user", {"cas": cas_ticket}, allow_reauth=False)
        except Exception:
            return False
        if resp.get("code") != 0:
            return False
        token = ((resp.get("data") or {}).get("member") or {}).get("token") or ""
        self.token = str(token)
        self._set_auth_header()
        return bool(self.token)

    def _is_token_valid(self) -> bool:
        if not self.token:
            return False
        try:
            check_day = dt.date.today().strftime("%Y-%m-%d")
            resp = self._post_json("/v4/space/pick", {"date": check_day}, allow_reauth=False)
            code = resp.get("code")
            msg = str(resp.get("message") or resp.get("msg") or "")
            if code == 10001 or "尚未登录" in msg:
                return False
            return True
        except Exception:
            return False

    def login(self) -> bool:
        # 1) 先试缓存 token
        if self._is_token_valid():
            return True

        self.token = ""
        self._set_auth_header()

        service_url = f"{self.base_url}/v4/login/cas"
        cas_auth_url = f"{self.cas_login_url}?service={service_url}"
        original_content_type = self.session.headers.pop("Content-Type", None)

        try:
            # 2) 先尝试 TGT 免密跳转
            try:
                resp = self.session.get(cas_auth_url, allow_redirects=True, timeout=25)
                cas_ticket = self._extract_cas_ticket(resp.url)
                if cas_ticket and self._exchange_cas_ticket(cas_ticket):
                    return True
            except Exception:
                pass

            if not self.password:
                return False

            # 3) 密码登录 CAS
            try:
                login_page = self.session.get(cas_auth_url, timeout=25)
                execution_match = re.search(r'name="execution" value="(.*?)"', login_page.text)
                salt_match = re.search(r'id="pwdEncryptSalt" value="(.*?)"', login_page.text)
                if not execution_match or not salt_match:
                    return False

                form_data = {
                    "username": self.username,
                    "password": self._encrypt_password(self.password, salt_match.group(1)),
                    "captcha": "",
                    "_eventId": "submit",
                    "cllt": "userNameLogin",
                    "dllt": "generalLogin",
                    "lt": "",
                    "execution": execution_match.group(1),
                }

                login_resp = self.session.post(
                    login_page.url,
                    data=form_data,
                    allow_redirects=True,
                    timeout=25,
                )
                cas_ticket = self._extract_cas_ticket(login_resp.url)
                return self._exchange_cas_ticket(cas_ticket)
            except Exception:
                return False
        finally:
            if original_content_type:
                self.session.headers["Content-Type"] = original_content_type

    @staticmethod
    def _to_hhmm(raw_time: Any) -> str:
        if raw_time is None:
            return ""
        text = str(raw_time).strip()
        match = re.search(r"(\d{2}:\d{2})", text)
        return match.group(1) if match else text

    @staticmethod
    def _time_to_minutes(raw_time: Any) -> int | None:
        hhmm = HenuLibraryBot._to_hhmm(raw_time)
        if not hhmm:
            return None
        try:
            hour, minute = hhmm.split(":")
            return int(hour) * 60 + int(minute)
        except Exception:
            return None

    @staticmethod
    def _normalize_seat_no(value: Any) -> str:
        text = str(value or "").strip()
        return text.lstrip("0") or "0"

    def _fetch_pick_areas(self, target_date: str) -> list[dict[str, Any]]:
        resp = self._post_json("/v4/space/pick", {"date": target_date})
        if resp.get("code") != 0:
            raise RuntimeError(self._resp_msg(resp, "获取区域列表失败"))
        return ((resp.get("data") or {}).get("area") or [])

    def _resolve_area(self, location_name: str, target_date: str) -> tuple[str, str]:
        location = str(location_name or "").strip()
        if not location:
            raise RuntimeError("区域名称不能为空")

        if location.isdigit():
            return location, location

        if location in self.LOCATIONS:
            return str(self.LOCATIONS[location]), location

        areas = self._fetch_pick_areas(target_date)

        for area in areas:
            if location == str(area.get("name", "")).strip():
                return str(area.get("id")), str(area.get("name"))

        for area in areas:
            area_name = str(area.get("name", "")).strip()
            if location and (location in area_name or area_name in location):
                return str(area.get("id")), area_name

        raise RuntimeError(f"区域 '{location}' 未找到，请检查名称")

    def _get_space_map(self, area_id: str) -> dict[str, Any]:
        resp = self._post_json("/v4/Space/map", {"id": str(area_id)})
        if resp.get("code") != 0:
            raise RuntimeError(self._resp_msg(resp, "获取区域详情失败"))
        data = resp.get("data") or {}
        if not data:
            raise RuntimeError("区域详情为空")
        return data

    @staticmethod
    def _pick_date_row(date_list: list[dict[str, Any]], target_date: str) -> dict[str, Any] | None:
        for row in date_list:
            if str(row.get("day")) == target_date:
                return row
        for row in date_list:
            day = str(row.get("day") or "")
            if day and day >= target_date:
                return row
        return date_list[0] if date_list else None

    def _get_study_period(self, area_id: str, target_date: str) -> dict[str, Any]:
        resp = self._post_json("/v4/member/checkStudyOpenTime", {"area": str(area_id)})
        if resp.get("code") != 0:
            raise RuntimeError(self._resp_msg(resp, "获取可预约周期失败"))
        periods = resp.get("data") or []
        if not periods:
            raise RuntimeError("可预约周期为空")
        for item in periods:
            start_day = str(item.get("startDay") or "")
            end_day = str(item.get("endDay") or "")
            if start_day and end_day and start_day <= target_date <= end_day:
                return item
        return periods[0]

    def _build_reservation_plan(
        self,
        area_id: str,
        space_map: dict[str, Any],
        target_date: str,
        preferred_time: str | None = None,
    ) -> dict[str, Any]:
        space_type = str(space_map.get("type") or "")
        label_ids: list[Any] = []

        if space_type != "1":
            period = self._get_study_period(area_id, target_date)
            begdate = str(period.get("startDay") or "")
            enddate = str(period.get("endDay") or "")
            if not begdate or not enddate:
                raise RuntimeError("学习周期日期无效")
            return {
                "seat_query": {
                    "id": str(area_id),
                    "day": "",
                    "label_id": label_ids,
                    "start_time": "",
                    "end_time": "",
                    "begdate": begdate,
                    "enddate": enddate,
                },
                "confirm_path": "/v4/space/studyConfirm",
                "confirm_payload": {
                    "begdate": begdate,
                    "enddate": enddate,
                },
                "confirm_crypto": True,
            }

        date_cfg = space_map.get("date") or {}
        reserve_type = str(date_cfg.get("reserveType") or "")
        date_list = date_cfg.get("list") or []
        date_row = self._pick_date_row(date_list, target_date)
        if not date_row:
            raise RuntimeError(f"区域未返回 {target_date} 的开放时间")

        day = str(date_row.get("day") or target_date)
        seat_query = {
            "id": str(area_id),
            "day": day,
            "label_id": label_ids,
            "start_time": "",
            "end_time": "",
            "begdate": "",
            "enddate": "",
        }
        confirm_payload = {
            "segment": "",
            "day": day,
            "start_time": "",
            "end_time": "",
        }

        if reserve_type == "1":
            times = date_row.get("times") or []
            if not times:
                raise RuntimeError(f"{day} 未返回可预约时段")
            active_slots = [item for item in times if str(item.get("status", "1")) == "1"] or times
            first_slot = active_slots[0]
            if preferred_time:
                preferred_min = self._time_to_minutes(preferred_time)
                if preferred_min is not None:
                    for item in active_slots:
                        start_min = self._time_to_minutes(item.get("start"))
                        end_min = self._time_to_minutes(item.get("end"))
                        if start_min is None or end_min is None:
                            continue
                        if start_min <= preferred_min <= end_min:
                            first_slot = item
                            break
            seat_query["start_time"] = self._to_hhmm(first_slot.get("start"))
            seat_query["end_time"] = self._to_hhmm(first_slot.get("end"))
            confirm_payload["segment"] = str(first_slot.get("id") or "")
            if not confirm_payload["segment"]:
                raise RuntimeError("预约时段参数缺失(segment)")
        elif reserve_type == "2":
            times = date_row.get("times") or []
            if not times:
                raise RuntimeError(f"{day} 未返回可预约时点")
            time_value = times[0]
            if preferred_time:
                preferred_hhmm = self._to_hhmm(preferred_time)
                for item in times:
                    if isinstance(item, dict):
                        compare_hhmm = self._to_hhmm(
                            item.get("time") or item.get("start") or item.get("end")
                        )
                    else:
                        compare_hhmm = self._to_hhmm(item)
                    if compare_hhmm == preferred_hhmm:
                        time_value = item
                        break
            if isinstance(time_value, dict):
                time_value = (
                    time_value.get("id")
                    or time_value.get("time")
                    or time_value.get("start")
                    or time_value.get("end")
                    or ""
                )
            hhmm = self._to_hhmm(time_value)
            seat_query["start_time"] = hhmm
            seat_query["end_time"] = hhmm
            confirm_payload["end_time"] = hhmm
        elif reserve_type == "3":
            start_time = self._to_hhmm(date_row.get("def_start_time") or date_row.get("start_time"))
            end_time = self._to_hhmm(date_row.get("def_end_time") or date_row.get("end_time"))
            if not start_time or not end_time:
                raise RuntimeError("预约时间参数缺失")
            seat_query["start_time"] = start_time
            seat_query["end_time"] = end_time
            confirm_payload["start_time"] = start_time
            confirm_payload["end_time"] = end_time
        else:
            # 兜底：优先取 times[0]，否则取默认时间
            times = date_row.get("times") or []
            if times and isinstance(times[0], dict):
                seat_query["start_time"] = self._to_hhmm(times[0].get("start"))
                seat_query["end_time"] = self._to_hhmm(times[0].get("end"))
                confirm_payload["segment"] = str(times[0].get("id") or "")
            if not seat_query["start_time"]:
                seat_query["start_time"] = self._to_hhmm(date_row.get("def_start_time") or date_row.get("start_time"))
            if not seat_query["end_time"]:
                seat_query["end_time"] = self._to_hhmm(date_row.get("def_end_time") or date_row.get("end_time"))
            if not confirm_payload["segment"]:
                confirm_payload["start_time"] = seat_query["start_time"]
                confirm_payload["end_time"] = seat_query["end_time"]

        return {
            "seat_query": seat_query,
            "confirm_path": "/v4/space/confirm",
            "confirm_payload": confirm_payload,
            "confirm_crypto": True,
        }

    def _query_seats(self, seat_query_payload: dict[str, Any]) -> list[dict[str, Any]]:
        resp = self._post_json("/v4/Space/seat", seat_query_payload)
        if resp.get("code") != 0:
            raise RuntimeError(self._resp_msg(resp, "查询座位失败"))
        return ((resp.get("data") or {}).get("list") or [])

    def _find_target_seat(self, seats: list[dict[str, Any]], seat_no: str) -> dict[str, Any] | None:
        target_raw = str(seat_no).strip()
        target_norm = self._normalize_seat_no(target_raw)
        for seat in seats:
            values = [seat.get("no"), seat.get("name")]
            for raw in values:
                text = str(raw or "").strip()
                if not text:
                    continue
                if text == target_raw or self._normalize_seat_no(text) == target_norm:
                    return seat
        return None

    @classmethod
    def _normalize_record_type(cls, record_type: str | int | None) -> str:
        key = str(record_type or "1").strip().lower()
        return cls.RECORD_TYPE_ALIASES.get(key, "1")

    def list_seat_records(
        self,
        record_type: str | int = "1",
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        if not self._is_token_valid() and not self.login():
            return {"success": False, "msg": "未登录或登录失效", "records": []}

        page_value = max(1, int(page))
        limit_value = max(1, min(100, int(limit)))
        type_value = self._normalize_record_type(record_type)

        try:
            resp = self._post_json(
                "/v4/member/seat",
                {
                    "type": type_value,
                    "page": page_value,
                    "limit": limit_value,
                },
            )
            if resp.get("code") != 0:
                return {
                    "success": False,
                    "msg": self._resp_msg(resp, "查询预约记录失败"),
                    "record_type": type_value,
                    "records": [],
                }
            data = resp.get("data") or {}
            records = data.get("data") or []
            total = data.get("total")
            if total is None:
                total = len(records)
            return {
                "success": True,
                "msg": self._resp_msg(resp, "操作成功"),
                "record_type": type_value,
                "page": page_value,
                "limit": limit_value,
                "total": int(total),
                "records": records,
            }
        except Exception as exc:
            return {"success": False, "msg": f"查询预约记录异常: {exc}", "records": []}

    def cancel_seat_record(
        self,
        record_id: str | int,
        record_type: str | int = "1",
    ) -> dict[str, Any]:
        if not self._is_token_valid() and not self.login():
            return {"success": False, "msg": "未登录或登录失效"}

        record_id_text = str(record_id or "").strip()
        if not record_id_text:
            return {"success": False, "msg": "record_id 不能为空"}

        type_value = self._normalize_record_type(record_type)
        cancel_path = "/v4/space/cancel" if type_value == "1" else "/v4/space/studyCancel"

        try:
            resp = self._post_json(cancel_path, {"id": record_id_text})
            return {
                "success": resp.get("code") == 0,
                "msg": self._resp_msg(resp),
                "code": resp.get("code"),
                "record_id": record_id_text,
                "record_type": type_value,
                "cancel_path": cancel_path,
            }
        except Exception as exc:
            return {"success": False, "msg": f"取消预约异常: {exc}"}

    def reserve(
        self,
        location_name: str,
        seat_no: str,
        target_date: str,
        preferred_time: str | None = None,
    ) -> dict[str, Any]:
        try:
            dt.date.fromisoformat(target_date)
        except ValueError:
            return {"success": False, "msg": "target_date 格式必须为 YYYY-MM-DD"}

        # 避免使用过期 token 直接进入预约流程
        if not self._is_token_valid() and not self.login():
            return {"success": False, "msg": "未登录或登录失效"}

        try:
            area_id, area_name = self._resolve_area(location_name, target_date)
            space_map = self._get_space_map(area_id)
            plan = self._build_reservation_plan(area_id, space_map, target_date, preferred_time=preferred_time)
            seats = self._query_seats(plan["seat_query"])
            if not seats:
                return {"success": False, "msg": f"区域 {area_name} 在 {target_date} 没有可查询座位"}

            target_seat = self._find_target_seat(seats, seat_no)
            if not target_seat:
                return {"success": False, "msg": f"在区域 {area_name} 未找到座位号: {seat_no}"}

            if str(target_seat.get("status")) != "1":
                return {
                    "success": False,
                    "msg": f"座位 {target_seat.get('no') or seat_no} 当前不可预约",
                }

            confirm_payload = dict(plan["confirm_payload"])
            confirm_payload["seat_id"] = str(target_seat.get("id"))
            confirm_resp = self._post_json(
                plan["confirm_path"],
                confirm_payload,
                is_crypto=bool(plan.get("confirm_crypto")),
            )
            success = confirm_resp.get("code") == 0
            return {
                "success": success,
                "msg": self._resp_msg(confirm_resp),
            }
        except Exception as exc:
            return {"success": False, "msg": f"预约流程异常: {exc}"}
