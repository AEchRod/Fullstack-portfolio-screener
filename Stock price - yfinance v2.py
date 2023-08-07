import os
from flask import Flask, render_template, redirect, url_for
from form import PortfolioForm, csrf
import yfinance as yf
import pytz
import datetime as dt
from datetime import timedelta


app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
csrf.init_app(app)

@app.route('/', methods=['GET', 'POST'])

def start_page():
    form = PortfolioForm()
    if form.validate_on_submit():
        return redirect(url_for("retrieve_portfolio"))
    return render_template('form_render.html', form=form)

@app.route('/portfolio/', methods=['GET', 'POST'])
def retrieve_portfolio():

    form = PortfolioForm()

    ticker = form.portfolio_ticker.data

    yf.pdr_override()

    tz = pytz.timezone("America/New_York")
    end = tz.localize(dt.datetime.now())

    if time_frame == '1d':
        start = end - timedelta(days=1)
    elif time_frame == '1mo':
        start = end - timedelta(days=30)
    elif time_frame == '1y':
        start = end - timedelta(days=365)
    elif time_frame == '2y':
        start = end - timedelta(days=365 * 2)
    else:
        # Default to a reasonable start date
        start = tz.localize(dt.datetime(2018, 1, 1))

    #this is a dataframe
    data = yf.download(tickers=ticker, start=start, end=end)


    #this converts the dataframe to html
    data_html = data.to_html()

    #render template and pass variable for Jinja variable
    return render_template("results_render.html", data_html = data_html)

if __name__ == "main":
    app.run(port=5000, debug= True)
