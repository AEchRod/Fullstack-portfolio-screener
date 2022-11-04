import os
from flask import Flask, render_template, jsonify, redirect, url_for #request
from form import PortfolioForm, csrf, time_frame_choices, time_interval_choices
import yfinance as yf
#import pandas as pd

#from pandas_datareader import data as pdr
#yf.pdr_override()

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
csrf.init_app(app)

"""portfolio_filler = str(input("Please input tickers to add to your stock portfolio: "))
#this breaks the user input into a list so we can check each individual ticker.
portfolio_list = portfolio_filler.split(" ")
time_period = str(input("Please select time frame (1d, 1mo): "))
time_interval = str(input("Please select time interval (1h, 1d, 1wk): "))"""

#print("Your porfolio is made up of: ", portfolio_list)

@app.route('/', methods=['GET', 'POST'])
def start_page():
    form = PortfolioForm()
    if form.validate_on_submit():
        return redirect(url_for("retrieve_portfolio"))
    return render_template('form_render.html', form=form)

@app.route('/portfolio/', methods=['GET', 'POST'])
def retrieve_portfolio():
    forms = PortfolioForm()

    port_tick = str(forms.portfolio_ticker.data)
    tim_fr = dict(time_frame_choices).get(forms.time_frame.data)
    tim_int = dict(time_interval_choices).get(forms.time_interval.data)

    data = yf.download(tickers=str(port_tick), period=str(tim_fr), interval=str(tim_int))

    #df = pd.DataFrame(data)
    #data.to_html() -> to convert the dataframe to HTML, data.values.tolist() if it was a Pandas dataframe
    return jsonify(data.to_dict())

#tickers = yf.Tickers(portfolio_filler)
#tickers.tickers.portfolio_filler.history(period=time_period)
# get stock info
#msft.info

# get historical market data
"""hist = msft.history(period="max")
hist_1d = msft.history(period="1d")"""

#print(msft.info)
#print(hist_1d)

if __name__ == "main":
    app.run(port=5000, debug= True)

