# 上線到 Cloudflare Pages（私密）— 步驟指南

目標：`https://daily-brief.pages.dev`（只有你自己登入睇到），每日香港時間 07:00 自動更新。

GitHub repo 已轉為 **private**：`victoryuen99999-commits/daily-brief`
（所以公開嘅 GitHub Pages 已經自動下線，現時係 404，屬正常）

---

## 步驟 1：開 Cloudflare 帳號（你做，約 2 分鐘）

1. 去 https://dash.cloudflare.com/sign-up
2. 填 email + 密碼（用你平時收信嘅 email，之後 Access 驗證碼會寄去同一個）
3. 去 email 撳驗證連結
4. 登入後如果問你要唔要加網站（Add a site），**跳過**，唔需要加 domain

> 密碼我唔會經手，你自己輸入。之後如果要我代你操作 dashboard，你可以在自動化瀏覽器登入，或者一步步跟我指示。

---

## 步驟 2：把 GitHub repo 接上 Pages（你做，約 2 分鐘）

1. 左邊選單 → **Workers & Pages**
2. **Create** → 選 **Pages** 分頁 → **Connect to Git**
3. 第一次要 **Authorize Cloudflare Pages** 連接 GitHub → 只授權 `daily-brief` 呢個 repo（可以揀 Only select repositories）
4. 揀 repo：**victoryuen99999-commits/daily-brief** → **Begin setup**
5. 設定：
   - Project name：`daily-brief`（決定網址 https://daily-brief.pages.dev）
   - Production branch：`main`
   - Framework preset：**None**
   - Build command：**留空**
   - Build output directory：**`/`**（一個斜線）
6. **Save and Deploy** → 等 30–60 秒

完成後會見到 `https://daily-brief.pages.dev`。呢個時候任何人開都睇得到，下一步才加鎖。

---

## 步驟 3：加鎖（只有你睇得到）— 你做，約 3 分鐘

1. 左邊選單 → **Zero Trust**（第一次要開通，會問 team name，隨便改個名，例如 `victor`；方案揀 **Free**，要填信用卡都係 $0，免費 50 人以下）
2. **Access** → **Applications** → **Add an application** → **Self-hosted**
3. Application name：`每日情報站`
4. Session Duration：`1 month`
5. Public hostname：
   - Subdomain：留空（如果你有 domain 就用 domain；冇就先用 pages.dev）
   - Domain：`daily-brief.pages.dev`
   - Path：留空
6. **Add policy**：
   - Policy name：`只有我`
   - Action：**Allow**
   - Include → **Emails** → 填你嘅 email
7. **Next** → 其他全部預設 → **Add application**

之後開 `https://daily-brief.pages.dev` 會先彈 Cloudflare 登入頁，寄一次性驗證碼去你 email；手機第一次登入後，一個月內唔會再問。

---

## 之後點更新

- GitHub Actions 每日香港時間 **07:00** 跑 `refresh.py`，自動 commit 新 `data.js`
- 你一 commit，Cloudflare Pages 就會自動重新部署（大約 30 秒）
- 想即刻更新：去 GitHub repo → Actions → refresh → **Run workflow**

即係話：你部電腦唔需要開，都會每日自己更新。

---

## 為甚麼用「Connect to Git」而唔用 wrangler 直接上傳

直接上傳（wrangler）冇辧法做到「commit 就自動部署」，要另外整個 API token 放去 GitHub secrets。Connect to Git 唔需要任何 token，亦唔會有人手漏 token 嘅風險。
