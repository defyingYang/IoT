# ai_module.py

# 簡單的關鍵字匹配作為模擬
EMERGENCY_KEYWORDS = ["生病", "緊急", "火災", "意外", "醫院", "聯絡家人", "天然災害", "安全問題", "有人受傷"]

def check_emergency(reason: str) -> bool:
    """
    判斷使用者輸入的原因是否為緊急狀況。
    
    在實際應用中：
    1. 可以呼叫 Gemini API 進行語義分析：
       prompt = f"判斷以下原因是否為真正的緊急狀況：'{reason}'。回答 '是' 或 '否'。"
    2. 使用更複雜的 NLP 模型。
    """
    reason_lower = reason.lower()
    
    # 簡單關鍵字匹配邏輯
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in reason_lower:
            return True
            
    # 排除常見非緊急理由
    if any(phrase in reason_lower for phrase in ["無聊", "想看", "想玩", "沒事做", "工作結束了", "想休息"]):
        return False
        
    return False