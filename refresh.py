# -*- coding: utf-8 -*-
"""每日情報站 —— 資料抓取與快照產生器
只用 Python 標準庫，唔需要安裝任何套件。
用法： python refresh.py
輸出： data.js（給網頁讀）、data.json（給其他程式讀）
"""
import json, os, re, sys, html, time, socket
import urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

HKT = timezone(timedelta(hours=8))
HERE = os.path.dirname(os.path.abspath(__file__))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# ── 來源設定 ───────────────────────────────────────────────
FEEDS = [
    # 香港
    dict(sec="hk",  name="香港電台",   url="https://rthk9.rthk.hk/rthk/news/rss/c_expressnews_clocal.xml", lim=18),
    dict(sec="hk",  name="明報要聞",   url="https://news.mingpao.com/rss/pns/s00001.xml", lim=18),
    dict(sec="hk",  name="星島頭條",   tag="港聞", url="https://std.stheadline.com/rss", lim=15),
    dict(sec="hk",  name="香港電台財經", url="https://rthk9.rthk.hk/rthk/news/rss/c_expressnews_cfinance.xml", lim=10),
    # 內地
    dict(sec="cn",  name="中新網即時", url="https://www.chinanews.com.cn/rss/scroll-news.xml", lim=18),
    dict(sec="cn",  name="中新網要聞", url="https://www.chinanews.com.cn/rss/importnews.xml", lim=15),
    dict(sec="cn",  name="明報中國",   url="https://news.mingpao.com/rss/pns/s00004.xml", lim=12),
    dict(sec="cn",  name="中央社兩岸", url="https://feeds.feedburner.com/rsscna/mainland", lim=12),
    # 國際
    dict(sec="intl", name="BBC 中文",  url="https://feeds.bbci.co.uk/zhongwen/trad/rss.xml", lim=15),
    dict(sec="intl", name="紐約時報中文", url="https://cn.nytimes.com/rss/", lim=12),
    dict(sec="intl", name="中央社國際", url="https://feeds.feedburner.com/rsscna/intworld", lim=12),
    dict(sec="intl", name="香港電台國際", url="https://rthk9.rthk.hk/rthk/news/rss/c_expressnews_cinternational.xml", lim=12),
    dict(sec="intl", name="德國之聲",   url="https://rss.dw.com/rdf/rss-chi-all", lim=12),
    # 賺錢／動態（HN 用關鍵字查詢，確保同錢有關；Product Hunt 睇新產品＝新機會）
    dict(sec="money", name="Reddit r/sidehustle", tag="網民討論", url="https://www.reddit.com/r/sidehustle/top/.rss?t=week&limit=15", alt="https://old.reddit.com/r/sidehustle/top/.rss?t=week&limit=15", lim=10),
    dict(sec="money", name="Hacker News", tag="實戰案例", url="https://hnrss.org/newest?q=side+hustle", lim=6),
    dict(sec="money", name="Hacker News", tag="收入故事", url="https://hnrss.org/newest?q=%22how+I+made%22", lim=6),
    dict(sec="money", name="Product Hunt", tag="新產品", url="https://www.producthunt.com/feed", lim=12),
    dict(sec="money", name="明報經濟", tag="財經", url="https://news.mingpao.com/rss/pns/s00004.xml", lim=12),
    dict(sec="money", name="香港電台財經", tag="財經", url="https://rthk9.rthk.hk/rthk/news/rss/c_expressnews_cfinance.xml", lim=10),
    dict(sec="money", name="FT 中文網", tag="財經", url="https://www.ftchinese.com/rss/news", lim=8),
    # 健康
    dict(sec="health", name="ScienceDaily 健康", tag="研究", url="https://www.sciencedaily.com/rss/health_medicine.xml", lim=8),
    dict(sec="health", name="ScienceDaily 大腦", tag="心理", url="https://www.sciencedaily.com/rss/mind_brain.xml", lim=8),
    dict(sec="health", name="Heho 健康", tag="中文", url="https://heho.com.tw/feed", lim=8),
    dict(sec="health", name="泛科學", tag="科普", url="https://pansci.asia/feed", lim=6),
    dict(sec="health", name="政府新聞公報", tag="官方", url="https://www.info.gov.hk/gia/rss/general_zh.xml", lim=6,
         match=["衞生", "衛生", "醫院", "疫苗", "流感", "健康", "醫管局", "食物安全", "傳染"]),
    # 學習
    dict(sec="study", name="阮一峰週刊", tag="週刊", url="https://www.ruanyifeng.com/blog/atom.xml", lim=4),
    dict(sec="study", name="Scott H Young", tag="學習方法", url="https://www.scotthyoung.com/blog/feed/", lim=6),
    dict(sec="study", name="Ness Labs", tag="思考", url="https://nesslabs.com/feed", lim=6),
    dict(sec="study", name="Learning Scientists", tag="學習科學", url="https://www.learningscientists.org/blog?format=rss", lim=6),
    dict(sec="study", name="The Marginalian", tag="思考", url="https://www.themarginalian.org/feed/", lim=5),
]

