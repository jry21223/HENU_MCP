#!/usr/bin/env python3
"""
HENU Campus Assistant CLI for OpenClaw
河南大学校园助手命令行接口
"""

import argparse
import json
import sys
from pathlib import Path

# 导入 Skill API 包装层（与 mcp_server 能力对齐）
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from henu_campus_mcp import (
    setup_account,
    sync_schedule,
    current_course,
    latest_schedule,
    latest_schedule_current_week,
    library_locations,
    library_reserve,
    library_records,
    library_cancel,
    set_calibration_source,
    system_status,
)


def main():
    parser = argparse.ArgumentParser(description="河南大学校园助手")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 账号设置
    setup_parser = subparsers.add_parser("setup_account", help="设置账号")
    setup_parser.add_argument("--student_id", required=True, help="学号")
    setup_parser.add_argument("--password", required=True, help="密码")
    setup_parser.add_argument("--library_location", default="", help="默认图书馆区域")
    setup_parser.add_argument("--library_seat_no", default="", help="默认座位号")
    setup_parser.add_argument(
        "--no_verify_login",
        action="store_true",
        help="仅保存账号，不立即验证登录",
    )
    setup_parser.add_argument(
        "--no_calibrate_period_time",
        action="store_true",
        help="初始化时不自动校准节次时间",
    )

    # 课表功能
    sync_parser = subparsers.add_parser("sync_schedule", help="同步课表")
    sync_parser.add_argument("--xn", default=None, help="学年")
    sync_parser.add_argument("--xq", default=None, help="学期")
    sync_parser.add_argument(
        "--no_auto_calibrate",
        action="store_true",
        help="同步前不执行自动节次校准",
    )

    current_parser = subparsers.add_parser("current_course", help="查询当前课程")
    current_parser.add_argument("--timezone", default="Asia/Shanghai", help="时区")
    current_parser.add_argument(
        "--no_auto_calibrate",
        action="store_true",
        help="查询前不执行自动节次校准",
    )

    subparsers.add_parser("latest_schedule", help="获取完整课表")

    latest_week_parser = subparsers.add_parser(
        "latest_schedule_current_week", help="获取本周课表（按周次过滤）"
    )
    latest_week_parser.add_argument("--timezone", default="Asia/Shanghai", help="时区")

    # 图书馆功能
    subparsers.add_parser("library_locations", help="查看图书馆区域")

    reserve_parser = subparsers.add_parser("library_reserve", help="预约座位")
    reserve_parser.add_argument("--location", default="", help="区域名")
    reserve_parser.add_argument("--seat_no", default="", help="座位号")
    reserve_parser.add_argument("--target_date", default="", help="日期 YYYY-MM-DD")
    reserve_parser.add_argument("--preferred_time", default="08:00", help="开始时间")

    records_parser = subparsers.add_parser("library_records", help="查询预约记录")
    records_parser.add_argument("--record_type", default="1", help="记录类型")
    records_parser.add_argument("--page", type=int, default=1, help="页码")
    records_parser.add_argument("--limit", type=int, default=20, help="每页数量")

    cancel_parser = subparsers.add_parser("library_cancel", help="取消预约")
    cancel_parser.add_argument("--record_id", required=True, help="记录ID")
    cancel_parser.add_argument("--record_type", default="auto", help="记录类型")

    # 节次校准源
    calibration_parser = subparsers.add_parser(
        "set_calibration_source", help="设置喜鹊节次校准请求参数"
    )
    calibration_parser.add_argument("--data", required=True, help="抓包 data 参数")
    calibration_parser.add_argument("--cookie", required=True, help="抓包 cookie")
    calibration_parser.add_argument(
        "--user_agent",
        default="KingoPalm/2.6.449 (iPhone; iOS 26.3; Scale/3.00)",
        help="请求 User-Agent",
    )

    # 系统状态
    system_parser = subparsers.add_parser("system_status", help="查看系统状态")
    system_parser.add_argument("--timezone", default="Asia/Shanghai", help="时区")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行对应命令
    try:
        if args.command == "setup_account":
            result = setup_account(
                student_id=args.student_id,
                password=args.password,
                library_location=args.library_location,
                library_seat_no=args.library_seat_no,
                verify_login=not args.no_verify_login,
                calibrate_period_time=not args.no_calibrate_period_time,
            )
        elif args.command == "sync_schedule":
            result = sync_schedule(
                xn=args.xn,
                xq=args.xq,
                auto_calibrate=not args.no_auto_calibrate,
            )
        elif args.command == "current_course":
            result = current_course(
                timezone=args.timezone,
                auto_calibrate=not args.no_auto_calibrate,
            )
        elif args.command == "latest_schedule":
            result = latest_schedule()
        elif args.command == "latest_schedule_current_week":
            result = latest_schedule_current_week(timezone=args.timezone)
        elif args.command == "library_locations":
            result = library_locations()
        elif args.command == "library_reserve":
            result = library_reserve(
                location=args.location,
                seat_no=args.seat_no,
                target_date=args.target_date,
                preferred_time=args.preferred_time,
            )
        elif args.command == "library_records":
            result = library_records(
                record_type=args.record_type,
                page=args.page,
                limit=args.limit,
            )
        elif args.command == "library_cancel":
            result = library_cancel(record_id=args.record_id, record_type=args.record_type)
        elif args.command == "set_calibration_source":
            result = set_calibration_source(
                data=args.data,
                cookie=args.cookie,
                user_agent=args.user_agent,
            )
        elif args.command == "system_status":
            result = system_status(timezone=args.timezone)
        else:
            print(f"未知命令: {args.command}")
            return

        # 输出结果
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(
            json.dumps(
                {"success": False, "msg": f"执行失败: {str(e)}"},
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
