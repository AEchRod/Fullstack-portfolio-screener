import os
from flask import Flask, render_template, redirect, url_for
from form import PortfolioForm, csrf
import yfinance as yf
import pytz
import datetime as dt


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
    start = tz.localize(dt.datetime(2018, 1, 1))
 

    #this is a dataframe
    data = yf.download(tickers=ticker, start=start, end=end)


    #this converts the dataframe to json
    return data.to_json()
    

if __name__ == "main":
    app.run(port=5000, debug= True)
