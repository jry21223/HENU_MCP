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
    library_current,
    library_auto_signin,
    library_locations,
    library_reserve,
    library_records,
    library_cancel,
    seminar_groups,
    seminar_group_save,
    seminar_group_delete,
    seminar_filters,
    seminar_signin,
    seminar_auto_signin,
    seminar_signin_tasks,
    seminar_records,
    seminar_rooms,
    seminar_cancel,
    seminar_room_detail,
    seminar_reserve,
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

    subparsers.add_parser("library_current", help="查询当前预约")

    signin_parser = subparsers.add_parser("library_auto_signin", help="自动签到")
    signin_parser.add_argument("--record_id", default="", help="指定当前预约记录ID")

    records_parser = subparsers.add_parser("library_records", help="查询预约记录")
    records_parser.add_argument("--record_type", default="1", help="记录类型")
    records_parser.add_argument("--page", type=int, default=1, help="页码")
    records_parser.add_argument("--limit", type=int, default=20, help="每页数量")

    cancel_parser = subparsers.add_parser("library_cancel", help="取消预约")
    cancel_parser.add_argument("--record_id", required=True, help="记录ID")
    cancel_parser.add_argument("--record_type", default="auto", help="记录类型")

    group_list_parser = subparsers.add_parser("seminar_groups", help="查看研讨室 groups")

    group_save_parser = subparsers.add_parser("seminar_group_save", help="保存研讨室 group")
    group_save_parser.add_argument("--group_name", required=True, help="group 名称")
    group_save_parser.add_argument(
        "--member_ids",
        required=True,
        help="同行成员学号，3-9 个，不含自己，逗号/空格/换行分隔",
    )
    group_save_parser.add_argument("--note", default="", help="备注")

    group_delete_parser = subparsers.add_parser("seminar_group_delete", help="删除研讨室 group")
    group_delete_parser.add_argument("--group_name", required=True, help="group 名称")

    subparsers.add_parser("seminar_filters", help="查询研讨室筛选项")

    seminar_records_parser = subparsers.add_parser("seminar_records", help="查询研讨室预约记录")
    seminar_records_parser.add_argument("--record_type", default="1", help="记录类型，1=普通空间 2=大型空间")
    seminar_records_parser.add_argument("--mode", default="books", help="记录模式，books=预约记录 reneges=违约/取消记录")
    seminar_records_parser.add_argument("--page", type=int, default=1, help="页码")
    seminar_records_parser.add_argument("--limit", type=int, default=20, help="每页数量")

    seminar_signin_tasks_parser = subparsers.add_parser("seminar_signin_tasks", help="查看研讨室自动签到任务")
    seminar_signin_tasks_parser.add_argument("--status", default="", help="按状态过滤，支持逗号分隔")

    seminar_signin_parser = subparsers.add_parser("seminar_signin", help="签到研讨室预约")
    seminar_signin_parser.add_argument("--record_id", required=True, help="研讨室预约记录 ID")

    subparsers.add_parser("seminar_auto_signin", help="执行一次研讨室自动签到扫描")

    seminar_rooms_parser = subparsers.add_parser("seminar_rooms", help="查询研讨室列表")
    seminar_rooms_parser.add_argument("--target_date", default="", help="日期 YYYY-MM-DD")
    seminar_rooms_parser.add_argument("--members", type=int, default=0, help="人数，0 表示不筛选")
    seminar_rooms_parser.add_argument("--name", default="", help="房间名称关键词")
    seminar_rooms_parser.add_argument("--room", default="", help="房型/房间筛选值")
    seminar_rooms_parser.add_argument("--start_time", default="", help="开始时间 HH:MM")
    seminar_rooms_parser.add_argument("--end_time", default="", help="结束时间 HH:MM")
    seminar_rooms_parser.add_argument("--library_ids", default="", help="馆舍 ID 列表")
    seminar_rooms_parser.add_argument("--library_names", default="", help="馆舍名称列表")
    seminar_rooms_parser.add_argument("--floor_ids", default="", help="楼层 ID 列表")
    seminar_rooms_parser.add_argument("--floor_names", default="", help="楼层名称列表")
    seminar_rooms_parser.add_argument("--category_ids", default="", help="分类 ID 列表")
    seminar_rooms_parser.add_argument("--category_names", default="", help="分类名称列表")
    seminar_rooms_parser.add_argument("--boutique_ids", default="", help="特色标签 ID 列表")
    seminar_rooms_parser.add_argument("--boutique_names", default="", help="特色标签名称列表")
    seminar_rooms_parser.add_argument("--page", type=int, default=1, help="页码")

    seminar_detail_parser = subparsers.add_parser("seminar_room_detail", help="查询研讨室详情")
    seminar_detail_parser.add_argument("--area_id", required=True, help="房间 area_id")
    seminar_detail_parser.add_argument("--target_date", default="", help="日期 YYYY-MM-DD")

    seminar_reserve_parser = subparsers.add_parser("seminar_reserve", help="预约研讨室")
    seminar_reserve_parser.add_argument("--area_id", required=True, help="房间 area_id")
    seminar_reserve_parser.add_argument("--target_date", default="", help="开始日期 YYYY-MM-DD")
    seminar_reserve_parser.add_argument("--start_time", default="", help="开始时间 HH:MM")
    seminar_reserve_parser.add_argument("--end_time", default="", help="结束时间 HH:MM")
    seminar_reserve_parser.add_argument("--end_date", default="", help="结束日期 YYYY-MM-DD")
    seminar_reserve_parser.add_argument("--title", default="", help="申请主题")
    seminar_reserve_parser.add_argument("--title_id", default="", help="预设主题 ID")
    seminar_reserve_parser.add_argument("--content", required=True, help="申请内容，必须大于10字")
    seminar_reserve_parser.add_argument("--mobile", default="", help="联系电话")
    seminar_reserve_parser.add_argument("--group_name", default="", help="已保存的 group 名称")
    seminar_reserve_parser.add_argument("--member_ids", default="", help="直接传同行成员学号列表，不含自己")
    seminar_reserve_parser.add_argument("--is_open", type=int, default=0, help="是否公开，0=是 1=否")
    seminar_reserve_parser.add_argument("--cate_id", default="", help="半天/全天分类 ID")
    seminar_reserve_parser.add_argument("--time_ranges_json", default="", help="多时间段 JSON 数组")

    seminar_cancel_parser = subparsers.add_parser("seminar_cancel", help="取消研讨室预约")
    seminar_cancel_parser.add_argument("--record_id", required=True, help="研讨室预约记录 ID")

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
        elif args.command == "library_current":
            result = library_current()
        elif args.command == "library_auto_signin":
            result = library_auto_signin(record_id=args.record_id)
        elif args.command == "library_records":
            result = library_records(
                record_type=args.record_type,
                page=args.page,
                limit=args.limit,
            )
        elif args.command == "library_cancel":
            result = library_cancel(record_id=args.record_id, record_type=args.record_type)
        elif args.command == "seminar_groups":
            result = seminar_groups()
        elif args.command == "seminar_group_save":
            result = seminar_group_save(
                group_name=args.group_name,
                member_ids=args.member_ids,
                note=args.note,
            )
        elif args.command == "seminar_group_delete":
            result = seminar_group_delete(group_name=args.group_name)
        elif args.command == "seminar_filters":
            result = seminar_filters()
        elif args.command == "seminar_records":
            result = seminar_records(
                record_type=args.record_type,
                mode=args.mode,
                page=args.page,
                limit=args.limit,
            )
        elif args.command == "seminar_signin_tasks":
            result = seminar_signin_tasks(status=args.status)
        elif args.command == "seminar_signin":
            result = seminar_signin(record_id=args.record_id)
        elif args.command == "seminar_auto_signin":
            result = seminar_auto_signin()
        elif args.command == "seminar_rooms":
            result = seminar_rooms(
                target_date=args.target_date,
                members=args.members,
                name=args.name,
                room=args.room,
                start_time=args.start_time,
                end_time=args.end_time,
                library_ids=args.library_ids,
                library_names=args.library_names,
                floor_ids=args.floor_ids,
                floor_names=args.floor_names,
                category_ids=args.category_ids,
                category_names=args.category_names,
                boutique_ids=args.boutique_ids,
                boutique_names=args.boutique_names,
                page=args.page,
            )
        elif args.command == "seminar_room_detail":
            result = seminar_room_detail(area_id=args.area_id, target_date=args.target_date)
        elif args.command == "seminar_reserve":
            result = seminar_reserve(
                area_id=args.area_id,
                target_date=args.target_date,
                start_time=args.start_time,
                end_time=args.end_time,
                end_date=args.end_date,
                title=args.title,
                title_id=args.title_id,
                content=args.content,
                mobile=args.mobile,
                group_name=args.group_name,
                member_ids=args.member_ids,
                is_open=args.is_open,
                cate_id=args.cate_id,
                time_ranges_json=args.time_ranges_json,
            )
        elif args.command == "seminar_cancel":
            result = seminar_cancel(record_id=args.record_id)
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
