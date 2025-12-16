# IoT(Unfinished)
=======
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
| **記憶卡** | 16GB |
| **杜邦線** | 公母線5條、公公線1條 |
| **變壓器** | 供應樹莓pi電源 |
| **電磁鎖** | 12V 通電上鎖 |
| **轉接器** | 電源12V |
| **分電線** | 將電源分為正極負極 |
| **繼電器** | 12V可行 |
| **觸控螢幕** | 樹莓派5吋電容式觸控螢幕(800×480, HDMI) |
| **USB 連接線** | USB to micro USB(公公) |
| **HDMI 連接線** | micro HDMI to HDMI (公公)|
| **紙箱** |  |

![材料](https://github.com/defyingYang/IoT/blob/eb66070cbf6b7238e2496d7fe16f7c4bef7c3e51/iot03.jpg)


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

電磁鎖與電源連結繼電器以下為連接點

| 元件 | 繼電器端子 | 電源/負載 | 繼電器狀態 | 鎖定狀態 |
| :--- | :--- | :--- | :--- | :--- |    
| **繼電器線圈 (IN)** | **IN (訊號線)** |  **GPIO 12** | **關閉 (OFF)** | **解鎖 (斷電)** |
| **繼電器線圈 (IN)** | **IN (訊號線)** |  **GPIO 12** | **吸合 (ON)** | **上鎖 (通電)** |
| **電源迴路**(電源-繼電器) | **COM** |  **變壓器正極 (+)** | - | - |
| **電源迴路**(電磁鎖-繼電器) | **NO(常開)** |  **電磁鎖正極 (+)** | - | - |
| **電源迴路**(電磁鎖-電源) | **電磁鎖負極 (-)** |  **12V** | **變壓器負極 (-)** | - |

![電磁鎖接線圖](https://github.com/defyingYang/IoT/blob/eb66070cbf6b7238e2496d7fe16f7c4bef7c3e51/iot01.jpg)

觸控螢幕與樹莓pi

| 連接點 | 樹莓派 | 
| :--- | :--- | 
| **microUSB** | **USB-A** | 
| **HDMI** | **microHDMI** | 

![觸控螢幕接線圖](https://github.com/defyingYang/IoT/blob/eb66070cbf6b7238e2496d7fe16f7c4bef7c3e51/iot02.jpg)

### 步驟 C: 運行應用程式

確保所有依賴安裝完成後，運行主程式：

```bash
(venv) $ python app.py
>>>>>>> a35f0b373acf1c20ca36c2d7da9b9bc0b7c62e1f
進入 http://172.20.10.2:5000/
```

首頁面可以選擇鎖定時間
![](https://github.com/defyingYang/IoT/blob/410991ed3f65d0204525b7c64dca4953a50eaad7/iot04.png)

倒數計時(上鎖)
![](https://github.com/defyingYang/IoT/blob/230c3951cf625461c0ff59e4ebee6cfd2b966dfa/iot05.png)

可經由輸入緊急情況解鎖
![](https://github.com/defyingYang/IoT/blob/a2f0218e2e943d45bf1d0d60286415c83e615095/iot06.png)

影片
* [測試影片]()

參考資料
* [基於物聯網的電磁門鎖使用樹莓派4](https://www.21ic.com/a/977886.html)
* [繼電器接電方法 (YouTube)](https://www.youtube.com/watch?v=A4OWrq6dQNA)
* [Raspberry Pi GPIO and Smart Relay (繼電器使用方法)](https://speakerdeck.com/piepie_tw/raspberry-pi-gpio-and-smart-relay?slide=49)
* [繼電器 (codedata.com.tw)](codedata.com.tw/java/att10/)
* Python Flask 官方文件
* Raspberry Pi RPi.GPIO 函式庫教學
* Chart.js 官方文件
* SQLite Python (sqlite3) 函式庫教學

