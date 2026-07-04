"""
LLM语义匹配模块 - 基于大模型对岗位JD与个人画像的语义理解
支持 OpenAI / DeepSeek / 其他 OpenAI兼容API
"""
import json
import requests
from typing import Dict, List, Optional


class LLMMatcher:
    """基于大模型的语义匹配评分器"""

    def __init__(self, api_key: str = "", api_base: str = "", model: str = ""):
        """
        api_key: LLM API密钥（从环境变量 LLM_API_KEY 读取）
        api_base: API地址（默认DeepSeek，也可用OpenAI等其他兼容接口）
        model: 模型名称（默认 deepseek-chat）
        """
        self.api_key = api_key or ""
        self.api_base = api_base or "https://api.deepseek.com/v1"
        self.model = model or "deepseek-chat"

    def semantic_match(self, jd_title: str, jd_description: str = "",
                       candidate_profile: str = "", location: str = "") -> Dict:
        """
        用大模型做语义匹配评分
        返回: {"score": int(0-100), "match_reasons": list, "semantic_tags": list}
        """
        if not self.api_key:
            # 没有配置API Key时，返回中性评分（不加分也不减分，由规则评分决定）
            return {"score": 0, "match_reasons": ["LLM未启用，仅规则评分"], "semantic_tags": []}

        prompt = f"""你是一个专业的岗位匹配评分专家。请根据以下信息，判断候选人是否适合该岗位。

## 岗位信息
- 标题: {jd_title}
- 描述: {jd_description or '(无详细描述)'}
- 地点: {location or '(未指定)'}

## 候选人画像
{candidate_profile or '浙江大学硕士（社会工作专业）/华中科技大学本科（环境设计专业）/985本硕/预备党员/AI产品0-1实践经验/熟悉Agent/Workflow/RAG'}

## 评分规则
请从以下3个维度评分（每个维度0-30分，总分0-90）：
1. **专业对口度**: 候选人的专业背景（社会工作+环境设计）与岗位的语义关联程度。注意：不要只看字面匹配，要理解专业能力可迁移的场景。例如："社会工作专业→民政局/人社局/社会组织→高度对口"，"设计专业→产品经理/UI设计→中度对口"，"社会学方法→用户研究/数据分析→中度对口"。
2. **城市发展匹配**: 候选人意向城市（武汉优先，长沙/杭州/深圳/广州次选）与岗位所在城市的匹配度。
3. **岗位层级适配**: 候选人作为应届硕士毕业生，与岗位层级（校招/管培/社招初中级）的适配度。

## 输出格式（严格JSON）
```json
{
  "major_relevance_score": 0-30,
  "major_relevance_reason": "一句话解释",
  "city_match_score": 0-30, 
  "city_match_reason": "一句话解释",
  "level_fit_score": 0-30,
  "level_fit_reason": "一句话解释",
  "total_score": 0-90,
  "semantic_tags": ["标签1", "标签2", "标签3"],
  "summary": "一句话总结匹配结论"
}
```

请直接输出JSON，不要输出其他内容。"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,  # 低温度保证评分稳定性
                "max_tokens": 500,
                "response_format": {"type": "json_object"} if "deepseek" in self.api_base else None
            }
            # 移除 response_format 如果不支持
            if payload["response_format"] is None:
                del payload["response_format"]

            resp = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            result = resp.json()

            content = result["choices"][0]["message"]["content"]
            # 清理可能的markdown包裹
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            parsed = json.loads(content)
            total = parsed.get("total_score", 0)
            reasons = [
                f"专业对口: {parsed.get('major_relevance_reason', '')} ({parsed.get('major_relevance_score', 0)}分)",
                f"城市匹配: {parsed.get('city_match_reason', '')} ({parsed.get('city_match_score', 0)}分)",
                f"层级适配: {parsed.get('level_fit_reason', '')} ({parsed.get('level_fit_score', 0)}分)",
            ]
            tags = parsed.get("semantic_tags", [])
            summary = parsed.get("summary", "")

            return {
                "score": total,
                "match_reasons": reasons,
                "semantic_tags": tags,
                "summary": summary
            }

        except Exception as e:
            print(f"[LLM匹配] 调用失败: {e}")
            return {"score": 0, "match_reasons": [f"LLM调用异常: {str(e)[:50]}"], "semantic_tags": []}


# === 测试 ===
if __name__ == "__main__":
    import os
    key = os.environ.get("LLM_API_KEY", "")
    if not key:
        print("请设置环境变量 LLM_API_KEY")
        print("DeepSeek API: https://platform.deepseek.com/api_keys 创建")
    else:
        matcher = LLMMatcher(api_key=key)
        # 测试：社会工作专业是否匹配民政局岗位
        test = matcher.semantic_match(
            jd_title="武汉市民政局社会事务管理岗",
            jd_description="负责社会组织管理、社会救助政策执行、儿童福利事务协调",
            location="武汉"
        )
        print(f"匹配分数: {test['score']}/90")
        for r in test["match_reasons"]:
            print(f"  - {r}")
        print(f"语义标签: {test['semantic_tags']}")
        print(f"总结: {test['summary']}")
