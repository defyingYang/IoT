# tasks.py

import database
from datetime import datetime

# =============================================================
# 模擬 GPIO 函式（實際專案需替換為 RPi.GPIO 呼叫）
# 假設 GPIO Pin 17 控制繼電器/鎖
# =============================================================
def lock_box_gpio():
    """模擬：將繼電器/鎖定裝置上鎖"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 GPIO: 盒子已上鎖 (Pin 17 HIGH)")
    # 實際 RPi.GPIO 程式碼 (範例):
    # import RPi.GPIO as GPIO
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(17, GPIO.OUT)
    # GPIO.output(17, GPIO.HIGH)

def unlock_box_gpio():
    """模擬：將繼電器/鎖定裝置解鎖"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 GPIO: 盒子已解鎖 (Pin 17 LOW)")
    # 實際 RPi.GPIO 程式碼 (範例):
    # import RPi.GPIO as GPIO
    # GPIO.output(17, GPIO.LOW)

# =============================================================
# 背景任務：時間到達時的自動解鎖
# =============================================================
def unlock_task(session_id):
    """
    由 APScheduler 在預定時間觸發執行。
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 背景任務：會話 {session_id} 時間到。")
    
    # 1. 觸發 GPIO 解鎖
    unlock_box_gpio()
    
    # 2. 更新資料庫紀錄為「completed」
    database.complete_lock_session(session_id)