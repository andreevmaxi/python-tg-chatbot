import time

import markdownify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import logging


class CultureDeckScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless=new")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")

        # Для работы в Docker
        self.options.add_argument("--remote-debugging-port=9222")
        self.options.binary_location = "/usr/bin/google-chrome"

    def get_driver(self):
        service = Service(executable_path=ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=self.options)

    def click_culture_expand(self, driver):
        try:
            culture_button_locator = (By.XPATH, "//div[text()='Culture']/following-sibling::div//span[@role='button']")
            menu_locator = (By.XPATH, "//div[@role='menu']")

            # Ожидаем, пока кнопка "Culture" станет кликабельной
            culture_button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable(culture_button_locator))
            print("Кнопка найдена")

            # Получаем текущее состояние кнопки (каждый раз обновляем элемент)
            def get_culture_button():
                return driver.find_element(*culture_button_locator)

            initial_state = get_culture_button().get_attribute("aria-expanded")
            print("Нынешний стейт кнопки:", initial_state)

            if initial_state == "false":
                # Используем ActionChains для надежного клика
                actions = ActionChains(driver)
                actions.move_to_element(get_culture_button()).click().perform()
                print("Кнопка нажата")

                # Ждём обновления страницы
                WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
                print("Страница полностью загрузилась после нажатия!")

                # Ожидаем, пока кнопка снова появится в DOM (устраняем stale element reference)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located(culture_button_locator))

                # Ждем, пока меню действительно появится
                WebDriverWait(driver, 15).until(EC.presence_of_element_located(menu_locator))
                print("Меню успешно появилось!")

            else:
                print("Меню уже открыто")

            return True

        except Exception as e:
            print(f"Ошибка при работе с меню: {str(e)}")
            return False

    def get_links(self, driver):
        # Ожидаем загрузки меню
        menu = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[role='menu']")
            )
        )

        # Находим все элементы меню
        menu_items = menu.find_elements(By.CSS_SELECTOR, "span[role='menuitem']")

        # Ищем индекс "Cut Cancer"
        cut_cancer_index = -1
        for i, item in enumerate(menu_items):
            if "Cut Cancer" in item.text:
                cut_cancer_index = i
                break

        if cut_cancer_index == -1:
            raise ValueError("Cut Cancer section not found")

        # Собираем ссылки
        links = []

        # Добавляем ссылку "Cut Cancer"
        cut_cancer_item = menu_items[cut_cancer_index]
        if link := self._extract_link(cut_cancer_item):
            links.append(link)

        # Ссылки до Cut Cancer
        for item in menu_items[:cut_cancer_index]:
            if link := self._extract_link(item):
                links.append(link)

        # Ссылки после Cut Cancer
        for item in menu_items[cut_cancer_index + 1:]:
            if link := self._extract_link(item):
                links.append(link)

        return links

    def _extract_link(self, element) -> dict:
        try:
            link_element = element.find_element(By.TAG_NAME, "a")
            return {
                'text': link_element.text.strip(),
                'url': link_element.get_attribute('href')
            }
        except:
            return None

    def _get_main_content(self, driver):
        try:
            content = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[id='content-container']")
                )
            )
            return markdownify.markdownify(content.get_attribute('innerHTML'))
        except TimeoutException:
            return "Content not available"


    def scrape_page_content(self, url: str) -> str:
        driver = self.get_driver()
        try:
            driver.get(url)
            WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
            return self._get_main_content(driver)
        except:
            return "Content not available"
        finally:
            driver.quit()

    def get_content(self, url: str) -> dict:
        driver = self.get_driver()
        try:
            driver.get(url)
            final_button_locator = (By.XPATH, "//span[text()='Copy doc']")  # кнопка после перезагрузки страницы

            # Ждём загрузки первой страницы
            WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
            print("Первая версия страницы загрузилась!")

            # Ждём появления финальной версии страницы
            try:
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located(final_button_locator))
                print("Финальная страница загружена (появилась новая кнопка)!")
            except:
                print("Финальная кнопка не появилась, возможно, страница не перезагружается.")

            if self.click_culture_expand(driver):
                print("Меню Culture успешно открыто!")
            else:
                print("Не удалось открыть меню Culture")

            menu_links = self.get_links(driver)

            additional_contents = {}
            for link in menu_links:
                additional_contents[link['text']] = self.scrape_page_content(link['url'])

            return {
                'main_content': self._get_main_content(driver),
                'additional_contents': additional_contents,
                'link': url
            }

        except Exception as e:
            logging.error(f"Ошибка при получении данных: {e}")
            return {'main_content': '', 'additional_contents': {}, 'link': url}

        finally:
            driver.quit()