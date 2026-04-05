# ================================================
# actions.py
# ================================================
# All reusable functions - clean, heavily documented, easy to add/remove

import time
import random
import subprocess
import yaml
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

# Easy log removal: comment out the next 3 lines after first successful run
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)
logger.info("=== TikTok Lite Automation Started ===")

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def human_delay(cfg, key="min_sec", extra_key=None):
    """Random realistic delay - the heart of humanoid behavior"""
    min_d = cfg["human_delay"][key]
    max_d = cfg["human_delay"][extra_key] if extra_key else cfg["human_delay"]["max_sec"]
    delay = random.uniform(min_d, max_d)
    time.sleep(delay)
    return delay

def adb_command(command: list):
    """Run ADB command and log it"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"ADB: {' '.join(command)}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"ADB failed: {e}")
        raise

def force_clear_app_data(cfg):
    """System-level clear data (bypasses UI completely)"""
    package = cfg["app"]["package"]
    adb_command(["adb", "shell", "pm", "clear", package])
    logger.info(f"✅ Force-cleared data for {package} (fresh install behavior)")

def init_driver(cfg):
    """Start Appium session"""
    desired_caps = {
        "platformName": "Android",
        "automationName": cfg["appium"]["automation_name"],
        "newCommandTimeout": cfg["appium"]["new_command_timeout"],
        "appPackage": cfg["app"]["package"],
        "appActivity": cfg["app"]["activity"],
        "noReset": False,
        "fullReset": False,
        "language": "en",
        "locale": "US"
    }
    if cfg["device"]["udid"]:
        desired_caps["udid"] = cfg["device"]["udid"]

    driver = webdriver.Remote(cfg["appium"]["server_url"], options=None, desired_capabilities=desired_caps)
    logger.info("✅ Appium driver initialized")
    return driver

def wait_and_click(driver, locator_dict, timeout=15):
    """Universal wait + click with WebDriverWait"""
    by_type = {
        "resource-id": AppiumBy.ID,
        "text": AppiumBy.ANDROID_UIAUTOMATOR,
        "xpath": AppiumBy.XPATH
    }
    if locator_dict["type"] == "text":
        locator = f'new UiSelector().text("{locator_dict["value"]}")'
    else:
        locator = locator_dict["value"]

    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by_type[locator_dict["type"]], locator))
    )
    element.click()
    logger.info(f"✅ Clicked: {locator_dict['value'][:50]}...")
    return element

def wait_and_send_keys(driver, locator_dict, text, timeout=12):
    """Clear field then type (human-like)"""
    by_type = {"resource-id": AppiumBy.ID, "text": AppiumBy.ANDROID_UIAUTOMATOR, "xpath": AppiumBy.XPATH}
    if locator_dict["type"] == "text":
        locator = f'new UiSelector().textContains("{locator_dict["value"]}")'
    else:
        locator = locator_dict["value"]

    field = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by_type[locator_dict["type"]], locator))
    )
    field.clear()
    human_delay(load_config(), "min_sec")  # tiny pause before typing
    field.send_keys(text)
    logger.info(f"✅ Typed into field: {text[:30]}...")

def tap_outside_popup(driver, cfg):
    """Fast, language-independent popup dismiss"""
    x = cfg["safe_popup_dismiss_tap"]["x"]
    y = cfg["safe_popup_dismiss_tap"]["y"]
    driver.execute_script("mobile: tap", {"x": x, "y": y})
    logger.info(f"✅ Tapped outside popup at ({x}, {y})")
    human_delay(cfg)

def swipe_picker(driver, element_id: str, swipe_count: int, direction="up", distance=400):
    """Fast wheel picker swipe (casino-machine style)"""
    cfg = load_config()
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((AppiumBy.ID, element_id))
    )
    size = element.size
    start_x = size["width"] // 2
    start_y = size["height"] // 2
    end_y = start_y + distance if direction == "down" else start_y - distance

    for _ in range(swipe_count):
        driver.swipe(start_x, start_y, start_x, end_y, 80)  # very fast swipe
        human_delay(cfg, "min_sec", "max_sec")  # tiny realistic pause
    logger.info(f"✅ Swiped {swipe_count}x {direction} on picker {element_id}")

def read_accounts(cfg):
    """Read accounts.txt → list of (email, password)"""
    path = cfg["files"]["accounts"]
    accounts = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    for i in range(0, len(lines), 2):
        if i+1 < len(lines):
            accounts.append((lines[i], lines[i+1]))
    return accounts

def read_bios(cfg):
    """Read bios.txt and return cycling iterator"""
    path = cfg["files"]["bios"]
    with open(path, "r", encoding="utf-8") as f:
        bios = [line.strip() for line in f if line.strip()]
    def bio_cycle():
        i = 0
        while True:
            yield bios[i % len(bios)]
            i += 1
    return bio_cycle()

def close_app(driver, cfg):
    """Close TikTok Lite cleanly"""
    package = cfg["app"]["package"]
    driver.terminate_app(package)
    logger.info("✅ App closed")
    human_delay(cfg, "after_action_min", "after_action_max")
