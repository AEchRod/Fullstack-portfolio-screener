import numpy as np
import pandas as pd

from charts import build_chart_payload, build_table_html, format_price, prepare_prices
from form import parse_tickers


def test_parse_tickers_splits_uppercases_and_drops_repeats():
    assert parse_tickers(' aapl, msft  tsla;AAPL ') == ['AAPL', 'MSFT', 'TSLA']
    assert parse_tickers(', ,') == []


def test_prepare_prices_keeps_typed_order_and_reports_missing(make_download):
    data = make_download(['AAPL', 'MSFT', 'ZZZZ']).sort_index(axis=1)
    data.loc[:, (slice(None), 'ZZZZ')] = np.nan

    prices, found, missing = prepare_prices(data, ['MSFT', 'ZZZZ', 'AAPL'])

    assert found == ['MSFT', 'AAPL']
    assert missing == ['ZZZZ']
    assert 'ZZZZ' not in prices.columns.get_level_values(1)


def test_prepare_prices_accepts_flat_columns_for_one_ticker(make_download):
    data = make_download(['AAPL']).droplevel('Ticker', axis=1)

    prices, found, missing = prepare_prices(data, ['AAPL'])

    assert found == ['AAPL'] and missing == []
    assert prices[('Close', 'AAPL')].iloc[0] == 100.0


def test_prepare_prices_accepts_ticker_first_columns(make_download):
    data = make_download(['AAPL', 'MSFT']).swaplevel(axis=1)

    _, found, _ = prepare_prices(data, ['AAPL', 'MSFT'])

    assert found == ['AAPL', 'MSFT']


def test_prepare_prices_with_no_data():
    assert prepare_prices(pd.DataFrame(), ['AAPL']) == (None, [], ['AAPL'])
    assert prepare_prices(None, ['AAPL']) == (None, [], ['AAPL'])


def test_payload_has_prices_change_and_stats(make_download):
    prices, found, _ = prepare_prices(make_download(['AAPL', 'MSFT']), ['AAPL', 'MSFT'])

    payload = build_chart_payload(prices, found, '1d')

    assert payload['labels'] == ['2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08', '2026-01-09']
    assert payload['intraday'] is False
    aapl, msft = payload['series']
    assert aapl['ticker'] == 'AAPL' and msft['ticker'] == 'MSFT'
    assert aapl['close'] == [100.0, 101.0, 102.0, 103.0, 104.0]
    assert aapl['change_pct'][0] == 0.0
    assert aapl['change_pct'][-1] == 4.0
    assert msft['change_pct'][-1] == 2.0
    assert aapl['volume'] == [1_000_000] * 5
    assert aapl['stats'] == {'last': 104.0, 'change': 4.0, 'change_pct': 4.0,
                             'high': 105.0, 'low': 99.0, 'as_of': '2026-01-09'}


def test_payload_turns_gaps_into_null_and_measures_change_from_first_price(make_download):
    data = make_download(['AAPL', 'BTC-USD'])
    #a ticker can be missing days, e.g. one that started trading later
    data.loc[data.index[:2], (slice(None), 'AAPL')] = np.nan
    data.loc[data.index[3], ('Close', 'BTC-USD')] = np.nan
    prices, found, _ = prepare_prices(data, ['AAPL', 'BTC-USD'])

    aapl, btc = build_chart_payload(prices, found, '1d')['series']

    assert aapl['close'][:2] == [None, None]
    assert aapl['change_pct'][2] == 0.0
    assert aapl['volume'][:2] == [None, None]
    assert btc['close'][3] is None and btc['change_pct'][3] is None
    assert btc['stats']['last'] == 204.0


def test_intraday_labels_include_the_time(make_download):
    data = make_download(['AAPL'], periods=3, start='2026-01-05 09:30', freq='h')
    data.index = data.index.tz_localize('America/New_York')
    prices, found, _ = prepare_prices(data, ['AAPL'])

    payload = build_chart_payload(prices, found, '1h')

    assert payload['intraday'] is True
    assert payload['labels'] == ['2026-01-05T09:30', '2026-01-05T10:30', '2026-01-05T11:30']
    assert payload['series'][0]['stats']['as_of'] == '2026-01-05 11:30'


def test_table_lists_newest_first_with_each_ticker_grouped(make_download):
    prices, found, _ = prepare_prices(make_download(['AAPL', 'MSFT']), ['AAPL', 'MSFT'])

    html = build_table_html(prices, found, '1d')

    assert html.index('2026-01-09') < html.index('2026-01-05')
    assert html.index('AAPL') < html.index('MSFT')
    assert '<th>Date</th>' in html
    assert '1,000,000' in html and '104.00' in html


def test_format_price():
    assert format_price(1234.5) == '1,234.50'
    assert format_price(0.012345) == '0.0123'
    assert format_price(2.5, signed=True) == '+2.50'
    assert format_price(-2.5, signed=True) == '-2.50'
    assert format_price(None) == '—'
