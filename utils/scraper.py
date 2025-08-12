# utils/scraper.py
import os, re
from time import sleep
from contextlib import redirect_stderr
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# ========= Normalizador numérico =========
def to_int(num_str: str) -> int:
    """
    Convierte textos humanos a enteros:
    '2,723'->2723 ; '12.345'->12345 ; '154k'/'153 mil'->154000/153000 ;
    '1,2M'/'1.2 M'/'1,2 mill.'->1200000
    """
    if not num_str:
        return 0
    s = num_str.lower().strip().replace("\u202f", " ").replace("\xa0", " ")
    s = s.replace("millones", "m").replace("millón", "m").replace("mill.", "m")
    s = s.replace(" mil", "k").replace("mil", "k")
    mult = 1
    if s.endswith("k"):
        mult, s = 1_000, s[:-1]
    elif s.endswith("m"):
        mult, s = 1_000_000, s[:-1]
    s = s.strip()
    if mult == 1:
        s = re.sub(r'(?<=\d)[\.,\s](?=\d{3}\b)', '', s)   # separadores miles
        s = re.split(r'[.,]', s)[0]                       # corta decimales
        digits = re.sub(r'\D', '', s)
        return int(digits) if digits else 0
    else:
        s = s.replace(".", "").replace(",", ".")
        try:
            return int(float(s) * mult)
        except:
            digits = "".join(re.findall(r"\d+", s))
            return int(digits) * mult if digits else 0

# ========= Selenium driver =========
def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--disable-features=VizDisplayCompositor")
    opts.add_argument("--lang=en-US")  # ayuda en FB (followers/likes)
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    # Silenciar ruido de DevTools en la consola
    f = open(os.devnull, "w")
    ctx = redirect_stderr(f); ctx.__enter__()
    driver = webdriver.Chrome(service=service, options=opts)
    driver._stderr_silencer = (ctx, f)
    return driver

def close_driver(driver):
    try:
        driver.quit()
    finally:
        if hasattr(driver, "_stderr_silencer"):
            ctx, f = driver._stderr_silencer
            ctx.__exit__(None, None, None)
            f.close()

# ========= Extractores =========
NUM_TOKEN = r'(\d[\d\.\,\s]*\s*(?:k|m|mil(?:l\.)?|mill(?:\.)?)?)'

# --- Instagram ---
def ig_get_meta_text(driver):
    for xp in ("//meta[@property='og:description']", "//meta[@name='description']"):
        els = driver.find_elements(By.XPATH, xp)
        if els:
            c = els[0].get_attribute("content") or ""
            if c.strip():
                return c.strip()
    return ""

def _grab(label_words, text):
    """Busca '123 label' o 'label 123' (ES/EN) y devuelve el número como string."""
    lbl = "|".join(label_words)
    m = re.search(fr'{NUM_TOKEN}\s*(?:{lbl})', text, flags=re.I)
    if m: return m.group(1).strip()
    m = re.search(fr'(?:{lbl})\s*{NUM_TOKEN}', text, flags=re.I)
    if m: return m.group(1).strip()
    return ""

def extract_instagram(driver, url):
    wait = WebDriverWait(driver, 12)
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    sleep(1.2)

    meta = ig_get_meta_text(driver)
    page_text = (meta or driver.find_element(By.TAG_NAME, "body").text).lower()

    posts_txt_raw     = _grab(["posts?", "publicaciones?"], page_text)
    followers_txt_raw = _grab(["followers", "seguidores"], page_text)
    following_txt_raw = _grab(["following", "seguidos"], page_text)

    posts_txt = str(to_int(posts_txt_raw)) if posts_txt_raw else ""
    return {
        "platform": "instagram",
        "posts_text": posts_txt,
        "followers_text": followers_txt_raw,
        "following_text": following_txt_raw,
        "posts": to_int(posts_txt),
        "followers": to_int(followers_txt_raw),
        "following": to_int(following_txt_raw),
    }

# --- Facebook ---
def fb_num_token():
    return r'(\d[\d\.\,\s]*\s*(?:[KkMm]|mil(?:l\.)?|mill(?:\.)?)?)'

