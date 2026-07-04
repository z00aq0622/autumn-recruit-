"""
Server酱推送模块 - 微信消息推送
文档: https://sct.ftqq.com/
"""
import requests
import json
from typing import Optional


class ServerChan:
    """Server酱推送（微信）"""

    def __init__(self, sendkey: str):
        self.sendkey = sendkey
        self.api_url = f"https://sctapi.ftqq.com/{sendkey}.send"

    def send(self, title: str, content: str, short: str = "") -> dict:
        """
        发送消息到微信
        title: 消息标题（必填）
        content: Markdown格式的消息正文
        short: 消息简述（可选，用于微信通知弹窗）
        """
        data = {
            "title": title[:100],
            "desp": content,
        }
        if short:
            data["short"] = short[:100]

        try:
            resp = requests.post(self.api_url, data=data, timeout=10)
            result = resp.json()
            if result.get("code") == 0:
                print(f"[Server酱] 推送成功: {title}")
                return {"success": True, "message": "推送成功"}
            else:
                print(f"[Server酱] 推送失败: {result}")
                return {"success": False, "message": str(result)}
        except Exception as e:
            print(f"[Server酱] 推送异常: {e}")
            return {"success": False, "message": str(e)}

    def send_daily_report(self, report_content: str, date_str: str) -> dict:
        """发送秋招日报"""
        title = f"🐗 秋招日报 | {date_str}"
        # 微信通知弹窗的简短内容
        short = "今日秋招信息已更新，点击查看详情"
        return self.send(title=title, content=report_content, short=short)

    def send_urgent(self, title: str, content: str) -> dict:
        """发送紧急提醒（如：截止日期临近）"""
        full_title = f"🚨 紧急提醒 | {title}"
        return self.send(title=full_title, content=content, short="有紧急秋招信息请注意！")


# === 测试 ===
if __name__ == "__main__":
    # 测试时替换为你的SendKey
    key = "YOUR_SENDKEY_HERE"
    sc = ServerChan(key)
    result = sc.send("测试标题", "## 这是测试内容\n\n来自秋招自动推送系统")
    print(result)
