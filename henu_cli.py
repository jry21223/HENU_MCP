#!/usr/bin/env python3
"""
HENU Campus Assistant CLI for OpenClaw
河南大学校园助手命令行接口
"""

import argparse
import json
import sys
from pathlib import Path

# 导入MCP服务器的功能
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from henu_campus_mcp import (
    setup_account, sync_schedule, current_course, latest_schedule,
    library_locations, library_reserve, library_records, library_cancel,
    system_status
)

def main():
    parser = argparse.ArgumentParser(description="河南大学校园助手")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 账号设置
    setup_parser = subparsers.add_parser('setup_account', help='设置账号')
    setup_parser.add_argument('--student_id', required=True, help='学号')
    setup_parser.add_argument('--password', required=True, help='密码')
    setup_parser.add_argument('--library_location', help='默认图书馆区域')
    setup_parser.add_argument('--library_seat_no', help='默认座位号')
    
    # 课表功能
    sync_parser = subparsers.add_parser('sync_schedule', help='同步课表')
    sync_parser.add_argument('--xn', help='学年')
    sync_parser.add_argument('--xq', help='学期')
    
    current_parser = subparsers.add_parser('current_course', help='查询当前课程')
    current_parser.add_argument('--timezone', default='Asia/Shanghai', help='时区')
    
    subparsers.add_parser('latest_schedule', help='获取最新课表')
    
    # 图书馆功能
    subparsers.add_parser('library_locations', help='查看图书馆区域')
    
    reserve_parser = subparsers.add_parser('library_reserve', help='预约座位')
    reserve_parser.add_argument('--location', help='区域名')
    reserve_parser.add_argument('--seat_no', help='座位号')
    reserve_parser.add_argument('--target_date', help='日期 YYYY-MM-DD')
    reserve_parser.add_argument('--preferred_time', default='08:00', help='时间')
    
    records_parser = subparsers.add_parser('library_records', help='查询预约记录')
    records_parser.add_argument('--record_type', default='1', help='记录类型')
    records_parser.add_argument('--page', type=int, default=1, help='页码')
    records_parser.add_argument('--limit', type=int, default=20, help='每页数量')
    
    cancel_parser = subparsers.add_parser('library_cancel', help='取消预约')
    cancel_parser.add_argument('--record_id', required=True, help='记录ID')
    cancel_parser.add_argument('--record_type', default='1', help='记录类型')
    
    # 系统状态
    subparsers.add_parser('system_status', help='查看系统状态')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应命令
    try:
        if args.command == 'setup_account':
            result = setup_account(
                args.student_id, args.password,
                args.library_location or "", args.library_seat_no or ""
            )
        elif args.command == 'sync_schedule':
            result = sync_schedule(args.xn, args.xq)
        elif args.command == 'current_course':
            result = current_course(args.timezone)
        elif args.command == 'latest_schedule':
            result = latest_schedule()
        elif args.command == 'library_locations':
            result = library_locations()
        elif args.command == 'library_reserve':
            result = library_reserve(
                args.location or "", args.seat_no or "",
                args.target_date or "", args.preferred_time
            )
        elif args.command == 'library_records':
            result = library_records(args.record_type, args.page, args.limit)
        elif args.command == 'library_cancel':
            result = library_cancel(args.record_id, args.record_type)
        elif args.command == 'system_status':
            result = system_status()
        else:
            print(f"未知命令: {args.command}")
            return
        
        # 输出结果
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "msg": f"执行失败: {str(e)}"
        }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()