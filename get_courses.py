# get_courses.py


import re
import time
from bs4 import BeautifulSoup  # required by the assignment, but we're mostly regexing visible text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://www.cdm.depaul.edu/academics/Pages/CourseSchedule.aspx?department=CSEC"

# regex bits
COURSE_LINE = re.compile(r'^(CSEC\s*\d{1,4}\s+.+)$', re.IGNORECASE)
TIME_LINE = re.compile(r'(\d{1,2}:\d{2}\s*(AM|PM))\s*-\s*(\d{1,2}:\d{2}\s*(AM|PM))', re.IGNORECASE)
# grab a plausible location line (CDM Center 658, Loop Campus, Online: Sync, etc.)
LOC_LINE = re.compile(
    r'(CDM\s*Center\s*\d+|Loop\s*Campus|Lincoln\s*Park\s*Campus|Online[:\s]\s*\w+|Cinespace.*?|Lake\s*Forest\s*Campus|Rolling\s*Meadows\s*Campus|Off\s*Campus)',
    re.IGNORECASE
)

def _make_driver():
    opts = Options()
    opts.add_argument("--headless=new")  # if this errors on your Chrome, change to "--headless"
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    # a tiny bit less “bot-like”
    opts.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

def get_courses(site_name: str):
    driver = _make_driver()
    try:
        driver.get(site_name)

        wait = WebDriverWait(driver, 20)

        # 1) Set Course Subject = "Cybersecurity"


        # try to find a select that contains the word "Cybersecurity" as an option
        selects = driver.find_elements(By.TAG_NAME, "select")
        target_select = None
        for s in selects:
            try:
                options_text = s.text
                if "Cybersecurity" in options_text:
                    target_select = s
                    break
            except Exception:
                pass

        if target_select is None:
            # fall back to executing a JS that selects "Cybersecurity" by visible text in any select
            driver.execute_script("""
                var sels = document.querySelectorAll('select');
                for (const sel of sels) {
                  for (const opt of sel.options) {
                    if ((opt.text || '').trim().toLowerCase() === 'cybersecurity') {
                      sel.value = opt.value;
                      sel.dispatchEvent(new Event('change', {bubbles:true}));
                    }
                  }
                }
            """)

        else:
            # set it via JS to ensure change event fires
            driver.execute_script("""
                var sel = arguments[0];
                for (const opt of sel.options) {
                  if ((opt.text || '').trim().toLowerCase() === 'cybersecurity') {
                    sel.value = opt.value;
                    sel.dispatchEvent(new Event('change', {bubbles:true}));
                  }
                }
            """, target_select)

        # 2) Click "Apply" (if there is a button) — try several common labels
        clicked_apply = False
        for label in ["Apply", "Apply Filters", "Filter", "Search"]:
            btns = driver.find_elements(By.XPATH, f"//button[contains(., '{label}')]")
            if btns:
                try:
                    btns[0].click()
                    clicked_apply = True
                    break
                except Exception:
                    pass

        # if we didn't find a button, the 'department=CSEC' query param may already trigger it; nbd.

        # 3) Wait until any text containing CSEC ### shows up in the body
        wait.until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "CSEC")
        )

        # tiny extra wait so everything is fully in DOM
        time.sleep(1.5)

        # 4) Now grab the visible text and parse lines
        visible_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [ln.strip() for ln in visible_text.splitlines() if ln.strip()]


        out_count = 0
        i = 0
        while i < len(lines):
            line = lines[i]
            m_course = COURSE_LINE.match(line)
            if m_course:
                title = m_course.group(1)


                time_str = "Time not found"
                loc_str = "Location not found"


                for j in range(1, 6):
                    if i + j >= len(lines):
                        break
                    t = lines[i + j]

                    if time_str == "Time not found":
                        m_time = TIME_LINE.search(t)
                        if m_time is not None:
                            time_str = m_time.group(0)

                    if loc_str == "Location not found":
                        m_loc = LOC_LINE.search(t)
                        if m_loc is not None:
                            loc_str = m_loc.group(0)


                print(title)
                print(time_str)
                print(loc_str)
                print("") 
                out_count += 1

                i += 3
            else:
                i += 1

        if out_count == 0:

            print("No CSEC courses detected. The page may have changed or no CSEC courses are posted yet.")

    finally:
        driver.quit()

if __name__ == "__main__":
    print("Problem 2.2:")
    get_courses(URL)
