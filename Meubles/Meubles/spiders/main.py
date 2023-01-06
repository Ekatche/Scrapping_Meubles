import scrapy
from scrapy.utils.project import get_project_settings
from scrapy import Request, Selector
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
import time


class Meubles(scrapy.Spider):
    name = 'meubles'
    start_urls = ['https://www.meubles.fr/']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
    }

    def start_requests(self):
        settings = get_project_settings()
        driver_path = settings.get('CHROME_DRIVER_PATH')
        options = ChromeOptions()
        options.headless = True
        driver = Chrome(executable_path=driver_path,
                        options=options)
        driver.get('https://www.meubles.fr/')
        driver.implicitly_wait(10)

        driver.find_element(By.CSS_SELECTOR, 'button.uc-col-span-full.uc-button.uc-button--primary').click()

        cat_links = driver.find_elements(By.CSS_SELECTOR, '.sc-ce694f1a-0.sc-f2a0811e-1.dAgXHA.gNHxTj a')
        for link in cat_links:
            categorie_url = link.get_attribute('href')

            yield Request(categorie_url, headers=self.headers, callback=self.parseSubcategories)
        driver.quit()

    def parseSubcategories(self, response):
        cssel2 = '.sc-d6da2685-0.kBSEaz'
        subcats  = response.css(cssel2)
        for data in subcats :
            subcat_url  = data.css('::attr(href)').get()
            print(subcat_url)
            subcat_name = subcat_url.split('/')[2]
            cat_name = subcat_url.split('/')[1]
            full_url = f'https://www.meubles.fr{subcat_url}'
            dict = {
                'categorie_name' : cat_name,
                'sub_categorie' : subcat_name,
            }
            yield Request(full_url, headers=self.headers, meta=dict, callback=self.parseCategories)


    def parseCategories(self, response):
        url = response.url
        settings = get_project_settings()
        driver_path = settings.get('CHROME_DRIVER_PATH')
        options = ChromeOptions()
        options.headless = True
        driver = Chrome(executable_path=driver_path,
                        options=options
                        )
        driver.get(url)
        driver.implicitly_wait(5)
        driver.find_element(By.CSS_SELECTOR, 'button.uc-col-span-full.uc-button.uc-button--primary').click()

        driver.implicitly_wait(5)

        while True:
            try:
                button = driver.find_element(
                    By.CSS_SELECTOR,
                    '.sc-9687a6e6-0.sc-e8191ef3-0.dAcuIE.wVWJj.sc-caf46107-6.fEFKHT'
                )
                time.sleep(5)

                cssSel = '.sc-ce694f1a-0.CHQKI [data-testid^="product-tile"]'

                links_element = driver.find_elements(By.CSS_SELECTOR, cssSel)

                for link in links_element:
                    product_url = link.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    product_name = link.get_attribute('title')
                    category = response.meta['categorie_name']
                    sub_category = response.meta['sub_categorie']
                    product_img = link.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                    data = dict(categorie=category, productName=product_name,
                                image=product_img, sous_categorie=sub_category)
                    yield Request(product_url, headers=self.headers, meta=data, callback=self.parseProduct)

                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(4)
                button.click()

            except Exception as e:
                print(e)
                driver.quit()
                break

    def parseProduct(self, response):
        partenaire_url = response.url
        print(partenaire_url)
        partenaire = partenaire_url.split('/')[2]
        dict = {
            'Categorie': response.meta['categorie'],
            'Sous_Categorie': response.meta['sous_categorie'],
            'Product_Name': response.meta['productName'],
            'Image': response.meta['image'],
            'Partenaire': partenaire,

        }
        yield dict
