# database.py

import sqlite3
from datetime import datetime, timedelta

DB_NAME = 'lockbox.db'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def init_db():
    """初始化資料庫表格"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Sessions 表：記錄每次鎖定會話
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration INTEGER NOT NULL,  -- 鎖定分鐘數
            status TEXT NOT NULL,       -- LOCKED, COMPLETED, PREMATURE
            is_emergency_unlocked INTEGER -- 0: 否, 1: 是 (非正常解鎖)
        )
    """)

    # Unlock_Logs 表：記錄所有緊急解鎖嘗試
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unlock_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            reason TEXT NOT NULL,
            ai_decision INTEGER,       -- AI 判定結果 (0: 否, 1: 是)
            timestamp TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)
    conn.commit()
    conn.close()

def start_new_lock(start_dt, end_dt, duration):
    """新增一個鎖定會話"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 先將所有舊的 "LOCKED" 設為 "PREMATURE" (以防應用重啟或其他錯誤)
    cursor.execute("UPDATE sessions SET status = 'PREMATURE' WHERE status = 'LOCKED'")

    cursor.execute(
        "INSERT INTO sessions (start_time, end_time, duration, status, is_emergency_unlocked) VALUES (?, ?, ?, ?, ?)",
        (start_dt.strftime(DATETIME_FORMAT), 
         end_dt.strftime(DATETIME_FORMAT), 
         duration, 
         'LOCKED', 
         0)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

# ... 其他資料庫操作函式 (get_current_session, complete_lock_session, premature_unlock, log_unlock_attempt, get_dashboard_stats, get_weekly_usage) ...

def get_current_session():
    """獲取目前的鎖定會話 (status = 'LOCKED')"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, start_time, end_time, duration, status FROM sessions WHERE status = 'LOCKED' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'start_time': row[1], 'end_time': row[2], 'duration': row[3], 'status': row[4]}
    return None

def complete_lock_session(session_id):
    """時間到，任務完成"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET status = 'COMPLETED' WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def premature_unlock(session_id):
    """緊急解鎖，提前結束"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 狀態設為 PREMATURE，並標記為緊急解鎖事件
    cursor.execute("UPDATE sessions SET status = 'PREMATURE', is_emergency_unlocked = 1 WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    
def log_unlock_attempt(session_id, reason, is_emergency):
    """記錄緊急解鎖嘗試"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO unlock_logs (session_id, reason, ai_decision, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, reason, 1 if is_emergency else 0, datetime.now().strftime(DATETIME_FORMAT))
    )
    conn.commit()
    conn.close()

def get_dashboard_stats():
    """獲取儀表板所需的統計資料"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 總專注時數 (小時)
    cursor.execute("SELECT SUM(duration) FROM sessions WHERE status IN ('COMPLETED', 'PREMATURE')")
    total_minutes = cursor.fetchone()[0] or 0
    total_hours = round(total_minutes / 60, 1)

    # 成功次數 (COMPLETED)
    cursor.execute("SELECT COUNT(id) FROM sessions WHERE status = 'COMPLETED'")
    success_count = cursor.fetchone()[0] or 0
    
    # 總任務次數
    cursor.execute("SELECT COUNT(id) FROM sessions WHERE status IN ('COMPLETED', 'PREMATURE')")
    total_tasks = cursor.fetchone()[0] or 0
    
    # 成功率
    success_rate = (success_count / total_tasks) * 100 if total_tasks > 0 else 0
    
    # 平均時長 (分鐘)
    cursor.execute("SELECT AVG(duration) FROM sessions WHERE status = 'COMPLETED'")
    avg_duration = round(cursor.fetchone()[0] or 0)
    
    conn.close()
    
    # 注意：圖片中的 "本週時數" 和 "-23%" 變化需要更複雜的週區間查詢，此處僅提供基本數據。
    return {
        'total_hours': total_hours,
        'success_count': success_count,
        'avg_duration': avg_duration,
        'success_rate': round(success_rate, 1)
    }

def get_weekly_usage():
    """模擬獲取每週使用圖表數據"""
    # 實際應根據當前日期計算過去 7 天的數據
    return [
        {'day': '一', 'hours': 3},
        {'day': '二', 'hours': 4.5},
        {'day': '三', 'hours': 6},
        {'day': '四', 'hours': 2},
        {'day': '五', 'hours': 5},
        {'day': '六', 'hours': 1},
        {'day': '日', 'hours': 0},
    ]