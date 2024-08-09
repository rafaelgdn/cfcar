from selenium_driverless import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import quote
import asyncio
import csv
import hrequests

headers = {}
cookies = []
cars = []


def import_csv_to_list():
    with open("src/VINs.csv", "r") as file:
        reader = csv.reader(file)
        data = [row[0] for row in reader]
    return data


async def start_driver():
    options = webdriver.ChromeOptions()
    driver = await webdriver.Chrome(options=options)
    return driver


async def bypass_captcha(driver):
    await driver.get("https://www.carjam.co.nz/car/?plate=EAA1%7C0", wait_load=True)
    await asyncio.sleep(0.5)

    pointer = driver.current_pointer
    await pointer.move_to(500, 200, smooth_soft=60, total_time=0.5)
    await pointer.move_to(20, 50, smooth_soft=60, total_time=0.5)
    await pointer.move_to(8, 45, smooth_soft=60, total_time=0.5)
    await pointer.move_to(500, 200, smooth_soft=60, total_time=0.5)
    await pointer.move_to(166, 206, smooth_soft=60, total_time=0.5)
    await pointer.move_to(200, 205, smooth_soft=60, total_time=0.5)

    shadow_root = await driver.execute_script("""
        return document.querySelector("#qquD4");
    """)

    location = await shadow_root.location
    size = await shadow_root.size

    x_offset = location["x"] + size["width"] / 16
    y_offset = location["y"] + size["height"] / 2

    await pointer.move_to(x_offset, y_offset, smooth_soft=60, total_time=0.5)
    await pointer.click()

    has_captcha = True

    while has_captcha:
        await asyncio.sleep(2)
        has_captcha = await driver.find_elements(By.ID, "cf-please-wait")

        if has_captcha:
            await pointer.move_to(500, 200, smooth_soft=60, total_time=0.5)
            await pointer.move_to(20, 50, smooth_soft=60, total_time=0.5)
            await pointer.move_to(8, 45, smooth_soft=60, total_time=0.5)
            await pointer.move_to(500, 200, smooth_soft=60, total_time=0.5)
            await pointer.move_to(166, 206, smooth_soft=60, total_time=0.5)
            await pointer.move_to(200, 205, smooth_soft=60, total_time=0.5)
            await pointer.move_to(x_offset, y_offset, smooth_soft=60, total_time=0.5)
            await asyncio.sleep(0.5)
            await pointer.click()

    await driver.get("https://www.carjam.co.nz/car/?plate=EAA2%7C0")


async def intercept_request(event, driver):
    global headers, cookies
    if "plate=EAA2%7C0" in event["request"]["url"]:
        headers = event["request"].get("headers", {})
        cookies = await driver.get_cookies()
    await driver.execute_cdp_cmd(
        "Network.continueInterceptedRequest",
        {"requestId": event["requestId"], "interceptionId": event["interceptionId"]},
    )


async def create_request_interception(driver):
    await driver.execute_cdp_cmd("Network.enable", {})
    await driver.execute_cdp_cmd(
        "Network.setRequestInterception",
        {"patterns": [{"urlPattern": "https://www.carjam.co.nz/car/?plate=EAA2%7C0"}]},
    )
    await driver.add_cdp_listener("Network.requestIntercepted", lambda event: intercept_request(event, driver))


def get_cookies_and_headers():
    filtered_cookies = [cookie for cookie in cookies if cookie["domain"] == ".carjam.co.nz"]
    return headers, filtered_cookies


def get_car_infos(text, url):
    soup = BeautifulSoup(text, "html.parser")
    return {
        "url": url,
        "year": soup.css.select('span[data-key="year_of_manufacture"]')[0].next_sibling.next_sibling.text,
        "make": soup.css.select('span[data-key="make"]')[0].next_sibling.next_sibling.text,
    }


async def handle_captcha_reload(url, encoded_vin, driver):
    await bypass_captcha(driver)
    await handle_page_request(url, encoded_vin, driver)


def renew_proxy():
    pass


async def handle_page_request(url, encoded_vin, driver):
    requestHeaders, requestCookies = get_cookies_and_headers()
    text = hrequests.get(url, cookies=requestCookies, headers=requestHeaders).text
    retries = 0

    if "has been blocked" in text:
        await renew_proxy()

    while 'data-key="year_of_manufacture"' not in text and retries < 10:
        if retries > 2:
            captcha_reloaded = await driver.find_elements(By.ID, "cf-please-wait")

            if captcha_reloaded:
                print("Captcha reloaded")
                await handle_captcha_reload(url, encoded_vin, driver)
                return

        print("Retrying...")
        retries += 1
        await driver.sleep(0.5)

        if retries > 1:
            await driver.sleep(1)
        if retries > 2:
            await driver.sleep(2)
        if retries > 3:
            await renew_proxy()

        text = hrequests.get(
            f"https://www.carjam.co.nz/car/?plate={encoded_vin}", cookies=requestCookies, headers=requestHeaders
        ).text

    car = get_car_infos(text, url)
    print(car)
    cars.append(car)


async def main():
    driver = await start_driver()
    await create_request_interception(driver)
    await bypass_captcha(driver)

    for vin in import_csv_to_list()[4:]:
        encoded_vin = quote(vin, safe="")
        url = f"https://www.carjam.co.nz/car/?plate={encoded_vin}"
        await handle_page_request(url, encoded_vin, driver)


asyncio.run(main())