SEC_ORDER = ["money", "health", "study", "hk", "cn", "intl"]
MAX_AGE_DAYS = {"money": 21, "health": 30, "study": 75}

# ── 指引庫（數字／做法來自 2026-10 核實資料，需定期覆核）──────────
GUIDES = {
 "money": [
  dict(n="產品化服務（你接單、AI 交付）", rows=[
    ("首筆收入","1–2 星期","hi"), ("實數","一單 2,000–8,000 HKD 起；人手只需 10–20 分鐘"),
    ("門檻","要有一項你做得到、講得出的專業（機電／BMS／工程文件）"),
    ("AI 幫手","交付 90–95%"), ("風險","低：先收訂金，唔壓貨","lo"), ("出處","2026-10 服務定價觀察")]),
  dict(n="專業模板／數位產品（Gumroad・Etsy）", rows=[
    ("首筆收入","2–6 星期","hi"), ("實數","平台中位數 US$72/月；44% 產品收入為 0；首 90 天 US$50–300/月；第 12 個月 US$1,000+"),
    ("門檻","窄專業市場（工程估算表、點表模板）比大眾模板好賣，可定價 US$50–199"),
    ("AI 幫手","生產 85–90%"), ("風險","中：上架免費＝冇流量，難在推廣","mid"), ("出處","Gumroad／Etsy 公開統計")]),
  dict(n="手機／限量品炒賣（差價）", rows=[
    ("首筆收入","即日","hi"), ("實數","收益 = 回收價 − 成本 − 車費；單機差價通常幾百至一、兩千"),
    ("門檻","要本金、要即時價（先達回收價／Apple 取貨名額）"),
    ("AI 幫手","代查價、代監察名額 80%；落單付款要你本人"),
    ("風險","高：價格即日可反轉，壓貨最痛","hi"), ("出處","本機價格監察實測")]),
  dict(n="穩定幣／存款收息（資本換收入）", rows=[
    ("首筆收入","即時","hi"), ("實數","3.8–5.0% APY；每月 500 HKD 需本金 12–16 萬"),
    ("門檻","要有閒置本金；穩定幣冇存款保障"),
    ("AI 幫手","近乎 100%（設定一次）"), ("風險","中：對手方／合約風險","mid"), ("出處","Sky／Kraken／Aave 2026-10 報價")]),
  dict(n="Crypto 空投（airdrop farming）", rows=[
    ("首筆收入","6–12 個月","hi"), ("實數","有效時薪 US$5–25；中位農夫 US$2,000–15,000/年，需 100–400 小時"),
    ("門檻","本金 US$500–5,000，要長期操作多錢包"), ("AI 幫手","60–70%（記錄、腳本、稅務整理）"),
    ("風險","高：Sybil 過濾可一夜清零","hi"), ("出處","空投收益統計")]),
  dict(n="開源賞金（Algora 等）", rows=[
    ("首筆收入","2–8 星期","hi"), ("實數","每單 US$50–2,500，實測平均 US$7.82/小時（競爭 PR 8–158 個，合併率約 15%）"),
    ("門檻","要識該專案技術棧"), ("AI 幫手","70%（但市場已被 agent 淹沒）"),
    ("風險","中：做白工機會大","mid"), ("出處","Algora 實測")]),
  dict(n="無人出鏡 YouTube／內容", rows=[
    ("首筆收入","6–24 個月","hi"), ("實數","要 1,000 訂閱 + 4,000 小時；>90% 頻道到唔到 1,000 訂閱"),
    ("門檻","要 3–5 條／週，每條 3–8 小時"), ("AI 幫手","70–80%（腳本、剪輯、配音）"),
    ("風險","高：有案例 150 天燒 US$26,311、收 US$15,218","hi"), ("出處","變現門檻公開數據")]),
  dict(n="Print on demand（印圖 T 恤等）", rows=[
    ("首筆收入","6–18 個月","hi"), ("實數","服飾淨利 15–20%；要見錢通常半年以上"),
    ("門檻","設計 + 廣告費"), ("AI 幫手","85%"), ("風險","中：廣告費食利潤","mid"), ("出處","行業平均值")]),
  dict(n="Amazon KDP 電子書", rows=[
    ("首筆收入","3–12 個月","hi"), ("實數","飽和；首書預算 US$3,700–4,700（大部分係廣告）；新書每格式每週限 2 本"),
    ("門檻","要廣告預算 + 耐性"), ("AI 幫手","80%"), ("風險","高：九個月近零收入屬常見","hi"), ("出處","KDP 實測案例")]),
  dict(n="GPU 硬件出租（Vast.ai）", rows=[
    ("首筆收入","2–4 星期","hi"), ("實數","4090 半載出租：扣 25% 平台費及電費後月淨 HK$479，折舊 HK$520 → 負數"),
    ("門檻","只出租你已經有嘅卡；唔好為此買卡"), ("AI 幫手","100%（被動）"),
    ("風險","高：新戶上座率 10–25%","hi"), ("出處","Vast.ai + 中電 2026 電價")]),
  dict(n="微任務／AI 標註（Toloka・Appen）", rows=[
    ("首筆收入","1–3 星期","hi"), ("實數","US$2–14/小時；部分「專家」項目低過最低工資"),
    ("門檻","要真人身份認證，AI 代做 0%"), ("AI 幫手","0%（平台會封號，而且自動化唔會多賺）"),
    ("風險","低金額、低風險","lo"), ("出處","平台公開費率")]),
 ],
 "health": [
  dict(n="每小時起身走 2 分鐘", rows=[
    ("做幾多","久坐每 30–60 分鐘起身 2 分鐘（行去斟水／行樓梯一層）","hi"),
    ("為何有效","打斷久坐可改善餐後血糖同腰圍；久坐時間本身係獨立風險因子"),
    ("幾時做","工作時，用手機每小時震一次"), ("證據","WHO 2020 體能活動指引；久坐中斷研究（短期代謝改善）"),
    ("最低要求","一日 4 次就夠，唔需要換運動服")]),
  dict(n="固定起床時間，睡 7–9 小時", rows=[
    ("做幾多","成人每晚 7–9 小時，起床時間固定在 ±30 分鐘內","hi"),
    ("為何有效","睡眠時長同記憶固化、情緒調節、免疫力、代謝都有關；固定起床時間比固定入睡時間更容易做到"),
    ("幾時做","今晚開始：先固定起床，睡意會自己追上"),
    ("證據","AASM／Sleep Research Society 成人睡眠共識（≥7 小時）；睡眠與記憶固化文獻"),
    ("最低要求","只做一件事：明天同今日同一個時間起身")]),
  dict(n="早上見光 10–20 分鐘", rows=[
    ("做幾多","起身後 1 小時內，戶外或窗邊 10–20 分鐘，唔戴太陽眼鏡","hi"),
    ("為何有效","晨光校準生理時鐘，令晚上較準時有睡意，亦影響日間情緒同警覺度"),
    ("幾時做","早餐前後；陰天都有用，室內燈光通常唔夠"),
    ("證據","晝夜節律與光暴露研究；光照治療對季節性抑鬱有實證"),
    ("最低要求","返工路途中段唔好全程遮光／戴帽")]),
  dict(n="每週 2 次肌力訓練", rows=[
    ("做幾多","每週 2 次，每次 20–30 分鐘，練大肌群（深蹲、推、拉、髖伸）","hi"),
    ("為何有效","肌力同全因死亡率、跌倒風險、血糖控制、老年自理能力都有關；30 歲後肌肉每十年流失 3–8%"),
    ("幾時做","固定兩個時段（例如星期二、五），唔好靠「有時間就做」"),
    ("證據","WHO 2020 指引：成人每週 ≥2 天肌力訓練"),
    ("最低要求","10 分鐘：深蹲 3×10、掌上壓 3×8、平板支撐 3×20 秒")]),
  dict(n="每日 5 份蔬果", rows=[
    ("做幾多","一日 400 克左右（約 5 份：3 份菜 2 份水果）","hi"),
    ("為何有效","蔬果攝取量同心血管病、部分癌症、全因死亡率呈反向關係"),
    ("幾時做","每餐加一份，唔需要一次食齊"),
    ("證據","WHO／WCRF 建議每日 ≥400 克蔬果"),
    ("最低要求","午餐同晚餐各加一手掌份量嘅菜")]),
  dict(n="3 分鐘呼吸練習", rows=[
    ("做幾多","吸 4 秒、呼 6 秒，做 3 分鐘（約 18 次）","hi"),
    ("為何有效","慢而長的呼氣提高副交感神經活動，即時降低心率同主觀緊張；對急性焦慮有短期效果"),
    ("幾時做","開會前、被人激到、睡前"),
    ("證據","慢呼吸／心率變異度研究；短期正念介入對焦慮的中等強度證據"),
    ("最低要求","一次 6 個呼吸就夠，唔需要墊同 app")]),
  dict(n="每日一次真人對話", rows=[
    ("做幾多","每日一次 5 分鐘以上嘅真人對話（見面或電話，唔係打字）","hi"),
    ("為何有效","社交連結同死亡風險、抑鬱、免疫力相關；孤獨嘅健康風險可比吸煙"),
    ("幾時做","食飯時間，或收工前 5 分鐘打一個電話"),
    ("證據","美國醫務總監 2023 孤獨與孤立報告；社交連結與死亡率 meta-analysis"),
    ("最低要求","今日主動問一個人「你今日點呀」")]),
  dict(n="睡前一小時調暗", rows=[
    ("做幾多","睡前 60 分鐘：燈調暗、螢幕轉夜間模式、唔睇工作訊息","hi"),
    ("為何有效","強光同訊息刺激延遲入睡、減少深睡；儀式化嘅睡前流程令入睡更快"),
    ("幾時做","由「刷牙時間」倒數一小時"),
    ("證據","睡前光暴露與褪黑素抑制研究；睡眠衛生指引"),
    ("最低要求","叉電位置搬離床頭")]),
  dict(n="寫低今日三件好事", rows=[
    ("做幾多","每晚寫 3 件具體嘅好事同「為何會發生」","hi"),
    ("為何有效","持續一週已見情緒改善，效果可維持數月；比寫「感恩」空泛字句有效，關鍵係寫原因"),
    ("幾時做","睡前，同刷牙綁埋一齊"),
    ("證據","Seligman 2005 正向心理學隨機對照試驗（three good things）"),
    ("最低要求","3 行字，手機備忘錄都可以")]),
 ],
 "study": [
  dict(n="主動回憶：合上書自己講一次", rows=[
    ("做法","讀完一節，合上書／關掉講義，用白紙寫出或講出重點，再對答案補漏","hi"),
    ("為何有效","提取記憶本身會強化記憶（testing effect），比重讀有效得多；同一時間內，自我測驗嘅保留率約係重讀兩倍"),
    ("幾時用","任何要記住嘅內容；尤其證照、技術文件、語言"),
    ("證據","Roediger & Karpicke 2006（testing effect）；Dunlosky 2013 教學法回顧列為高效度"), ("最小起步","每讀完一段問自己：呢段講咩？講唔出就返去讀")]),
  dict(n="間隔重複（Anki／卡片）", rows=[
    ("做法","把要記嘅知識做成問答卡，隔 1 日、3 日、7 日、21 日重溫","hi"),
    ("為何有效","遺忘曲線下，喺就快忘記之前重溫，記憶保持最有效率；比集中溫習省一半以上時間"),
    ("幾時用","詞彙、法規條文、BACnet 點位、公式"),
    ("證據","Cepeda 2006 meta-analysis（spacing effect）；Dunlosky 2013 高效度方法之一"),
    ("最小起步","今日先做 10 張卡，唔需要一次建全套")]),
  dict(n="交錯練習：混住練唔同題型", rows=[
    ("做法","一次練習入面交替處理唔同類型題目，唔好一個類型練到熟才換","hi"),
    ("為何有效","交錯迫使你每次判斷「呢題係邊類、用邊個方法」，呢個判斷力才係實戰要嘅（interleaving）"),
    ("幾時用","數學、電路、程式、診斷類工作"), ("證據","Rohrer & Taylor 2007；Dunlosky 2013"),
    ("最小起步","練習時把兩三種題目洗牌")]),
  dict(n="費曼技巧：講到外行明白", rows=[
    ("做法","用最簡單嘅字寫／講一次，唔用行話；卡住嘅位置就係你未真明嘅位置，返去補","hi"),
    ("為何有效","把知識重新組織成因果鏈，暴露缺口；生成式解釋（self-explanation）有實證提升理解"),
    ("幾時用","準備講解、寫報告、面試前"), ("證據","self-explanation 研究；Chi 2008 回顧"),
    ("最小起步","用 5 句向一個唔識嘅人解釋你今日學咗咩")]),
  dict(n="刻意練習：針對弱點 + 即時回饋", rows=[
    ("做法","揀一個具體弱點，做剛好超出能力嘅練習，每做完就有回饋（對答案／師傅／錄影自己）","hi"),
    ("為何有效","重複已識嘅東西唔會進步；進步來自邊緣難度＋回饋修正"),
    ("幾時用","任何技能：焊接、寫程式、談判、英文口語"), ("證據","Ericsson 刻意練習研究（注意：對專家表現的解釋力有爭議，但對技能訓練有效）"),
    ("最小起步","今日錄一段 2 分鐘自己嘅表現，睇一次")]),
  dict(n="先輸出，後輸入", rows=[
    ("做法","睇資料前先做一題／先寫一版，再對照正確答案","hi"),
    ("為何有效","先嘗試（即使錯）會令之後接收嘅資訊更容易被記住（pretesting effect），亦令你知要睇邊部分"),
    ("幾時用","學新工具、新標準、新軟件"), ("證據","pretesting effect 研究（Richland 2009 等）"),
    ("最小起步","開文件前先猜答案寫低")]),
  dict(n="筆記改成問題庫", rows=[
    ("做法","唔好抄原文；每條筆記寫成一個問題 + 一句答案，之後直接當卡片用","hi"),
    ("為何有效","抄寫係低效編碼；寫成問題即刻變成可測試嘅材料，接上主動回憶同間隔重複"),
    ("幾時用","上課、睇規格書、開會"), ("證據","筆記組織方式與學習成效研究（生成式筆記優於逐字抄錄）"),
    ("最小起步","下次開會把 3 條筆記改寫成 3 條問題")]),
  dict(n="90 分鐘深度時段", rows=[
    ("做法","每日一段 90 分鐘：電話靜音、通知關掉、只做一件事","hi"),
    ("為何有效","切換成本高，碎片時間做唔到深度理解；注意力恢復需要真正離開任務"),
    ("幾時做","一日最清醒嘅時段（多數人係上午）"), ("證據","task-switching 成本研究；深度工作實踐報告"),
    ("最小起步","明日 25 分鐘無通知，只做最難嗰件事")]),
  dict(n="學完就睡，唔好通宵", rows=[
    ("做法","重要內容學完，至少留 6 小時睡眠；唔好靠通宵衝刺","hi"),
    ("為何有效","睡眠期間海馬體重播並鞏固新記憶；睡眠不足直接損害編碼同提取"),
    ("幾時用","考試／匯報前一晚"), ("證據","睡眠與記憶固化研究（Walker 等）"),
    ("最小起步","今晚 23:30 收機，早上早 45 分鐘起身補溫習")]),
 ],
}

