# 智慧戒斷盒 (Self-Discipline Lockbox)

**專注時長設定、GPIO 硬體鎖定、AI 緊急解鎖判斷**

---

## 專案資訊

112403539 資管3B 楊翔善

##  專案概觀

**智慧戒斷盒** 是一個結合 Flask 網頁應用、背景排程與 AI 邏輯的自律工具。使用者可以設定專注時長，觸發 GPIO 實體上鎖，並透過 AI 語言模型判斷緊急狀況來決定是否允許提前解鎖，旨在幫助使用者維持專注。

### 核心功能 (後端路由)

| 路由 (Route) | 方法 (Method) | 描述 |
| :--- | :--- | :--- |
| `/` | `GET` | 顯示目前鎖定狀態、倒數計時器及鎖定設定介面。 |
| `/lock` | `POST` | 接收設定時長，觸發 **GPIO 12** 上鎖，並啟動 `flask-apscheduler` 背景倒數計時器。 |
| `/ai_unlock` | `GET/POST` | 提供緊急解鎖申請頁面。`POST` 接收文字原因，透過內建 AI 模組判斷是否為緊急狀況，若為真則提前解鎖。 |

---

## 環境與工具要求

### 1. 硬體 (Hardwares)

| 元件 | 備註 |
| :--- | :--- |
| **Raspberry Pi 4** |  |
| **杜邦線** | 公母線5條、公公線1條 |
| **變壓器** | 供應樹莓pi電源 |
| **電磁鎖** | 12V 通電上鎖 |
| **轉接器** | 電源12V |
| **分電線** | 將電源分為正極負極 |
| **繼電器** | 12V可行 |
| **觸控螢幕** | 樹莓派5吋電容式觸控螢幕(800×480, HDMI) |
| **USB 連接線** | USB to micro USB(公公) |
| **HDMI 連接線** | micro HDMI to HDMI (公公)|

### 2. 軟體依賴 (Software Dependencies)

| 項目 | 備註 |
| :--- | :--- |
| **Python** | 3.x |
| **Flask** | 核心 Web 框架 |
| **flask-apscheduler** | 背景排程與倒數計時 |
| **RPi.GPIO** | 控制鎖 |
| **sqlite3** | 儲存資料 |

---

## 部署與執行步驟

### 步驟 A: 環境設定 (Setup)

1.  **克隆專案：** 從 GitHub 下載您的程式碼。

    ```bash
    git clone [https://github.com/defyingYang/IoT.git](https://github.com/defyingYang/IoT.git)
    cd IoT/final
    ```

2.  **建立與啟動虛擬環境：**

    ```bash
    python -m venv venv
    source venv/bin/activate  # 或 .\venv\Scripts\activate.bat
    ```

3.  **安裝 Python 依賴：**
    
    > **注意：** `app.py` 程式碼會根據環境自動偵測 `RPi.GPIO`。如果您在樹莓派上部署，請確保安裝它。

    ```bash
    # 安裝 Flask 核心組件
    (venv) $ pip install Flask flask-apscheduler

    # 僅在 Raspberry Pi 上執行這條指令
    (venv) $ pip install RPi.GPIO
    ```

### 步驟 B: 硬體接線 (GPIO 12)

專案已設定使用 **GPIO 12 (BCM 編號)** 作為繼電器訊號線。

| 連接點 | 樹莓派腳位 (BCM) | 程式碼中的狀態 |
| :--- | :--- | :--- |
| **訊號線 (IN)** | **GPIO 12** | 核心控制腳位。 |
| **VCC** | 5V 或 3.3V | 繼電器供電。 |
| **GND** | 任何 GND 腳位 | 接地。 |

電磁鎖與電源連結繼電器

| 電源 | 繼電器 | 電磁鎖 |
| :--- | :--- | :--- |  
| **電源正極** | **COM** | 
|  | **NO** | **電磁鎖正極** |
| **電源負極** |  | **電磁鎖負極** | 
 

### 步驟 C: 運行應用程式

確保所有依賴安裝完成後，運行主程式：

```bash
(venv) $ python app.py
