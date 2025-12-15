# app.py - 智慧戒斷盒 (Self-Discipline Lockbox) 整合版
# -----------------------------------------------------------

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_apscheduler import APScheduler
from apscheduler.jobstores.base import JobLookupError
from datetime import datetime, timedelta
import sqlite3
import time
import atexit # 用於程式結束時清理 GPIO 資源

# === [0] 全域設定與初始化 ===

app = Flask(__name__)

# 配置 APScheduler
app.config['SCHEDULER_API_ENABLED'] = True
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

DB_NAME = 'lockbox.db'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# === [1] 資料庫操作模組 ===

def get_db_connection():
    """連接到 SQLite 資料庫"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化資料庫表格"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration INTEGER NOT NULL,
            status TEXT NOT NULL,
            is_emergency_unlocked INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unlock_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            reason TEXT NOT NULL,
            ai_decision INTEGER,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)
    conn.commit()
    conn.close()

def start_new_lock(start_dt, end_dt, duration):
    """新增一個鎖定會話"""
    conn = get_db_connection()
    cursor = conn.cursor()
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

def get_current_session():
    """獲取目前的鎖定會話 (status = 'LOCKED')"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, start_time, end_time, duration, status FROM sessions WHERE status = 'LOCKED' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def complete_lock_session(session_id):
    """時間到，任務完成"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET status = 'COMPLETED' WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def premature_unlock(session_id):
    """緊急解鎖，提前結束"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET status = 'PREMATURE', is_emergency_unlocked = 1 WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    
def log_unlock_attempt(session_id, reason, is_emergency):
    """記錄緊急解鎖嘗試"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO unlock_logs (session_id, reason, ai_decision, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, reason, 1 if is_emergency else 0, datetime.now().strftime(DATETIME_FORMAT))
    )
    conn.commit()
    conn.close()

def get_dashboard_stats():
    """獲取儀表板所需的統計資料 (使用模擬數據)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(duration) FROM sessions WHERE status IN ('COMPLETED', 'PREMATURE')")
    total_minutes = cursor.fetchone()[0] or 0
    total_hours = round(total_minutes / 60, 1)

    cursor.execute("SELECT COUNT(id) FROM sessions WHERE status = 'COMPLETED'")
    success_count = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(id) FROM sessions WHERE status IN ('COMPLETED', 'PREMATURE')")
    total_tasks = cursor.fetchone()[0] or 0
    
    success_rate = (success_count / total_tasks) * 100 if total_tasks > 0 else 0
    
    cursor.execute("SELECT AVG(duration) FROM sessions WHERE status = 'COMPLETED'")
    avg_duration = round(cursor.fetchone()[0] or 0)
    
    conn.close()
    
    # 模擬圖片中的數據
    return {
        'total_hours': total_hours, # 使用實際計算
        'success_count': success_count,
        'avg_duration': avg_duration,
        'success_rate': round(success_rate, 1)
    }

# === [2] 背景任務與 GPIO 實作/模擬 (GPIO 12 設置) ===

# --- 導入 GPIO 函式庫：根據運行平台安全導入 ---
try:
    import RPi.GPIO as GPIO
    IS_RPI = True
    print("[GPIO]: 成功載入 RPi.GPIO。正在樹莓派環境運行。")
    # --- GPIO 腳位設定 ---
    RELAY_PIN = 12                  # *** 核心設定：使用 GPIO 12 (BCM 編號) ***
    LOCK_STATE = GPIO.HIGH          # 鎖定狀態 (假設繼電器為低電位觸發，HIGH=關閉=鎖定)
    UNLOCK_STATE = GPIO.LOW         # 解鎖狀態 (假設繼電器為低電位觸發，LOW=開啟=解鎖)
    # ----------------------
except ModuleNotFoundError:
    # 運行模擬模式 (Windows/Mac)
    IS_RPI = False
    print("[GPIO]: 找不到 RPi.GPIO。運行模擬模式。")
    class MockGPIO:
        HIGH = 1
        LOW = 0
        OUT = 0
        BCM = 0
        def setmode(self, mode): pass
        def setup(self, pin, mode, initial): pass
        def output(self, pin, state): pass
        def cleanup(self): pass

    GPIO = MockGPIO()
    RELAY_PIN = 12
    LOCK_STATE = GPIO.HIGH
    UNLOCK_STATE = GPIO.LOW
# -----------------------------------------------------

# --- GPIO 函式 ---

def setup_gpio():
    """初始化 GPIO 設定"""
    if IS_RPI:
        try:
            GPIO.setmode(GPIO.BCM)
            # 設置初始狀態為鎖定，確保一開始是鎖住的
            GPIO.setup(RELAY_PIN, GPIO.OUT, initial=LOCK_STATE) 
            print(f"[GPIO Setup]: 初始化完成，GPIO {RELAY_PIN} 設置為輸出。")
        except Exception as e:
            print(f"[GPIO Setup Error]: 無法初始化 GPIO: {e}")
    else:
        print("[GPIO Setup]: 運行模擬模式，跳過硬體初始化。")


def cleanup_gpio():
    """清除 GPIO 設定"""
    if IS_RPI:
        GPIO.cleanup()
        print("[GPIO Cleanup]: 釋放 GPIO 資源。")
    else:
        pass

def lock_box_gpio():
    """實際/模擬：將繼電器/鎖定裝置上鎖 (GPIO 12 設置為 LOCK_STATE)"""
    try:
        GPIO.output(RELAY_PIN, LOCK_STATE)
        status_text = "實際" if IS_RPI else "模擬"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{status_text} GPIO]: 盒子已上鎖 (Pin {RELAY_PIN})。")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [GPIO ERROR]: 無法上鎖。 {e}")

