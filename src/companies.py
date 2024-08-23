from selenium_driverless import webdriver
from selenium_driverless.types.by import By
import asyncio
import json
import csv

companies = []

async def main():
    options = webdriver.ChromeOptions()
    driver = await webdriver.Chrome(options=options)

    await driver.get('https://www.inc.com/inc5000/2024', wait_load=True)
    await driver.sleep(10)

    for rank in range(1, 5001):
            print(rank)
            try:
                rank_elem = await driver.find_element(By.CSS_SELECTOR, f'div[data-rankid="{rank}"]')
            except:
                print('Not found element, scrolling...')
                list_elem = await driver.find_element(By.CLASS_NAME, 'List')
                await driver.execute_script("arguments[0].scrollTop += 500;", list_elem)
                await driver.sleep(1)
                rank_elem = await driver.find_element(By.CSS_SELECTOR, f'div[data-rankid="{rank}"]')

            company = {
                'URL FOR CHECKING': await (await driver.find_element(By.CSS_SELECTOR, f'#rank-{rank} a')).get_attribute('href'),
                'Company': await (await driver.find_element(By.CSS_SELECTOR, f'#rank-{rank} div.company')).get_attribute('textContent'),
                'Descriptions': await (await driver.find_element(By.CSS_SELECTOR, f'#rank-{rank} div.description')).get_attribute('textContent'),
                '3 Yrs Growth': await (await driver.find_element(By.CSS_SELECTOR, f'#rank-{rank} div.growth')).get_attribute('textContent'),
                'Industry': await (await driver.find_element(By.CSS_SELECTOR, f'#rank-{rank} div.industry')).get_attribute('textContent'),
                'State': await (await driver.find_element(By.CSS_SELECTOR, f'#rank-{rank} div.state')).get_attribute('textContent'),
                'City': await (await driver.find_element(By.CSS_SELECTOR, f'#rank-{rank} div.city')).get_attribute('textContent'),
                'Year Founded': '',
                'Website': '',
            }
            
            print(company)
            companies.append(company)
            

    with open('arquivo.json', 'w', encoding='utf-8') as arquivo_json:
        json.dump(companies, arquivo_json, indent=4)

    with open('arquivo.csv', 'w', newline='') as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=list(companies[0].keys()))
        writer.writeheader()
        writer.writerows(companies)



asyncio.run(main())
