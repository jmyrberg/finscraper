"""Module for OikotieApartment spider."""


import logging
import time

from scrapy import Item, Field, Request
from scrapy.crawler import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, Identity, Compose

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from finscraper.request import SeleniumCallbackRequest
from finscraper.text_utils import strip_join, drop_empty_elements, \
    paragraph_join
from finscraper.utils import get_chromedriver


logger = logging.getLogger(__name__)


class _OikotieApartmentSpider(Spider):
    name = 'oikotieapartment'
    base_url = 'https://asunnot.oikotie.fi/myytavat-asunnot'
    item_link_extractor = LinkExtractor(
        allow_domains=('asunnot.oikotie.fi'),
        allow=(r'.*\/myytavat-asunnot\/.*\/[0-9]{3,}'),
        deny=(r'.*?origin\=.*'),
        deny_domains=(),
        canonicalize=True
    )
    custom_settings = {
        # Custom
        'DISABLE_HEADLESS': True,
        'MINIMIZE_WINDOW': True,
        # Scrapy
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.9,
        'CONCURRENT_REQUESTS': 4,
        'ROBOTSTXT_OBEY': False,
        'DOWNLOADER_MIDDLEWARES': {
            'finscraper.middlewares.SeleniumCallbackMiddleware': 800
        }
    }
    itemcount = 0
    listings_per_page = 24
    title2field = {
        # Perustiedot
        'Sijainti': 'location',
        'Kaupunki': 'city',
        'Kaupunginosa': 'district',
        'Kohdenumero': 'oikotie_id',
        'Kerros': 'floor',
        'Asuinpinta-ala': 'life_sq',
        'Tontin pinta-ala': 'property_sq',
        'Kokonaispinta-ala': 'total_sq',
        'Huoneiston kokoonpano': 'room_info',
        'Huoneita': 'number_of_rooms',
        'Kunto': 'condition',
        'Kunnon lisätiedot': 'condition_details',
        'Lisätietoa vapautumisesta': 'availability',
        'Keittiön varusteet': 'kitchen_appliances',
        'Kylpyhuoneen varusteet': 'bathroom_appliances',
        'Ikkunoiden suunta': 'window_direction',
        'Parveke': 'has_balcony',
        'Parvekkeen lisätiedot': 'balcony_details',
        'Säilytystilat': 'storage_space',
        'Näkymät': 'view',
        'Tulevat remontit': 'future_renovations',
        'Tehdyt remontit': 'completed_renovations',
        'Asunnossa sauna': 'has_sauna',
        'Saunan lisätiedot': 'sauna_details',
        'Asumistyyppi': 'housing_type',
        'Palvelut': 'services',
        'Lisätiedot': 'additional_info',
        'Kiinteistötunnus': 'property_id',
        'Kohde on': 'apartment_is',
        'Tietoliikennepalvelut': 'telecommunication_services',

        # Hintatiedot ja muut kustannukset
        'Velaton hinta': 'price_no_tax',
        'Myyntihinta': 'sales_price',
        'Lainaosuuden maksu': 'shared_loan_payment',
        'Neliöhinta': 'price_per_sq',
        'Velkaosuus': 'share_of_liabilities',
        'Kiinnitykset': 'mortgages',

        'Rahoitusvastike': 'financial_charge',
        'Hoitovastike': 'condominium_payment',
        'Yhtiövastike': 'maintenance_charge',
        'Vesimaksu': 'water_charge',
        'Vesimaksun lisätiedot': 'water_charge_details',
        'Lämmityskustannukset': 'heating_charge',
        'Muut kustannukset': 'other_costs',

        # Talon ja tontin tiedot
        'Uudiskohde': 'is_brand_new',
        'Taloyhtiön nimi': 'housing_company_name',
        'Rakennuksen tyyppi': 'building_type',
        'Rakennusvuosi': 'build_year',
        'Rakennusvuoden lisätiedot': 'build_year_details',
        'Huoneistojen lukumäärä': 'number_of_apartments',
        'Kerroksia': 'total_floors',
        'Hissi': 'building_has_elevator',
        'Taloyhtiössä on sauna': 'building_has_sauna',
        'Rakennusmateriaali': 'building_material',
        'Kattotyyppi': 'roof_type',
        'Energialuokka': 'energy_class',
        'Energiatoditus': 'has_energy_certificate',
        'Kiinteistön antennijärjestelmä': 'antenna_system',
        'Tontin koko': 'property_size',
        'Kiinteistönhoito': 'maintenance',
        'Isännöinti': 'real_estate_management',
        'Kaavatiedot': 'plan_info',
        'Kaavatilanne': 'plan',
        'Liikenneyhteydet': 'traffic_communication',
        'Lämmitys': 'heating',

        # Tilat ja materiaalit
        'Pysäköintitilan kuvaus': 'parking_space_description',
        'Yhteiset tilat': 'common_spaces',
        'Pintamateriaalit': 'wallcovering'
    }

    def __init__(self, *args, area=None, **kwargs):
        """Fetch oikotie.fi apartments.

        Args:
            area (str, optional): Scrape listings based on area, e.g.
                "helsinki" or "hausjärvi". The final URL will be formed as:
                'https://asunnot.oikotie.fi/myytavat-asunnot/{area}'. Defaults
                to None.
        """
        super(_OikotieApartmentSpider, self).__init__(*args, **kwargs)
        self.area = area

        self._last_page = None

    def start_requests(self):
        # Render start page with headed Chrome
        driver = get_chromedriver(settings=self.settings)

        area = '' if self.area is None else f'/{self.area}'
        base_url_with_area = f'{self.base_url}{area}'
        logger.info(f'Using "{base_url_with_area}" as start URL')

        driver.get(base_url_with_area)

        # Click yes on modal, if it exists (Selenium)
        self._handle_start_modal(driver)

        # Find the last page in pagination
        self._last_page = self._get_last_page(driver)

        driver.close()

        # Iterate pagination pages one-by-one and extract links + items
        for page in range(1, self._last_page + 1):
            url = f'{base_url_with_area}?pagination={page}'
            yield SeleniumCallbackRequest(
                url,
                priority=10,
                meta={'page': page},
                selenium_callback=self._handle_pagination_page)

    def _get_last_page(self, driver):
        logger.debug('Getting last page...')
        last_page_xpath = '//span[contains(@ng-bind, "ctrl.totalPages")]'
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, last_page_xpath)))
        last_page_element = driver.find_element(By.XPATH, last_page_xpath)
        last_page = int(last_page_element.text.split('/')[-1].strip())
        logger.debug(f'Last page found: {last_page}')
        return last_page

    def _handle_start_modal(self, driver):
        # Click modal, if it exists
        try:
            # Find iframe
            logger.debug('Waiting for iframe...')
            iframe_xpath = "//iframe[contains(@id, 'sp_message_iframe')]"
            iframe = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, iframe_xpath)))
            driver.switch_to.frame(iframe)
            logger.debug(f'Switched to iframe {iframe}')

            # Find button
            logger.debug('Finding button...')
            button_xpath = "//button[contains(., 'Hyväksy')]"
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, button_xpath)))
            modal = driver.find_element(By.XPATH, button_xpath)
            logger.debug('Clicking modal...')
            modal.click()
            logger.debug('Waiting for modal to disappear...')
            WebDriverWait(driver, 2).until(
                EC.invisibility_of_element_located((By.XPATH, button_xpath)))

            logger.debug('Switching to default frame')
            driver.switch_to.default_content()
            logger.debug('Modal handled successfully!')
        except TimeoutException:
            logger.warning('No modal found, assuming does not exist')

    def _handle_pagination_page(self, request, spider, driver):
        driver.get(request.url)

        logger.debug('Scrolling pagination page to bottom...')
        listings_xpath = '//div[contains(@class, "cards-v2__card")]'
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

        logger.debug('Waiting for listings to be available...')
        page = request.meta['page']
        n_listings = self.listings_per_page if page < self._last_page else 1
        WebDriverWait(driver, 10).until(
            lambda browser:
                len(browser.find_elements(By.XPATH, listings_xpath)) >=
                n_listings)
        logger.debug('Listings rendered, returning response')

        return HtmlResponse(
            driver.current_url,
            body=driver.page_source.encode('utf-8'),
            encoding='utf-8',
            request=request
        )

    def parse(self, resp, to_parse=False):
        """Parse items and follow links based on defined link extractors."""
        max_itemcount = self.settings.get('CLOSESPIDER_ITEMCOUNT', 0)
        if self.itemcount and self.itemcount == max_itemcount:
            raise CloseSpider

        if to_parse:  # Parse listing item
            yield self._parse_item(resp)
            self.itemcount += 1

        # Extract listing links and parse them
        item_links = self.item_link_extractor.extract_links(resp)
        for link in item_links:
            yield Request(link.url, callback=self.parse, priority=20,
                          cb_kwargs={'to_parse': True})

    def _parse_item(self, resp):
        il = ItemLoader(item=_OikotieApartmentItem(), response=resp)
        il.add_value('url', resp.url)
        il.add_value('time', int(time.time()))

        # Apartment info
        il.add_xpath('title', '//title//text()')
        il.add_xpath(
            'overview',
            '//div[contains(@class, "listing-overview")]//text()')

        # From tables
        table_xpath = '//dt[text()="{title}"]/following-sibling::dd[1]//text()'
        for title, field in self.title2field.items():
            il.add_xpath(field, table_xpath.format(title=title))

        # Contact information
        il.add_xpath(
            'contact_person_name',
            '//div[contains(@class, "listing-person__details-item--big")]'
            '//text()'
        )
        il.add_xpath(
            'contact_person_job_title',
            '//div[contains(@class, "listing-person__details-item--waisted")]'
            '//text()'
        )
        il.add_xpath(
            'contact_person_phone_number',
            '(//div[contains(@class, "listing-person__details-item'
            '--sm-top-margin")]/span)[2]//text()'
        )
        il.add_xpath(
            'contact_person_company',
            '//div[@class="listing-company__name"]/a/span//text()'
        )
        il.add_xpath('contact_person_email', '(//p)[1]//text()')
        return il.load_item()


