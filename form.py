from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SelectField, validators, SubmitField

csrf = CSRFProtect()

time_frame_choices = [('1d', '1d'), ('1mo', '1mo'), ('1y', '1y'), ('2y', '2y')]
time_interval_choices = [('1h', '1h'), ('1d', '1d'), ('5d', '5d'), ('1wk', '1wk'), ('1mo', '1mo'), ('3mo', '3mo')]


class PortfolioForm(FlaskForm): #inheriting from FlaskForm

    portfolio_ticker = StringField(u'Please input ticker to add to your stock portfolio (data available since 2018): ', default='AAPL', validators=[validators.DataRequired()])
    time_frame = SelectField(u'Select time frame: ', choices=time_frame_choices)
    time_interval = SelectField(u'Select time interval: ', choices=time_interval_choices)
    submit = SubmitField('See your portfolio!')