# ── 工具 ───────────────────────────────────────────────
def fetch(url, tries=2):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*",
                "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
            })
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (401, 403, 404, 429):   # 唔值得重試
                break
            time.sleep(1.0 * (i + 1))
        except Exception as e:
            last = e
            time.sleep(1.0 * (i + 1))
    raise last

def localname(tag):
    return tag.rsplit("}", 1)[-1].lower()

def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        return parsedate_to_datetime(s).astimezone(HKT)
    except Exception:
        pass
    t = s.replace("Z", "+00:00")
    for fmt in (None, "%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            d = datetime.fromisoformat(t) if fmt is None else datetime.strptime(t, fmt)
            if d.tzinfo is None:
                d = d.replace(tzinfo=HKT)
            return d.astimezone(HKT)
        except Exception:
            continue
    return None

def parse_feed(raw, src):
    root = ET.fromstring(raw)
    out = []
    for el in root.iter():
        ln = localname(el.tag)
        if ln not in ("item", "entry"):
            continue
        title = link = desc = date = ""
        for ch in el:
            cl = localname(ch.tag)
            if cl == "title":
                title = (ch.text or "").strip()
            elif cl == "link":
                href = ch.get("href")
                if href and (ch.get("rel") in (None, "alternate")):
                    link = href
                elif not link and (ch.text or "").strip():
                    link = ch.text.strip()
            elif cl in ("description", "summary", "content", "encoded"):
                if not desc:
                    desc = ch.text or ""
            elif cl in ("pubdate", "published", "updated", "date"):
                if not date:
                    date = ch.text or ""
        title = strip_html(title)
        if not title or not link:
            continue
        if title.startswith("【重溫】") or "新聞天地" in title:
            continue
        d = parse_date(date)
        sm = strip_html(desc)
        sm = re.sub(r"(Article URL|Comments URL):\s*\S+", "", sm)
        sm = re.sub(r"(Points|#\s*Comments):\s*\d+", "", sm)
        sm = sm.replace("Discussion | Link", "").replace("Discussion", "").strip()
        sm = re.sub(r"\s{2,}", " ", sm)[:150]
        if len(sm) < 12 or sm.lower() in ("comments", "查看全文", "read more"):
            sm = ""
        out.append(dict(
            t=strip_html(title)[:180],
            l=link.strip(),
            s=src,
            d=(d or datetime.now(HKT)).isoformat(),
            ts=(d or datetime.now(HKT)).timestamp(),
            x=sm,
        ))
    return out


def build():
    prev = {}
    try:
        with open(os.path.join(HERE, "data.json"), "r", encoding="utf-8") as f:
            prev = json.load(f)
    except Exception:
        prev = {}

    buckets = {k: [] for k in SEC_ORDER}
    health = []
    cache = dict(prev.get("feed_cache", {}))
    newcache = {}
    for f in FEEDS:
        key = f["url"]
        try:
            try:
                items = parse_feed(fetch(f["url"]), f["name"])
            except Exception:
                if not f.get("alt"):
                    raise
                items = parse_feed(fetch(f["alt"]), f["name"])
            if f.get("match"):
                items = [i for i in items if any(k in i["t"] for k in f["match"])]
            if not items:
                raise ValueError("0 items")
            items.sort(key=lambda i: i["ts"], reverse=True)
            use = items[: f["lim"]]
            newcache[key] = use
            health.append(dict(src=f["name"], sec=f["sec"], ok=True, n=len(use)))
        except Exception as e:
            use = cache.get(key, [])[: f["lim"]]
            cached = bool(use)
            if cached:            # 失敗都保住上次成功嘅資料，唔會令 cache 條目消失
                newcache[key] = use
            health.append(dict(src=f["name"], sec=f["sec"], ok=False, err=type(e).__name__,
                               n=len(use), cached=cached))
            print(f"  ! {f['name']}: {type(e).__name__} {e}" + ("（用上次成功資料）" if cached else ""))
        for it in use:
            it["g"] = f.get("tag", "")
            buckets[f["sec"]].append(it)

    data = dict(generated_at=datetime.now(HKT).isoformat(timespec="seconds"),
                generated_ts=time.time(), guides=GUIDES, health=health, sections={},
                feed_cache=newcache)
    for k in SEC_ORDER:
        arr = buckets[k]
        days = MAX_AGE_DAYS.get(k)
        if days:            # 只留最近資料，免得舊文頂住版面
            cut = time.time() - days * 86400
            arr = [i for i in arr if i["ts"] >= cut]
        arr.sort(key=lambda i: i["ts"], reverse=True)
        seen, out = set(), []
        for it in arr:
            key = re.sub(r"[^\w\u4e00-\u9fff]", "", it["t"])[:40]
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        pri = {
            "money":  {"網民討論": 0, "實戰案例": 0, "收入故事": 1, "新產品": 2},
            "health": {"官方": 0, "研究": 0, "心理": 0, "科普": 1, "中文": 2},
            "study":  {"學習方法": 0, "學習科學": 0, "週刊": 0, "思考": 1},
        }.get(k)
        if pri:
            out.sort(key=lambda i: (pri.get(i.get("g", ""), 3), -i["ts"]))
        srcs = sorted({i["s"] for i in out})
        block = dict(items=out[:48], sources=srcs, stale=False)
        if not out and prev.get("sections", {}).get(k, {}).get("items"):
            old = dict(prev["sections"][k]); old["stale"] = True
            block = old
        data["sections"][k] = block

    with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "data.js"), "w", encoding="utf-8") as f:
        f.write("/* generated by refresh.py — 請勿手改 */\nwindow.DAILY=")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    return data

if __name__ == "__main__":
    t0 = time.time()
    print("抓取中…")
    d = build()
    print(f"\n完成 {d['generated_at']}  用時 {time.time()-t0:.1f}s")
    for k in SEC_ORDER:
        s = d["sections"][k]
        newest = s["items"][0]["d"][11:16] if s["items"] else "—"
        flag = "（沿用舊資料）" if s.get("stale") else ""
        print(f"  {k:<6} {len(s['items']):>2} 條  最新 {newest}  來源 {len(s['sources'])}{flag}")
    bad = [h["src"] for h in d["health"] if not h["ok"]]
    print("  失敗來源：" + ("、".join(bad) if bad else "無"))