class _OikotieApartmentItem(Item):
    __doc__ = """
    Returned fields:
        * url (str): URL of the scraped web page.
        * time (int): UNIX timestamp of the scraping.
        * title (str): Title of the web browser tab.
        * overview (str): Overview text of the apartment.
        * contact_person_name (str): Name of the contact person.
        * contact_person_job_title (str): Job title of the contact person.
        * contact_person_phone_number (str): Phone number of the contact \
            person.
        * contact_person_company (str): Company of the contact person.
        """.strip() + (
        '\n' +
        '\n'.join(f'{" " * 8}* {field} (str): {desc}'
                  for desc, field
                  in _OikotieApartmentSpider.title2field.items())
    )
    url = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    time = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    # Apartment info
    title = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    overview = Field(
        input_processor=Compose(drop_empty_elements, paragraph_join),
        output_processor=TakeFirst()
    )
    # Basic information
    location = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    city = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    house_number = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    district = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    oikotie_id = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    floor = Field(
        input_processor=lambda x: x[-1:],
        output_processor=TakeFirst()
    )
    total_floors = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    life_sq = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    property_sq = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    total_sq = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    room_info = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    number_of_rooms = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    condition = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    condition_details = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    availability = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    kitchen_appliances = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    bathroom_appliances = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    window_direction = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    has_balcony = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    balcony_details = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    storage_space = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    view = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    future_renovations = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    completed_renovations = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    has_sauna = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    sauna_details = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    housing_type = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    services = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    additional_info = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    property_id = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    apartment_is = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    telecommunication_services = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    # Price and cost information
    price_no_tax = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    sales_price = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    shared_loan_payment = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    price_per_sq = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    share_of_liabilities = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    mortgages = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    financial_charge = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    condominium_payment = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    maintenance_charge = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    water_charge = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    water_charge_details = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    heating_charge = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    heating_charge_details = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    other_costs = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    # House and property
    is_brand_new = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    housing_company_name = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    building_type = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    build_year = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    build_year_details = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    number_of_apartments = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    building_has_elevator = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    building_has_sauna = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    building_material = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    roof_type = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    energy_class = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    has_energy_certificate = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    antenna_system = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    property_size = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    property_size_unit = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    property_owner = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    maintenance = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    real_estate_management = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    plan_info = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    plan = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    traffic_communication = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    heating = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    # Spaces and material
    parking_space_description = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    common_spaces = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    wallcovering = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    # Contacts
    contact_person_name = Field(
        input_processor=strip_join,
        output_processor=TakeFirst()
    )
    contact_person_company = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    contact_person_job_title = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    contact_person_email = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
    contact_person_phone_number = Field(
        input_processor=Identity(),
        output_processor=TakeFirst()
    )
