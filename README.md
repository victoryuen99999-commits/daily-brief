# 每日情報站

自己睇嘅每日資訊站：賺錢方法 + 香港／內地／國際新聞，一日更新一次以上，電腦同手機都開得。

## 一、點開

**電腦（最快）**：double-click `index.html` 就得，唔需要開伺服器（睇到上次抓取嘅資料，頁面右上角會寫時間）。

**電腦＋手機，連即時更新**：double-click `start.bat`，會出一個黑色視窗，寫住兩個網址：

```
電腦：  http://localhost:8090/
手機：  http://192.168.x.x:8090/     ← 手機同一個 Wi-Fi 就打呢個
```

黑色視窗唔好關，關咗就冇得即時更新（但 index.html 照樣開得）。按 `Ctrl+C` 停止。

> **本機 port：8090**（原本嘅「皇崗口岸資訊站」繼續用 8080，兩個站互不影響、可以同時開。）

## 二、六個版面

| 分頁 | 內容 | 來源 |
|---|---|---|
| 賺錢 | 11 個賺錢方法（按「幾時收到第一筆錢」排序）＋今日賺錢動態 | Hacker News（關鍵字查詢）、Reddit r/sidehustle、Product Hunt、明報經濟、港台財經、FT 中文網 |
| 健康 | 9 個每日健康微習慣（身體＋心情）＋健康新聞與研究 | ScienceDaily（健康／大腦）、Heho 健康、泛科學、政府新聞公報（衞生相關） |
| 學習 | 9 個有實證的學習方法＋課程與文章 | Learning Scientists、Scott H Young、Ness Labs、阮一峰週刊、The Marginalian |
| 香港 | 本地要聞 | 香港電台、明報要聞、香港電台財經 |
| 內地 | 內地及兩岸 | 中新網（即時＋要聞）、明報中國、中央社兩岸 |
| 國際 | 今日同近日國際大事 | BBC 中文、紐約時報中文、中央社國際、香港電台國際、德國之聲 |

每頁有搜尋框，例如打「利率」「AI」「樓」即刻篩。

## 三、更新機制

- `start.bat` 開住：每 **60 分鐘**自動抓一次，頁面右上角寫「自動更新 · 時:分」，按「更新」可即時重抓。
- 只用 `index.html`：右上角寫「**離線快照** · 時:分」，資料係上一次抓取嘅。想手動更新就 double-click `update.bat`（約 10 秒）。
- 已設定 Windows 工作排程（見下），每日 08:00 同每次開機都會自動抓一次。

**頁面唔會扮即時**：右上角個牌就係實際資料時間。

## 四、檔案

| 檔案 | 用途 |
|---|---|
| `index.html` | 網站本體（單檔，CSS/JS 內嵌，離線都用得） |
| `data.js` | 抓取出嚟嘅資料（自動產生，唔好手改） |
| `data.json` | 同一份資料，格式 JSON，方便其他程式讀 |
| `refresh.py` | 抓取腳本（只用 Python 標準庫，唔需安裝任何套件） |
| `serve.py` | 本機伺服器（`/api/live`、`/api/refresh`＋每 60 分鐘自動更新） |
| `start.bat` | 開伺服器（電腦＋手機） |
| `update.bat` | 只更新一次資料 |
| `autostart_server.bat` | 開機自動背景開伺服器（工作排程器用） |
| `allow_firewall.bat` | 開放防火牆 port 8090（手機連唔到時用，需按一次 UAC） |

## 五、已裝嘅 Windows 工作排程

| 名稱 | 時間 | 做乜 |
|---|---|---|
| `DailyBrief Refresh` | 每日 08:00 ＋ 每次登入 | 跑 `update.bat` 更新資料 |
| `DailyBrief Server` | 每次登入 | 背景開伺服器（最小化視窗） |

唔想要就開「命令提示字元」打：

```
schtasks /delete /tn "DailyBrief Refresh" /f
schtasks /delete /tn "DailyBrief Server" /f
```

## 六、想放上網（手機用流動數據都開得）

現時手機只可以同一個 Wi-Fi 開。要真正公開網址（免費、24 小時、唔需要開電腦），做法係 GitHub Pages ＋ Actions 每日自動更新：

1. 裝 `gh` 並登入：`gh auth login`
2. 開 repo 並推上去：
   ```
   cd "C:\Users\Neuron\OneDrive - Neuron Operations Limited\Desktop\DailyBrief"
   gh repo create daily-brief --public --source=. --push
   ```
3. 去 repo → Settings → Pages → Source 揀 `Deploy from a branch` → `main` / `root` → Save
4. `.github/workflows/refresh.yml` 已經準備好，GitHub 會每日香港時間 07:00 自動抓一次並 commit

網址會係 `https://<你的帳號>.github.io/daily-brief/`。

## 七、如果手機連唔到

1. 手機同電腦要連**同一個 Wi-Fi**（唔可以一個 Wi-Fi 一個流動數據）。
2. 黑色視窗要開住（或已裝嘅 `DailyBrief Server` 工作排程有跑）。
3. Windows 防火牆可能擋住 port 8090：double-click **`allow_firewall.bat`**，按「是」就得（會要求管理員權限一次）。
4. 網址以 `start.bat` 印出嘅為準，路由器重開機後 IP 可能變。

## 八、已知限制

- 手機版只有同一個 Wi-Fi 用得到（未放上網）。
- 新聞只抓標題＋摘要，全文要點入原文（版權屬原作者）。
- 賺錢方法嘅數字係 2026-10 嘅市場統計與實測紀錄，**唔係投資建議**，費率會變，用之前自己覆核一次。
- 個別 RSS 有時會 429／逾時，該分類會顯示上次成功嘅資料並標明「舊資料」，唔會顯示假數。
- OneDrive 會同步呢個資料夾；`data.js` 每次更新都會觸發同步，屬正常。
