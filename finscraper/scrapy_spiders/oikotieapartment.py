"""Module for OikotieApartment spider."""


import time

from scrapy import Item, Field, Request
from scrapy.crawler import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Identity, Compose

from finscraper.request import SeleniumCallbackRequest
from finscraper.text_utils import strip_join, drop_empty_elements, \
    paragraph_join


class _OikotieApartmentSpider(Spider):
    name = 'oikotieapartment'
    start_urls = ['https://asunnot.oikotie.fi/myytavat-asunnot']
    follow_link_extractor = LinkExtractor(
        allow_domains=('asunnot.oikotie.fi'),
        allow=(r'.*\/myytavat-asunnot\/.*'),
        deny=(r'.*?origin\=.*'),
        deny_domains=(),
        canonicalize=True
    )
    item_link_extractor = LinkExtractor(
        allow_domains=('asunnot.oikotie.fi'),
        allow=(rf'.*/myytavat-asunnot/.*/[0-9]+'),
        deny=(r'.*?origin\=.*'),
        deny_domains=(),
        canonicalize=True
    )
    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # No robots.txt, will fail with yes
        'DOWNLOADER_MIDDLEWARES': {
            'finscraper.middlewares.SeleniumCallbackMiddleware': 800
        }
    }
    itemcount = 0
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

    def __init__(self, *args, **kwargs):
        """Fetch oikotie.fi apartments.

        Args:
        """
        kwargs['follow_request_type'] = SeleniumCallbackRequest
        super(_OikotieApartmentSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumCallbackRequest(
                url, selenium_callback=self._handle_start)

    @staticmethod
    def _handle_start(request, spider, driver):
        driver.get(request.url)
        policy_modal = driver.find_element_by_xpath(
            '//div[contains(@class, "sccm-button-green")]')
        if policy_modal:
            policy_modal.click()
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

        if to_parse:
            yield self._parse_item(resp)
            self.itemcount += 1

        # Parse items and further on extract links from those pages
        item_links = self.item_link_extractor.extract_links(resp)
        for link in item_links:
            yield Request(link.url, callback=self.parse, priority=20,
                          cb_kwargs={'to_parse': True})

        # Extract all links from this page
        follow_links = self.follow_link_extractor.extract_links(resp)
        for link in follow_links:
            yield SeleniumCallbackRequest(
                link.url, callback=self.parse, priority=10)

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
                      in _OikotieApartmentSpider.title2field.items()))
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
