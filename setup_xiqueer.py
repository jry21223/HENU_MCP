#!/usr/bin/env python3
"""
配置西瓜儿API以自动获取节次时间
"""

import json
import sys
from pathlib import Path

# 从你的curl命令中提取的参数
DATA = """appinfo=iOS2.6.449&appsjxh=iPhone17,1&echo=78gjsvcyzmfg98o8ggnyt9rukhzjyrjl&encrptSecretKey=XDq7R1FBbCQv1mvg3yRGYuUTMuG__SCnj5FxgODna6PJrn77kIg0-yROFzcpubIgK4dgWRZtagR8rB4Fzhc5v1tOemztqq0EnMu3jmt7uCOES5_V66d55xLdlNt8LDErZfoNfrwF369t5_199JK_DrSWkchkIWhuF_pmhQoGtFY&param=2jth1j2kexfp3kp5ad1otmir2sqi3a1rsq842qxav81szqu72jt1lj2tc8lf3qnhdq2v4r4e2jth1j2kexgw3x8cdt1wkxbs3br5i52qynkv3ob0hg1wleas3n3yc22kdj9n2ncm562vq56h3t2hbt1wjxux2v39141peqll2s4ifr1peqll2tbdn11otbrd3koz4h21x5232zus6820qeh7311zqq204yvc2uhuyh1otpls311l2j1q0hqc2spvpu1q0rqy3uuptp2jscx12pqew31rtppy2spilg1q0ihw2twj7j1iwn4o3lbo952llinc3u90yp2kdat93rvfxx2prknf2xi6o329nr562tavw00029x0&param2=f1f54e31d063b6e7eea1af0dba4b2564&timestamp=1773025507&token=1sd8m51wjfa51x4rrj1wj5zm1uqwq01szgrn1r6b2p1urtw81ybjx51tk64r1vcgya2ezqde000035&xqerSign=gKLUf6vmWouv99s0zWdvGNprA6I2sHSCI8vuJBNT-DzXZPhdUM0uM8K73lMzNdSW8DADP4f2xkUPUrXuEuEX2MJIsRA_TKLOWXhzwbbjRxbmL7W7AibDA9fSMol9ksLzmaWidMetL7dBdO2ENLZbIU0NFPHSrH8JQGPKg2wrjEY"""

COOKIE = "JSESSIONID=CE0A2AD1AD88A590D20FC956817F9D32"

def main():
    base_dir = Path(__file__).parent
    config_file = base_dir / "xiqueer_period_time_request.json"
    
    config = {
        "url": "http://api.xiqueer.com/manager/wap/wapController.jsp",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Cookie": COOKIE,
            "User-Agent": "Mozilla/5.0"
        },
        "data": DATA,
        "timeout": 25
    }
    
    config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ 西瓜儿API配置已保存到: {config_file}")
    print("\n现在可以通过MCP工具自动获取节次时间了！")
    print("\n测试配置:")
    print("  python3 -c 'from mcp_server import test_xiqueer_period_time_request; import json; print(json.dumps(test_xiqueer_period_time_request(), indent=2, ensure_ascii=False))'")

if __name__ == "__main__":
    main()
