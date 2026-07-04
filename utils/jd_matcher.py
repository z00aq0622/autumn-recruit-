"""
JD匹配评分器 - 双引擎：规则化评分V1 + 大模型语义匹配V2
规则化评分处理关键词/排除词/城市/优先级等确定性维度
大模型语义匹配处理专业对口度/岗位层级适配等需要语义理解的维度
"""
import os
import yaml
from typing import List, Dict
try:
    from utils.llm_matcher import LLMMatcher
except ImportError:
    try:
        from .llm_matcher import LLMMatcher
    except ImportError:
        LLMMatcher = None  # LLM模块不可用时降级为纯规则评分


class JDMatcher:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # 自动定位项目根目录下的config/profile.yaml
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, "config", "profile.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.directions = self.config.get("directions", [])

        # 初始化LLM语义匹配引擎（双引擎V2）
        llm_key = os.environ.get("LLM_API_KEY", "")
        llm_base = os.environ.get("LLM_API_BASE", "https://api.deepseek.com/v1")
        llm_model = os.environ.get("LLM_MODEL", "deepseek-chat")
        if LLMMatcher is not None:
            self.llm_matcher = LLMMatcher(api_key=llm_key, api_base=llm_base, model=llm_model)
            self.llm_enabled = bool(llm_key)
        else:
            self.llm_matcher = None
            self.llm_enabled = False
            print("[JDMatcher] LLM模块不可用，仅使用规则化评分")

        # 构建候选人画像（从配置文件读取）
        personal = self.config.get("personal", {})
        self.candidate_profile = (
            f"{personal.get('school', '浙江大学硕士')}（{personal.get('major', '社会工作')}专业）/"
            f"985本硕/预备党员/AI产品0-1实践经验/熟悉Agent/Workflow/RAG"
        )

    def score(self, title: str, description: str = "", company: str = "", location: str = "") -> Dict:
        """
        双引擎评分：规则化V1（确定性维度） + LLM语义V2（语义理解维度）
        返回: {"score": int, "direction": str, "reasons": list, "engine": str}
        """
        # === V1: 规则化评分 ===
        text = f"{title} {description} {company}".lower()
        rule_score = 0
        best_direction = ""
        rule_reasons = []

        for direction in self.directions:
            score = 0
            reasons = []

            # 1. 方向关键词 (+10 each)
            for kw in direction.get("keywords", []):
                if kw.lower() in text:
                    score += 10
                    reasons.append(f"关键词命中: {kw}")

            # 2. 排除词 (-30 each)
            for ekw in direction.get("exclude_keywords", []):
                if ekw.lower() in text:
                    score -= 30
                    reasons.append(f"排除词命中: {ekw}")

            # 3. 城市匹配 (+5 each)
            for city in direction.get("cities", []):
                if city in text or city in location:
                    score += 5
                    reasons.append(f"城市匹配: {city}")
                    break

            # 4. 优先级加权
            if direction.get("priority") == 1:
                score = int(score * 1.2)
            elif direction.get("priority") == 2:
                score = int(score * 1.0)

            if score > rule_score:
                rule_score = score
                best_direction = direction["name"]
                rule_reasons = reasons

        rule_score = min(rule_score, 100)

        # === V2: LLM语义匹配评分 ===
        llm_result = {"score": 0, "match_reasons": [], "semantic_tags": []}
        if self.llm_matcher is not None and self.llm_enabled:
            try:
                llm_result = self.llm_matcher.semantic_match(
                    jd_title=title,
                    jd_description=description,
                    candidate_profile=self.candidate_profile,
                    location=location
                )
            except Exception as e:
                print(f"[JDMatcher] LLM评分异常: {e}")
                llm_result = {"score": 0, "match_reasons": [f"LLM异常: {str(e)[:30]}"], "semantic_tags": []}

        llm_score = llm_result.get("score", 0)
        llm_reasons = llm_result.get("match_reasons", [])
        semantic_tags = llm_result.get("semantic_tags", [])

        # === 双引擎融合 ===
        # V1规则评分权重40%，V2语义评分权重60%
        # LLM未启用时，纯规则评分（V1权重100%）
        if self.llm_enabled and llm_score > 0:
            final_score = int(rule_score * 0.4 + llm_score * 0.6 / 90 * 100)
            engine = "双引擎(规则V1+语义V2)"
            all_reasons = rule_reasons + llm_reasons
        else:
            final_score = rule_score
            engine = "规则化评分V1"
            all_reasons = rule_reasons

        final_score = min(final_score, 100)

        return {
            "score": final_score,
            "direction": best_direction,
            "reasons": all_reasons[:8],
            "engine": engine,
            "semantic_tags": semantic_tags,
            "rule_score": rule_score,
            "llm_score": llm_score
        }

    def filter_best(self, items: List[Dict], min_score: int = 30) -> List[Dict]:
        """筛选评分合格的岗位"""
        results = []
        for item in items:
            title = item.get("title", "")
            desc = item.get("description", "")
            company = item.get("company", "")
            location = item.get("location", "")

            result = self.score(title, desc, company, location)
            if result["score"] >= min_score:
                item["match_score"] = result["score"]
                item["match_direction"] = result["direction"]
                item["match_reasons"] = result["reasons"]
                item["match_engine"] = result["engine"]
                if result.get("semantic_tags"):
                    item["semantic_tags"] = result["semantic_tags"]
                results.append(item)

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results
