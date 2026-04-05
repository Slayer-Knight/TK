# ================================================
# main.py
# ================================================

from actions import (
    load_config, force_clear_app_data, init_driver, human_delay,
    wait_and_click, wait_and_send_keys, tap_outside_popup,
    swipe_picker, read_accounts, read_bios, close_app
)
import logging
import random

logger = logging.getLogger(__name__)

def main():
    cfg = load_config()
    accounts = read_accounts(cfg)
    bio_gen = read_bios(cfg)
    pic_index = cfg["profile_pictures"]["start_index"]

    logger.info(f"🚀 Starting automation for {len(accounts)} accounts...")

    for idx, (email, password) in enumerate(accounts):
        logger.info(f"🔄 Processing account {idx+1}/{len(accounts)} → {email}")

        force_clear_app_data(cfg)
        driver = init_driver(cfg)
        human_delay(cfg, "after_action_min", "after_action_max")

        wait_and_click(driver, cfg["locators"]["use_phone_or_email"])
        tap_outside_popup(driver, cfg)
        wait_and_click(driver, cfg["locators"]["email_option"])
        human_delay(cfg)

        wait_and_send_keys(driver, cfg["locators"]["email_field"], email)

        try:
            wait_and_click(driver, cfg["locators"]["checkbox_get_updates"])
        except:
            pass

        wait_and_click(driver, cfg["locators"]["next_button"])
        human_delay(cfg, "after_action_min", "after_action_max")

        wait_and_send_keys(driver, cfg["locators"]["password_field"], password)
        wait_and_click(driver, cfg["locators"]["next_button"])
        human_delay(cfg, "after_action_min", "after_action_max")

        # ==================== DOB LOGIC (UPDATED) ====================
        logger.info("Setting random 18+ DOB → Year uses DOWNWARD swipes only...")

        # Day: random count + random direction
        day_count = random.randint(cfg["dob"]["day_swipes"]["min"], cfg["dob"]["day_swipes"]["max"])
        swipe_picker(driver, cfg["locators"]["dob_day_picker"]["value"], 
                     day_count, random.choice(["up", "down"]))

        # Month: random count + random direction
        month_count = random.randint(cfg["dob"]["month_swipes"]["min"], cfg["dob"]["month_swipes"]["max"])
        swipe_picker(driver, cfg["locators"]["dob_month_picker"]["value"], 
                     month_count, random.choice(["up", "down"]))

        # Year: random count + ONLY DOWNWARD swipes (as per your instruction)
        year_count = random.randint(cfg["dob"]["year_swipes"]["min"], cfg["dob"]["year_swipes"]["max"])
        swipe_picker(driver, cfg["locators"]["dob_year_picker"]["value"], 
                     year_count, "down")          # ← CHANGED TO "down"

        wait_and_click(driver, cfg["locators"]["next_button"])
        human_delay(cfg, "after_action_min", "after_action_max")
        # ==========================================================

        # Rest of the account creation flow (unchanged)
        username_part = email.split('@')[0]
        profile_name = ''.join(c for c in username_part if c.isalpha()).capitalize()
        wait_and_send_keys(driver, cfg["locators"]["profile_name_field"], profile_name)
        wait_and_click(driver, cfg["locators"]["create_button"])
        human_delay(cfg, "after_action_min", "after_action_max")

        wait_and_click(driver, cfg["locators"]["profile_icon"])
        human_delay(cfg)
        wait_and_click(driver, cfg["locators"]["select_from_gallery"])

        gallery_locator = {"type": "xpath", "value": cfg["locators"]["gallery_images_container"]["value"]}
        images = driver.find_elements(AppiumBy.XPATH, gallery_locator["value"])
        if images and pic_index < len(images):
            images[pic_index].click()
            pic_index += 1
            logger.info(f"✅ Selected profile picture index {pic_index-1}")
        else:
            logger.warning("⚠️ Not enough gallery images - using first available")
            if images:
                images[0].click()

        wait_and_click(driver, cfg["locators"]["save_picture_button"])
        human_delay(cfg, "after_action_min", "after_action_max")

        wait_and_send_keys(driver, cfg["locators"]["username_field_container"], email.split('@')[0].lower())
        wait_and_click(driver, cfg["locators"]["save_username_button"])
        human_delay(cfg)
        wait_and_click(driver, cfg["locators"]["set_username_dialog_button"])
        human_delay(cfg, "after_action_min", "after_action_max")

        wait_and_click(driver, cfg["locators"]["add_bio_button"])
        bio_text = next(bio_gen)
        wait_and_send_keys(driver, cfg["locators"]["bio_field"], bio_text)
        wait_and_click(driver, cfg["locators"]["save_bio_button"])
        human_delay(cfg, "after_action_min", "after_action_max")

        wait_and_click(driver, cfg["locators"]["home_tab"])
        wait_and_click(driver, cfg["locators"]["search_icon"])
        wait_and_send_keys(driver, cfg["locators"]["search_bar"], cfg["locators"]["target_user_to_search"])
        driver.press_keycode(66)  # Enter
        human_delay(cfg, "after_action_min", "after_action_max")

        target_user = cfg["locators"]["target_user_to_search"]

        user_locator = {
            "type": "xpath",
            "value": f"//android.view.ViewGroup[@content-desc='{target_user}']//android.view.ViewGroup[1]"
        }
        wait_and_click(driver, user_locator)

        wait_and_click(driver, cfg["locators"]["following_tab"])
        human_delay(cfg, "after_action_min", "after_action_max")

        for i in range(cfg["follow_settings"]["people_to_follow"]):
            try:
                follow_btns = driver.find_elements(AppiumBy.XPATH, f"//android.widget.TextView[@text='Follow']")
                if follow_btns:
                    follow_btns[0].click()
                    logger.info(f"✅ Followed user {i+1}")
                    human_delay(cfg, "follow_delay_min", "follow_delay_max")
            except:
                break

        close_app(driver, cfg)
        driver.quit()

        logger.info(f"✅ Account {idx+1} completed. Waiting before next loop...")
        human_delay(cfg, "after_action_min", "after_action_max")

    logger.info("🎉 ALL ACCOUNTS PROCESSED - Automation finished!")

if __name__ == "__main__":
    main()
