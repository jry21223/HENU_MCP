from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from lxml import html


WEEKDAY_ORDER = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
SLOT_FALLBACK = {"一": "第1-2节", "二": "第3-4节", "三": "第6-7节", "四": "第9-10节", "五": "第11-12节"}
SLOT_ORDER = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5}
SECTION_MAP = {"上午": "上午", "下午": "下午", "晚上": "晚上"}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _norm_no_space(text: str) -> str:
    return re.sub(r"\s+", "", text or "").strip()


def _extract_meta(doc: html.HtmlElement) -> dict[str, str]:
    meta: dict[str, str] = {}
    info_tables = doc.xpath("(//table)[1]")
    if not info_tables:
        return meta

    texts = [_norm("".join(td.xpath(".//text()"))) for td in info_tables[0].xpath(".//tr/td")]
    for item in texts:
        if "学号：" in item:
            meta["student_id"] = item.split("学号：", 1)[1].strip()
        elif "姓名：" in item:
            meta["name"] = item.split("姓名：", 1)[1].strip()
        elif "所在班级：" in item:
            meta["class_name"] = item.split("所在班级：", 1)[1].strip()
        elif "课程门数：" in item:
            meta["summary"] = item
    return meta


def _extract_weekdays(table: html.HtmlElement) -> list[str]:
    rows = table.xpath(".//tr")
    if not rows:
        return []
    header_cells = rows[0].xpath("./td")[1:]
    weekdays = [_norm_no_space("".join(td.xpath(".//text()"))) for td in header_cells]
    weekdays = [item for item in weekdays if item]
    return weekdays


def _period_from_slot(slot_key: str, week_time: str) -> str:
    match = re.search(r"\[(\d+-\d+)\]", week_time or "")
    if match:
        return f"第{match.group(1)}节"
    return SLOT_FALLBACK.get(slot_key, "")


def parse_schedule_grid_html(html_text: str) -> dict[str, Any]:
    doc = html.fromstring(html_text)
    tables = doc.xpath("//table[@id='mytable']")
    if not tables:
        raise ValueError("未找到课表主表格(id=mytable)")

    table = tables[0]
    rows = table.xpath(".//tr")
    weekdays = _extract_weekdays(table)
    if not weekdays:
        raise ValueError("未解析到星期表头")

    schedule: dict[str, list[dict[str, str]]] = {day: [] for day in weekdays}

    for row in rows[1:]:
        tds = row.xpath("./td")
        if not tds:
            continue

        cell0 = _norm_no_space("".join(tds[0].xpath(".//text()")))
        if cell0 == "中午":
            continue

        section = ""
        slot_key = ""
        start_idx = 1

        if cell0 in SECTION_MAP:
            section = SECTION_MAP[cell0]
            slot_key = _norm_no_space("".join(tds[1].xpath(".//text()"))) if len(tds) > 1 else ""
            start_idx = 2
        else:
            slot_key = cell0
            if slot_key in ("一", "二"):
                section = "上午"
            elif slot_key in ("三", "四"):
                section = "下午"
            elif slot_key == "五":
                section = "晚上"

        if slot_key not in SLOT_FALLBACK:
            continue

        weekday_cells = tds[start_idx : start_idx + len(weekdays)]
        for idx, td in enumerate(weekday_cells):
            day = weekdays[idx]
            blocks = td.xpath(".//div[.//font]")
            if not blocks:
                continue

            for block in blocks:
                parts = [_norm(x) for x in block.xpath(".//text()")]
                parts = [item for item in parts if item]
                if not parts:
                    continue

                course = parts[0]
                teacher = parts[1] if len(parts) > 1 else ""
                week_time = parts[2] if len(parts) > 2 else ""
                location = parts[3] if len(parts) > 3 and parts[3] else "未标注"

                schedule[day].append(
                    {
                        "section": section,
                        "period": _period_from_slot(slot_key, week_time),
                        "period_key": slot_key,
                        "course": course,
                        "teacher": teacher,
                        "time": week_time,
                        "location": location,
                    }
                )

    for day, items in schedule.items():
        items.sort(key=lambda row: SLOT_ORDER.get(row.get("period_key", ""), 99))

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "meta": _extract_meta(doc),
        "schedule": schedule,
    }


def render_schedule_markdown(schedule_data: dict[str, Any]) -> str:
    meta = schedule_data.get("meta") or {}
    schedule = schedule_data.get("schedule") or {}

    lines: list[str] = [f"# 课表整理（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）"]
    if meta:
        lines.append("")
        lines.append(f"- 学号：{meta.get('student_id', '')}")
        lines.append(f"- 姓名：{meta.get('name', '')}")
        lines.append(f"- 班级：{meta.get('class_name', '')}")
        if meta.get("summary"):
            lines.append(f"- 概览：{meta['summary']}")

    for day in WEEKDAY_ORDER:
        lines.append("")
        lines.append(f"### {day}")
        day_items = schedule.get(day, [])
        if not day_items:
            lines.append("- 当天无课程安排。")
            continue
        for item in day_items:
            lines.append(f"- {item.get('section', '')}（{item.get('period', '')}）")
            lines.append(f"  - 课程：{item.get('course', '')}")
            lines.append(f"  - 老师：{item.get('teacher', '')}")
            lines.append(f"  - 时间：{item.get('time', '')}")
            lines.append(f"  - 地点：{item.get('location', '')}")

    return "\n".join(lines)


def save_clean_files(
    output_dir: Path,
    source_file: str,
    schedule_data: dict[str, Any],
    timestamp: str | None = None,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    schedule_data = dict(schedule_data)
    schedule_data["source_file"] = source_file

    latest_json = output_dir / "schedule_clean_latest.json"
    latest_md = output_dir / "schedule_clean_latest.md"
    stamped_json = output_dir / f"schedule_clean_{ts}.json"
    stamped_md = output_dir / f"schedule_clean_{ts}.md"

    md_text = render_schedule_markdown(schedule_data)
    json_text = json.dumps(schedule_data, ensure_ascii=False, indent=2)

    latest_json.write_text(json_text, encoding="utf-8")
    latest_md.write_text(md_text, encoding="utf-8")
    stamped_json.write_text(json_text, encoding="utf-8")
    stamped_md.write_text(md_text, encoding="utf-8")

    return {
        "clean_schedule_json": str(latest_json),
        "clean_schedule_md": str(latest_md),
        "clean_schedule_json_stamped": str(stamped_json),
        "clean_schedule_md_stamped": str(stamped_md),
    }


def clean_schedule_grid_file(grid_file: str | Path, output_dir: str | Path) -> dict[str, Any]:
    grid_path = Path(grid_file)
    if not grid_path.exists():
        raise FileNotFoundError(f"文件不存在: {grid_path}")

    html_text = grid_path.read_text(encoding="utf-8", errors="ignore")
    parsed = parse_schedule_grid_html(html_text)
    files = save_clean_files(Path(output_dir), str(grid_path), parsed)
    return {"data": parsed, "files": files}


def load_latest_clean_schedule(output_dir: str | Path) -> dict[str, Any]:
    latest = Path(output_dir) / "schedule_clean_latest.json"
    if not latest.exists():
        raise FileNotFoundError(f"未找到: {latest}")
    return json.loads(latest.read_text(encoding="utf-8"))
