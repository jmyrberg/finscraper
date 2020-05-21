"""Module for testing spiders."""


import time

import pytest
pytestmark = [pytest.mark.spider]

from finscraper.spiders import ILArticle, ISArticle, YLEArticle, VauvaPage, \
    OikotieApartment

from tests.utils import calc_field_emptiness


# Spiders can be added here, and basic tests will be set up automatically
spiders = [
    {
        'class': ILArticle,
        'params': [None],
        'n_fields': 8,
        'mark': pytest.mark.ilarticle
    },
    {
        'class': ISArticle,
        'params': [None],
        'n_fields': 8,
        'mark': pytest.mark.isarticle
    },
    {
        'class': YLEArticle,
        'params': [None],
        'n_fields': 8,
        'mark': pytest.mark.ylearticle
    },
    {
        'class': VauvaPage,
        'params': [None],
        'n_fields': 8,
        'mark': pytest.mark.vauvapage
    },
    {
        'class': OikotieApartment,
        'params': [None],
        'n_fields': 80,
        'mark': pytest.mark.oikotieapartment
    }
]


scrape_cases = [pytest.param(s['class'], p, s['n_fields'], marks=s['mark'])
                for s in spiders for p in s['params']]

other_cases = [pytest.param(s['class'], p, marks=s['mark'])
               for s in spiders for p in s['params']]         


@pytest.fixture(scope='function')
def spider_params(request):
    return request.param or {}


@pytest.mark.parametrize('spider_cls, spider_params, n_fields', scrape_cases,
                         indirect=['spider_params'])
def test_scraping(spider_cls, spider_params, n_fields, capsys, n_items=10):
    # Scraping
    spider = spider_cls(**spider_params).scrape(n_items)
    df = spider.get()
    assert len(df) >= n_items
    assert len(df.columns) == n_fields

    # Continue scraping
    df2 = spider.scrape(1).get()
    assert len(df2) > len(df)

    # Field emptiness
    emptiness = calc_field_emptiness(df2)
    with capsys.disabled():
        print(f'\n{emptiness.to_string(index=False)}\n')
    assert not (emptiness['empty_pct'] == 100).all()


@pytest.mark.parametrize('spider_cls, spider_params', other_cases,
                         indirect=['spider_params'])
def test_functionality(spider_cls, spider_params):
    # Save and load
    spider = spider_cls(**spider_params).scrape(1)
    df = spider.get()
    jobdir = spider.save()
    del spider
    spider = spider_cls.load(jobdir)
    df2 = spider.scrape(1).get()
    assert len(df2) > len(df)


@pytest.mark.parametrize('spider_cls, spider_params', other_cases,
                         indirect=['spider_params'])
@pytest.mark.xfail(reason='Benchmark')
def test_benchmark_scrape_1_min(spider_cls, spider_params, capsys):
    df = spider_cls(**spider_params).scrape(0, 60).get()
    assert len(df) >= 60
    with capsys.disabled():
        print(f'-- {len(df)} items')


@pytest.mark.parametrize('spider_cls, spider_params', other_cases,
                         indirect=['spider_params'])
@pytest.mark.xfail(reason='Benchmark')
def test_benchmark_scrape_100_items(spider_cls, spider_params, capsys):
    start = time.perf_counter()
    df = spider_cls(**spider_params).scrape(100).get()
    elapsed_time = int(time.perf_counter() - start)
    assert len(df) >= 100
    with capsys.disabled():
        print(f'-- {elapsed_time} seconds ({len(df)} items)')