def unlock_box_gpio():
    """實際/模擬：將繼電器/鎖定裝置解鎖 (GPIO 12 設置為 UNLOCK_STATE)"""
    try:
        GPIO.output(RELAY_PIN, UNLOCK_STATE)
        status_text = "實際" if IS_RPI else "模擬"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{status_text} GPIO]: 盒子已解鎖 (Pin {RELAY_PIN})。")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [GPIO ERROR]: 無法解鎖。 {e}")

# --- APScheduler 任務 ---

def unlock_task(session_id):
    """
    由 APScheduler 在預定時間觸發執行。
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [Background Task]: 會話 {session_id} 時間到。")
    
    # 1. 觸發 GPIO 解鎖
    unlock_box_gpio()
    
    # 2. 更新資料庫紀錄為「completed」
    complete_lock_session(session_id)


# === [3] AI 判斷模組 ===

EMERGENCY_KEYWORDS = ["生病", "緊急", "火災", "意外", "醫院", "聯絡家人", "天然災害", "安全問題", "有人受傷"]

def check_emergency(reason: str) -> bool:
    """利用關鍵字模擬語言模型判斷是否為緊急狀況"""
    reason_lower = reason.lower()
    
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in reason_lower:
            return True
            
    if any(phrase in reason_lower for phrase in ["無聊", "想看", "想玩", "沒事做", "工作結束了", "想休息"]):
        return False
        
    return False


# === [4] Flask 路由 (核心) ===

# -------------------------------------------------------------
# 1. GET /：顯示目前鎖定狀態與倒數設定介面
# -------------------------------------------------------------
@app.route('/', methods=['GET'])
def home():
    current_session = get_current_session()
    stats = get_dashboard_stats()
    
    time_remaining_seconds = 0
    if current_session and current_session['status'] == 'LOCKED':
        try:
            end_dt = datetime.strptime(current_session['end_time'], DATETIME_FORMAT)
            time_remaining = end_dt - datetime.now()
            time_remaining_seconds = max(0, int(time_remaining.total_seconds()))
        except ValueError:
            time_remaining_seconds = 0

    return render_template('index.html', 
                           session=current_session, 
                           stats=stats,
                           time_remaining_seconds=time_remaining_seconds)

# -------------------------------------------------------------
# 2. POST /lock：鎖定操作
# -------------------------------------------------------------
@app.route('/lock', methods=['POST'])
def lock():
    try:
        duration_minutes = int(request.form.get('duration', 0))
    except (ValueError, TypeError):
        return "Invalid duration", 400

    if duration_minutes <= 0 or get_current_session():
        return redirect(url_for('home')) 

    start_dt = datetime.now()
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    
    session_id = start_new_lock(start_dt, end_dt, duration_minutes)
    
    # 實際/模擬 GPIO 上鎖 (控制 GPIO 12)
    lock_box_gpio()
    
    # 啟動背景倒數計時器
    scheduler.add_job(
        id=f'unlock_job_{session_id}', 
        func=unlock_task, 
        trigger='date', 
        run_date=end_dt, 
        args=[session_id],
        misfire_grace_time=600 
    )
    
    return redirect(url_for('home'))

# -------------------------------------------------------------
# 3. GET /ai_unlock & POST /ai_unlock：緊急解鎖
# -------------------------------------------------------------
@app.route('/ai_unlock', methods=['GET'])
def ai_unlock_page():
    return render_template('ai_unlock.html', error_message=None, success_message=None)

@app.route('/ai_unlock', methods=['POST'])
def handle_ai_unlock():
    reason = request.form.get('reason', '').strip()
    current_session = get_current_session()

    if not current_session or current_session['status'] != 'LOCKED':
        return render_template('ai_unlock.html', error_message="目前沒有活躍的鎖定會話。")
    
    if not reason:
        return render_template('ai_unlock.html', error_message="請提供詳細說明。")

    is_emergency = check_emergency(reason)
    
    log_unlock_attempt(current_session['id'], reason, is_emergency)
    
    if is_emergency:
        # 實際/模擬 GPIO 解鎖 (控制 GPIO 12)
        unlock_box_gpio()
        premature_unlock(current_session['id'])
        
        # 安全地嘗試移除 APScheduler 中預定的任務
        job_id_to_remove = f'unlock_job_{current_session["id"]}'
        
        try:
            scheduler.remove_job(job_id_to_remove)
            print(f"成功移除 APScheduler 任務: {job_id_to_remove}")
        except JobLookupError:
            print(f"警告: 嘗試移除任務 {job_id_to_remove} 失敗，可能該任務已完成或伺服器已重啟。")
            pass
        
        return render_template('ai_unlock.html', success_message="緊急解鎖成功！請妥善處理您的急事。", unlocked=True)
    else:
        return render_template('ai_unlock.html', error_message="判定非緊急狀況。系統維持鎖定。", unlocked=False)

# -------------------------------------------------------------
# 4. GET /dashboard：儀表板 (導向首頁，因已移除)
# -------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    return redirect(url_for('home'))


# 應用程式啟動區塊
def setup():
    """初始化資料庫和 GPIO"""
    init_db()
    
    # 執行 GPIO 初始化
    try:
        setup_gpio()
    except NameError:
        print("[GPIO Setup]: RPi.GPIO 未在當前環境載入，跳過硬體初始化。")
        pass

if __name__ == '__main__':
    # 1. 在運行前確保 DB 和 GPIO 初始化
    with app.app_context():
        setup()
    
    # 2. 註冊 GPIO 清理函式 (僅在樹莓派環境生效)
    if 'IS_RPI' in locals() and IS_RPI:
        atexit.register(cleanup_gpio)
        
    app.run(debug=True, host='0.0.0.0', port=5000)