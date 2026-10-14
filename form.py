import re

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SelectField, validators, SubmitField, ValidationError

csrf = CSRFProtect()

time_frame_choices = [('1d', '1d'), ('1mo', '1mo'), ('1y', '1y'), ('2y', '2y')]
time_interval_choices = [('1h', '1h'), ('1d', '1d'), ('5d', '5d'), ('1wk', '1wk'), ('1mo', '1mo'), ('3mo', '3mo')]

#the charts have one colour per ticker, and eight colours
MAX_TICKERS = 8
#letters, digits and the symbols Yahoo uses, e.g. BRK-B, ^GSPC, EURUSD=X
TICKER_PATTERN = re.compile(r'^[A-Z0-9.\-^=]{1,15}$')
#rough length of each choice in days, to catch intervals too long to draw a trend
DAYS = {'1h': 1 / 24, '1d': 1, '5d': 5, '1wk': 7, '1mo': 30, '3mo': 90, '1y': 365, '2y': 730}


def parse_tickers(raw):
    """Turn 'aapl, msft tsla' into ['AAPL', 'MSFT', 'TSLA'], dropping repeats."""
    tickers = []
    for part in re.split(r'[\s,;]+', raw or ''):
        ticker = part.upper()
        if ticker and ticker not in tickers:
            tickers.append(ticker)
    return tickers


class PortfolioForm(FlaskForm): #inheriting from FlaskForm

    portfolio_ticker = StringField(u'Please input ticker(s) to add to your stock portfolio, separated by commas (data available since 2018): ', default='AAPL', validators=[validators.DataRequired()])
    time_frame = SelectField(u'Select time frame: ', choices=time_frame_choices, default='1y')
    time_interval = SelectField(u'Select time interval: ', choices=time_interval_choices, default='1d')
    submit = SubmitField('See your portfolio!')

    @property
    def tickers(self):
        return parse_tickers(self.portfolio_ticker.data)

    def validate_portfolio_ticker(self, field):
        tickers = parse_tickers(field.data)
        if not tickers:
            raise ValidationError('Please enter at least one ticker.')
        invalid = [t for t in tickers if not TICKER_PATTERN.match(t)]
        if invalid:
            raise ValidationError(f'Not a valid ticker: {", ".join(invalid)}')
        if len(tickers) > MAX_TICKERS:
            raise ValidationError(f'Please enter at most {MAX_TICKERS} tickers.')

    def validate_time_interval(self, field):
        interval, frame = field.data, self.time_frame.data
        if interval in DAYS and frame in DAYS and DAYS[interval] >= DAYS[frame]:
            raise ValidationError(f'A {interval} interval is too long for a {frame} time frame, please pick a shorter interval.')
        #Yahoo only keeps hourly prices for the last 730 days
        if interval == '1h' and frame == '2y':
            raise ValidationError('Hourly data only goes back about two years, please pick a 1y time frame or shorter.')
