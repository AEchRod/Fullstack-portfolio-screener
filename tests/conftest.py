import numpy as np
import pandas as pd
import pytest

from app import app as flask_app


def fake_download(tickers, periods=5, start='2026-01-05', freq='B'):
    """A DataFrame shaped like yf.download's: (field, ticker) columns, sorted by field."""
    index = pd.date_range(start, periods=periods, freq=freq, name='Date')
    columns = pd.MultiIndex.from_product([['Close', 'High', 'Low', 'Open', 'Volume'], tickers],
                                         names=['Price', 'Ticker'])
    data = pd.DataFrame(index=index, columns=columns, dtype=float)
    for n, ticker in enumerate(tickers):
        close = 100.0 * (n + 1) + np.arange(periods)
        data[('Close', ticker)] = close
        data[('Open', ticker)] = close - 0.5
        data[('High', ticker)] = close + 1
        data[('Low', ticker)] = close - 1
        data[('Volume', ticker)] = 1_000_000.0 * (n + 1)
    return data


@pytest.fixture
def make_download():
    return fake_download


@pytest.fixture
def client():
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with flask_app.test_client() as client:
        yield client
