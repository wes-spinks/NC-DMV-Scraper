from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
import time
import random
import requests
import os

# --- Configuration ---

YOUR_DISCORD_WEBHOOK_URL = os.getenv("YOUR_DISCORD_WEBHOOK_URL", "YOUR_WEBHOOK_URL_HERE") # !!! REPLACE WITH YOUR ACTUAL WEBHOOK URL !!!
GECKODRIVER_PATH = os.getenv('GECKODRIVER_PATH','YOUR_GECKODRIVER_PATH_HERE') # Replace with your geckodriver path

if GECKODRIVER_PATH == 'YOUR_GECKODRIVER_PATH_HERE':
    print("Please set your geckodriver path in scrapedmv.py. If you do not know how, please look at the readme.")
    exit()

BASE_INTERVAL_MINUTES = 5
MIN_RANDOM_DELAY_SECONDS = 10
MAX_RANDOM_DELAY_SECONDS = 30
NCDOT_APPOINTMENT_URL = "https://skiptheline.ncdot.gov"
# Discord message limits
MAX_DISCORD_MESSAGE_LENGTH = 1950 # Slightly less than 2000 for safety margin

# --- End Configuration ---

class options_loaded_in_select(object):
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            select_element = driver.find_element(*self.locator)
            if not select_element.is_enabled():
                return False
            options = select_element.find_elements(By.TAG_NAME, "option")
            if len(options) > 1 and options[1].get_attribute("data-datetime"):
                return True
            return False
        except NoSuchElementException:
            return False

def send_discord_notification(webhook_url, message_content):
    if not webhook_url or webhook_url == "YOUR_WEBHOOK_URL_HERE":
        print("Discord webhook URL not configured. Skipping notification.")
        return

    intro_message = f"@everyone Appointments available at {NCDOT_APPOINTMENT_URL}:\n"
    full_message = intro_message + message_content

    message_chunks = []
    remaining_message = full_message

    while len(remaining_message) > 0:
        if len(remaining_message) <= MAX_DISCORD_MESSAGE_LENGTH:
            message_chunks.append(remaining_message)
            remaining_message = ""
        else:
            # Find the last newline character before the limit
            split_index = remaining_message.rfind('\n', 0, MAX_DISCORD_MESSAGE_LENGTH)
            if split_index == -1:
                # No newline found, force split at the max length
                split_index = MAX_DISCORD_MESSAGE_LENGTH

            message_chunks.append(remaining_message[:split_index])
            remaining_message = remaining_message[split_index:].lstrip()

            if split_index == MAX_DISCORD_MESSAGE_LENGTH and len(remaining_message) > 0:
                 message_chunks[-1] += "\n... (split)" # forced split in middle of line


    print(f"Sending notification in {len(message_chunks)} chunk(s)...")
    success = True
    for i, chunk in enumerate(message_chunks):
        payload = {"content": chunk}
        try:
            response = requests.post(webhook_url, json=payload, timeout=15)
            response.raise_for_status()
            print(f"Discord notification chunk {i+1}/{len(message_chunks)} sent successfully.")
            if i < len(message_chunks) - 1:
                time.sleep(1) # avoid ratelimit
        except requests.exceptions.RequestException as e:
            print(f"Error sending Discord notification chunk {i+1}: {e}")
            success = False
            break
        except Exception as e:
            print(f"An unexpected error occurred during Discord notification chunk {i+1}: {e}")
            success = False
            break

    if success:
        print("All Discord notification chunks sent.")
    else:
        print("Failed to send all Discord notification chunks.")


def format_results_for_discord(raw_results):
    """Formats the valid results into a string for Discord."""
    message_lines = []
    found_valid_times = False
    for location, result in raw_results.items():
        if isinstance(result, list) and result:
            message_lines.append(f"\n**Location: {location}**")
            for dt_str in result:
                message_lines.append(f"- {dt_str}")
            found_valid_times = True

    if not found_valid_times:
        return None

    return "\n".join(message_lines)


