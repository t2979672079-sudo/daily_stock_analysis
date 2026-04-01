from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Optional


def _to_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def clamp_score(score: Any) -> int:
    s = _to_float(score)
    if s is None:
        return 50
    s = int(round(s))
    return max(0, min(100, s))


def advice_from_score(score: int) -> str:
    if score <= 29:
        return "卖出"
    if score <= 44:
        return "观望"
    if score <= 59:
        return "持有"
    if score <= 74:
        return "谨慎看多"
    if score <= 89:
        return "看多"
    return "强烈看多"


def trend_from_score(score: int) -> str:
    if score <= 29:
        return "强烈看空"
    if score <= 44:
        return "看空"
    if score <= 59:
        return "震荡"
    return "看多"


def apply_score_guard(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一分数-动作绑定：
    - 先钳制 sentimentScore
    - 再按分数强制重算 operationAdvice / trendPrediction
    """
    score = clamp_score(result.get("sentimentScore"))
    result["sentimentScore"] = score

    result["operationAdvice"] = advice_from_score(score)
    result["trendPrediction"] = trend_from_score(score)

    # decisionType 也同步，避免前后矛盾
    if score <= 29:
        result["decisionType"] = "sell"
    elif score <= 59:
        result["decisionType"] = "hold"
    else:
        result["decisionType"] = "buy"

    return result


def _extract_price_candidates(text: str) -> list[float]:
    vals = []
    for m in re.findall(r"\d+(?:\.\d+)?", text or ""):
        try:
            vals.append(float(m))
        except ValueError:
            pass
    return vals


def validate_stock_identity_and_price(
    result: Dict[str, Any],
    stock_code: str,
    stock_name: str,
    other_names: Optional[Iterable[str]] = None,
    current_price: Optional[float] = None,
) -> tuple[bool, str]:
    """
    校验：
    1. 页面正文不能串其他股票名
    2. 关键价位不能离当前价过远
    """
    text_blocks = [
        str(result.get("analysisSummary", "") or ""),
        str(result.get("coreConclusion", "") or ""),
        str(result.get("keyPoints", "") or ""),
        str(result.get("riskWarning", "") or ""),
        str(result.get("buyReason", "") or ""),
    ]

    dashboard = result.get("dashboard") or {}
    core = dashboard.get("core_conclusion") or {}
    text_blocks.append(str(core.get("one_sentence", "") or ""))

    full_text = "\n".join(text_blocks)

    if stock_name and stock_name not in full_text:
        # 名字不一定总会出现，先不直接失败
        pass

    if other_names:
        for name in other_names:
            if name and name != stock_name and name in full_text:
                return False, f"检测到串股名称: {name}"

    cp = _to_float(current_price)
    if cp is not None and cp > 0:
        candidates = _extract_price_candidates(full_text)
        for p in candidates:
            # 容忍百分比 35%，超出则高度可疑
            if abs(p - cp) / cp > 0.35:
                return False, f"检测到疑似错位价位: {p} (current={cp})"

    return True, "ok"


def apply_data_completeness_guard(
    result: Dict[str, Any],
    data_complete: bool,
) -> Dict[str, Any]:
    """
    数据不完整时，禁止强结论。
    """
    if data_complete:
        return result

    score = clamp_score(result.get("sentimentScore"))
    score = min(score, 59)
    result["sentimentScore"] = score
    result["operationAdvice"] = "观望"
    result["trendPrediction"] = "震荡"
    result["decisionType"] = "hold"

    return result
