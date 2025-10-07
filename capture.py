# capture.py
# pulls top sites list and screenshots top 10 homepages into the current directory

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import tldextract

RAW_LIST_URL = "https://raw.githubusercontent.com/bensooter/URLchecker/master/top-1000-websites.txt"

def load_top_sites(list_url: str = RAW_LIST_URL):
    resp = requests.get(list_url, timeout=20)
    resp.raise_for_status()
    lines = [ln.strip() for ln in resp.text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    out = []
    for ln in lines:
        if ln.startswith("http://") or ln.startswith("https://"):
            out.append(ln)
        else:
            out.append("https://" + ln)
    return out

def domain_filename(url: str) -> str:
    ex = tldextract.extract(url)
    # keep domain + suffix so files are unique (e.g., google.com.png)
    name = f"{ex.domain}.{ex.suffix}" if ex.suffix else ex.domain
    safe = name.replace("/", "_").replace("\\", "_")
    return f"{safe}.png"

def capture(url: str):
    top_ten = load_top_sites(url)[:10]

    # Selenium 4 setup
    options = Options()
    options.add_argument("--headless=new")   # Pylance-safe
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        for site in top_ten:
            try:
                driver.get(site)
                time.sleep(2)  # quick wait for above-the-fold to render
                # small scroll to trigger lazy stuff
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                fname = domain_filename(site)
                driver.save_screenshot(os.path.join(os.getcwd(), fname))
                print(f"Saved screenshot: {fname}")
            except Exception as e:
                print(f"Failed to screenshot {site}: {e}")
    finally:
        driver.quit()

    return top_ten

if __name__ == "__main__":
    url = RAW_LIST_URL
    print(f"Problem 3: {capture(url)}")