def extract_times_for_all_locations_firefox(url, driver_path):
    driver = None
    raw_location_results = {}
    try:
        firefox_options = Options()
        firefox_options.set_preference("geo.enabled", False)
        firefox_options.add_argument("--headless")
        service = FirefoxService(executable_path=driver_path)
        driver = webdriver.Firefox(service=service, options=firefox_options)
        driver.implicitly_wait(5)

        driver.get(url)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Navigated to:", url)

        time.sleep(40)
        make_appointment_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "cmdMakeAppt"))
        )
        print("Found 'Make an Appointment' button.")
        make_appointment_button.click()
        print("Clicked 'Make an Appointment' button.")
        time.sleep(20)

        # first_layer_button_xpath = "//div[contains(@class, 'QflowObjectItem') and contains(@class, 'form-control') and contains(@class, 'ui-selectable') and contains(@class, 'valid') and .//div[contains(text(), 'Driver License - First Time')]]"
        first_layer_button_xpath = "//div[contains(@class, 'QflowObjectItem') and .//div[contains(text(), 'Driver License - First Time')]]"
        first_layer_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, first_layer_button_xpath))
        )
        print("Found 'Driver License - First Time' button (First Layer).")
        first_layer_button.click()
        print("Clicked 'Driver License - First Time' button (First Layer).")

        time.sleep(20)
        wait = WebDriverWait(driver, 15)
        second_layer_button_selector = "div.QflowObjectItem.form-control.ui-selectable.valid:not(.disabled-unit):not(:has(> div.hover-div))"
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, second_layer_button_selector)))
        print("Second layer location buttons are now present (using refined selector).")

        for index in range(100):
            try:
                location_button_elements = driver.find_elements(By.CSS_SELECTOR, second_layer_button_selector)
                active_location_buttons_list = [button for button in location_button_elements if button.is_displayed() and button.is_enabled()]

                if index >= len(active_location_buttons_list):
                    print(f"Index {index} is out of range (list size: {len(active_location_buttons_list)}). Finished processing locations for this run.")
                    break

                current_button = active_location_buttons_list[index]
                button_lines = current_button.text.splitlines()
                location_name = button_lines[0].strip() if button_lines else f"Unknown Location {index}"

                print(f"\n--- Processing location: {location_name} (Index: {index}) ---")
                print("Clicking location button:", location_name)
                current_button.click()
                time.sleep(20)

                time_slot_container_selector = "div.step-control-content.AppointmentTime.TimeSlotModel.TimeSlotDataControl"
                time_slot_container = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, time_slot_container_selector))
                )

                time_select_id = "6f1a7b21-2558-41bb-8e4d-2cba7a8b1608"
                time_select_locator = (By.ID, time_select_id)

                options_loaded = False
                skip_extraction = False
                try:
                    select_present_wait = WebDriverWait(driver, 5)
                    time_select_element = select_present_wait.until(EC.presence_of_element_located(time_select_locator))

                    if not time_select_element.is_enabled():
                        print("Time select dropdown is DISABLED.")
                        raw_location_results[location_name] = "Dropdown Disabled"
                        skip_extraction = True
                    else:
                        options_loaded_wait = WebDriverWait(driver, 15)
                        try:
                            time.sleep(20)
                            options_loaded_wait.until(options_loaded_in_select(time_select_locator))
                            print("Confirmed: Options loaded.")
                            options_loaded = True
                        except TimeoutException:
                            print("Timeout: Options did not load or remained as placeholder only.")

                except TimeoutException:
                    print("Timeout: Could not find the select dropdown element.")
                    raw_location_results[location_name] = "Select Element Not Found"
                    skip_extraction = True

                if not skip_extraction:
                    valid_appointment_datetimes = []
                    options_processed_count = 0
                    try:
                        time_select_element = driver.find_element(*time_select_locator)
                        time_options = time_select_element.find_elements(By.TAG_NAME, "option")

                        try:
                            for option_index, option in enumerate(time_options[1:]):
                                datetime_str = option.get_attribute("data-datetime")
                                if datetime_str:
                                    valid_appointment_datetimes.append(datetime_str)
                                    options_processed_count += 1
                        except StaleElementReferenceException:
                            print(f"StaleElementReferenceException occurred while iterating options after processing {options_processed_count}. Storing partial results.")

                        if valid_appointment_datetimes:
                            print(f"Successfully extracted {len(valid_appointment_datetimes)} valid date/times.")
                            raw_location_results[location_name] = valid_appointment_datetimes
                        else:
                            if options_loaded:
                                print("No valid appointment times extracted (options existed but lacked data-datetime).")
                            else:
                                print("No appointment times found (options did not load).")
                            raw_location_results[location_name] = []

                    except NoSuchElementException:
                         print("Error: Select element disappeared before time extraction.")
                         raw_location_results[location_name] = "Select Element Disappeared"

                driver.back()
                time.sleep(0.5)
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, second_layer_button_selector)))


            except StaleElementReferenceException:
                print(f"StaleElementReferenceException caught in main loop for index {index}. Retrying...")
                try:
                    current_url_check = driver.current_url
                    if NCDOT_APPOINTMENT_URL not in current_url_check:
                         driver.back()
                         WebDriverWait(driver, 5).until(lambda d: d.current_url != current_url_check)
                except: pass # Ignore errors during back navigation in retry
                time.sleep(1)
                continue
            except Exception as location_e:
                print(f"Error processing location index {index} ({location_name}): {location_e}")
                raw_location_results[location_name] = "Error processing location"
                try:
                    current_url = driver.current_url
                    driver.back()
                    time.sleep(1)
                    WebDriverWait(driver, 5).until(lambda d: d.current_url != current_url)
                    print("Navigated back after error.")
                    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, second_layer_button_selector)))
                except:
                    print("Error navigating back after location processing error. Stopping run.")
                    break


    except Exception as e:
        print(f"An error occurred during WebDriver execution: {e}")
    finally:
        if driver:
            driver.quit()
            print("WebDriver closed.")

    return raw_location_results


if __name__ == '__main__':

    if YOUR_DISCORD_WEBHOOK_URL == "YOUR_WEBHOOK_URL_HERE":
        print("!!! WARNING: DISCORD WEBHOOK URL IS NOT SET. Notifications will be skipped. !!!")
        print("!!! Edit the YOUR_DISCORD_WEBHOOK_URL variable in the script. !!!")

    while True:
        print(f"\n--- Starting run at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")

        results = extract_times_for_all_locations_firefox(NCDOT_APPOINTMENT_URL, GECKODRIVER_PATH)
        print(results)

        discord_message_content = format_results_for_discord(results)
        if discord_message_content:
            print("Valid appointment times found. Sending notification...")
            send_discord_notification(YOUR_DISCORD_WEBHOOK_URL, discord_message_content)
        else:
            print("No valid appointment times found in this run.")

        base_sleep = BASE_INTERVAL_MINUTES * 60
        random_delay = random.randint(MIN_RANDOM_DELAY_SECONDS, MAX_RANDOM_DELAY_SECONDS)
        total_sleep = base_sleep + random_delay

        print(f"--- Run finished. Sleeping for {total_sleep // 60} minutes and {total_sleep % 60} seconds ---")
        try:
            time.sleep(total_sleep)
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Exiting script.")
            break
