import json
import re

import pandas as pd
import pytest

import app as app_module


def chart_data(response):
    match = re.search(r'<script type="application/json" id="chart-data">(.*?)</script>',
                      response.get_data(as_text=True), re.S)
    return json.loads(match.group(1)) if match else None


@pytest.fixture
def downloads(monkeypatch, make_download):
    """Replace the Yahoo Finance download; records the arguments it was called with."""
    calls = []

    def fake_fetch(tickers, time_frame, time_interval):
        calls.append((tickers, time_frame, time_interval))
        return make_download([t for t in tickers if t != 'ZZZZ'])

    monkeypatch.setattr(app_module, 'fetch_prices', fake_fetch)
    return calls


def test_form_page_renders(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'See your portfolio!' in response.get_data(as_text=True)


def test_submitting_the_form_puts_the_choices_in_the_url(client):
    response = client.post('/', data={'portfolio_ticker': 'aapl, msft',
                                      'time_frame': '1y', 'time_interval': '1wk'})

    assert response.status_code == 302
    assert response.headers['Location'] == '/portfolio/?portfolio_ticker=AAPL,MSFT&time_frame=1y&time_interval=1wk'


@pytest.mark.parametrize('frame, interval, message', [
    ('1d', '1wk', 'A 1wk interval is too long for a 1d time frame'),
    ('1mo', '1mo', 'A 1mo interval is too long for a 1mo time frame'),
    ('2y', '1h', 'Hourly data only goes back about two years'),
])
def test_form_rejects_intervals_that_do_not_fit_the_time_frame(client, frame, interval, message):
    response = client.post('/', data={'portfolio_ticker': 'AAPL', 'time_frame': frame, 'time_interval': interval})

    assert response.status_code == 200
    assert message in response.get_data(as_text=True)


def test_results_page_embeds_chart_data(client, downloads):
    response = client.get('/portfolio/?portfolio_ticker=MSFT,AAPL&time_frame=1y&time_interval=1d')

    assert response.status_code == 200
    assert downloads == [(['MSFT', 'AAPL'], '1y', '1d')]
    data = chart_data(response)
    assert [s['ticker'] for s in data['series']] == ['MSFT', 'AAPL']
    page = response.get_data(as_text=True)
    assert 'id="price-chart"' in page
    assert page.count('class="volume-chart"') == 2
    assert 'chart.umd.min.js' in page


def test_results_page_defaults_to_the_form_defaults(client, downloads):
    response = client.get('/portfolio/')

    assert response.status_code == 200
    assert downloads == [(['AAPL'], '1y', '1d')]


def test_results_page_warns_about_tickers_without_data(client, downloads):
    response = client.get('/portfolio/?portfolio_ticker=AAPL,ZZZZ&time_frame=1y&time_interval=1d')

    assert 'No price data was found for ZZZZ' in response.get_data(as_text=True)
    assert [s['ticker'] for s in chart_data(response)['series']] == ['AAPL']


def test_results_page_without_any_data(client, monkeypatch):
    monkeypatch.setattr(app_module, 'fetch_prices', lambda *args: pd.DataFrame())

    response = client.get('/portfolio/?portfolio_ticker=ZZZZ&time_frame=1y&time_interval=1d')

    assert response.status_code == 200
    assert 'No price data was found for ZZZZ' in response.get_data(as_text=True)
    assert chart_data(response) is None


def test_results_page_when_the_download_fails(client, monkeypatch):
    def broken_fetch(*args):
        raise ConnectionError('no network')
    monkeypatch.setattr(app_module, 'fetch_prices', broken_fetch)

    response = client.get('/portfolio/?portfolio_ticker=AAPL&time_frame=1y&time_interval=1d')

    assert 'Could not download data from Yahoo Finance' in response.get_data(as_text=True)
    assert chart_data(response) is None


@pytest.mark.parametrize('query, message', [
    ('portfolio_ticker=AA$PL', 'Not a valid ticker: AA$PL'),
    ('portfolio_ticker=A,B,C,D,E,F,G,H,I', 'Please enter at most 8 tickers.'),
    ('portfolio_ticker=AAPL&time_frame=5y', 'Not a valid choice'),
])
def test_results_page_rejects_bad_choices(client, downloads, query, message):
    response = client.get('/portfolio/?' + query)

    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    assert downloads == []