def _extract_by_label(texto, labels):
    """Evita confundir likes con followers cuando van en la misma línea."""
    t = (texto or "").replace("\u202f", " ").replace("\xa0", " ")
    for label in labels:
        m = re.search(rf'{fb_num_token()}\s*{re.escape(label)}', t, flags=re.I)
        if m: return m.group(1).strip()
        m = re.search(rf'{re.escape(label)}\s*{fb_num_token()}', t, flags=re.I)
        if m: return m.group(1).strip()
    return ""

def extract_facebook(driver, url):
    wait = WebDriverWait(driver, 12)
    clean = url.split("?")[0].rstrip("/")
    slug = clean.split("/")[-1] if "/" in clean else clean

    followers = ""
    likes = ""

    intentos = [
        f"https://www.facebook.com/{slug}?locale=en_US",
        f"https://m.facebook.com/{slug}?locale=en_US",
        f"https://m.facebook.com/{slug}/about?locale=en_US",
        f"https://mbasic.facebook.com/{slug}",
    ]

    for u in intentos:
        try:
            driver.get(u)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            sleep(1.2)
            body_text = driver.find_element(By.TAG_NAME, "body").text

            if not followers:
                followers = _extract_by_label(body_text, ["followers", "seguidores"])
            if not likes:
                likes = _extract_by_label(body_text, ["likes", "me gusta"])

            if followers and likes:
                break
        except Exception:
            continue

    return {
        "platform": "facebook",
        "followers_text": followers or "",
        "likes_text": likes or "",
        "followers": to_int(followers),
        "likes": to_int(likes),
    }

# ========= API pública para Flask =========
def scrape_stats_from_url(url: str) -> Dict[str, Any]:
    """
    Devuelve métricas de un perfil IG/FB.
    - Instagram -> posts, followers, following (+ *_text)
    - Facebook  -> followers, likes (+ *_text)
    {} si URL no soportada o error.
    """
    if not url or not isinstance(url, str):
        return {}

    lower_url = url.lower().strip()
    if ("instagram.com" not in lower_url) and ("facebook.com" not in lower_url):
        return {}

    driver = None
    try:
        driver = make_driver()
        if "instagram.com" in lower_url:
            s = extract_instagram(driver, url)
            return {
                "platform": "instagram",
                "posts_text": s.get("posts_text", "") or "",
                "followers_text": s.get("followers_text", "") or "",
                "following_text": s.get("following_text", "") or "",
                "posts": int(s.get("posts", 0) or 0),
                "followers": int(s.get("followers", 0) or 0),
                "following": int(s.get("following", 0) or 0),
            }
        else:
            s = extract_facebook(driver, url)
            return {
                "platform": "facebook",
                "followers_text": s.get("followers_text", "") or "",
                "likes_text": s.get("likes_text", "") or "",
                "followers": int(s.get("followers", 0) or 0),
                "likes": int(s.get("likes", 0) or 0),
            }
    except Exception:
        return {}
    finally:
        if driver:
            close_driver(driver)

def scrape_reviews_from_url(url: str, limit: int = 50) -> List[str]:
    """
    Wrapper de compatibilidad (si tu app ya usa este nombre):
    - Instagram -> [posts, followers, following] (strings)
    - Facebook  -> [followers, likes] (strings)
    """
    stats = scrape_stats_from_url(url)
    if not stats:
        return []

    if stats.get("platform") == "instagram":
        return [
            str(stats.get("posts", 0)),
            str(stats.get("followers", 0)),
            str(stats.get("following", 0)),
        ]
    elif stats.get("platform") == "facebook":
        return [
            str(stats.get("followers", 0)),
            str(stats.get("likes", 0)),
        ]
    return []

# ========= Demo local =========
if __name__ == "__main__":
    DEMO_URL = "https://www.instagram.com/claroecuador/"
    data = scrape_stats_from_url(DEMO_URL)
    print("== STATS =="); print(data)
    print("== WRAPPER =="); print(scrape_reviews_from_url(DEMO_URL))
