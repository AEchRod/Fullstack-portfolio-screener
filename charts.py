"""Turns the price data downloaded with yfinance into chart series, summary stats and a table."""
import math

import pandas as pd
import yfinance as yf

PRICE_FIELDS = ['Open', 'High', 'Low', 'Close']


def fetch_prices(tickers, time_frame, time_interval):
    #yfinance accepts the form's time frame and interval choices directly as period and interval
    return yf.download(tickers=tickers, period=time_frame, interval=time_interval,
                       auto_adjust=True, progress=False)


def is_intraday(time_interval):
    #minute and hour intervals ('1m', '1h', ...) carry a time of day; '1mo' and '3mo' do not
    return time_interval.endswith(('m', 'h'))


def format_price(value, signed=False):
    """Two decimals for normal prices, four for prices under 1 (penny stocks, currencies)."""
    if value is None:
        return '—'
    decimals = 2 if abs(value) >= 1 else 4
    sign = '+' if signed and value > 0 else ''
    return f'{sign}{value:,.{decimals}f}'


def format_percent(value):
    if value is None:
        return '—'
    return f'{value:+.2f}%'


def _number(value, digits):
    #NaN and infinity become None so they turn into null in the page's JSON
    if value is None or pd.isna(value) or not math.isfinite(value):
        return None
    return round(float(value), digits)


def prepare_prices(data, tickers):
    """Return (prices, found, missing).

    prices has (field, ticker) columns for the tickers that came back with data, in the
    order the user typed them; missing lists the tickers yfinance found nothing for.
    """
    if data is None or data.empty:
        return None, [], list(tickers)

    #yfinance returns (field, ticker) columns, but older versions use flat columns for one ticker
    if not isinstance(data.columns, pd.MultiIndex):
        data = data.copy()
        data.columns = pd.MultiIndex.from_product([data.columns, tickers[:1]])
    elif 'Close' not in data.columns.get_level_values(0):
        data = data.swaplevel(axis=1)

    close = data['Close']
    found = [t for t in tickers if t in close.columns and close[t].notna().any()]
    missing = [t for t in tickers if t not in found]
    if not found:
        return None, [], missing

    prices = data.loc[:, data.columns.get_level_values(1).isin(found)]
    prices = prices.loc[close[found].notna().any(axis=1)]
    return prices, found, missing


def _labels(index, time_interval):
    fmt = '%Y-%m-%dT%H:%M' if is_intraday(time_interval) else '%Y-%m-%d'
    return [ts.strftime(fmt) for ts in index]


def _column(prices, field, ticker):
    if (field, ticker) in prices.columns:
        return prices[(field, ticker)]
    return prices[('Close', ticker)]


def build_chart_payload(prices, found, time_interval):
    """Everything the charts on the results page need, as JSON-ready lists."""
    labels = _labels(prices.index, time_interval)
    series = []
    for ticker in found:
        close = prices[('Close', ticker)]
        valid = close.notna().to_numpy().nonzero()[0]
        first, last = close.iloc[valid[0]], close.iloc[valid[-1]]
        #every point as % change from the first close, so tickers with different prices share one axis
        change_pct = (close / first - 1) * 100
        if ('Volume', ticker) in prices.columns:
            volume = [None if pd.isna(v) else int(v) for v in prices[('Volume', ticker)]]
        else:
            volume = [None] * len(labels)

        series.append({
            'ticker': ticker,
            'close': [_number(v, 4) for v in close],
            'change_pct': [_number(v, 4) for v in change_pct],
            'volume': volume,
            'stats': {
                'last': _number(last, 4),
                'change': _number(last - first, 4),
                'change_pct': _number((last / first - 1) * 100, 2),
                'high': _number(_column(prices, 'High', ticker).max(), 4),
                'low': _number(_column(prices, 'Low', ticker).min(), 4),
                'as_of': labels[valid[-1]].replace('T', ' '),
            },
        })
    return {'labels': labels, 'intraday': is_intraday(time_interval), 'series': series}


def build_table_html(prices, found, time_interval):
    """The downloaded data as an HTML table, newest first, with each ticker's columns grouped."""
    columns = {}
    for ticker in found:
        for field in PRICE_FIELDS:
            if (field, ticker) in prices.columns:
                columns[(ticker, field)] = [format_price(_number(v, 4)) for v in prices[(field, ticker)]]
        if ('Volume', ticker) in prices.columns:
            columns[(ticker, 'Volume')] = ['—' if pd.isna(v) else f'{int(v):,}' for v in prices[('Volume', ticker)]]

    table = pd.DataFrame(columns, index=[label.replace('T', ' ') for label in _labels(prices.index, time_interval)])
    #'Date' heads the index column on the same header row as the field names
    table.columns.names = [None, 'Date']
    return table.iloc[::-1].to_html(classes='table table-sm table-striped table-hover text-end mb-0', border=0)
