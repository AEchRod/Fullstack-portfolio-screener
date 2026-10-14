import os
from flask import Flask, render_template, redirect, request, url_for
from form import PortfolioForm, csrf
from charts import (build_chart_payload, build_table_html, fetch_prices, format_percent,
                    format_price, prepare_prices)


app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
csrf.init_app(app)
app.add_template_filter(format_price, 'price')
app.add_template_filter(format_percent, 'percent')

@app.route('/', methods=['GET', 'POST'])

def start_page():
    form = PortfolioForm()
    if form.validate_on_submit():
        #pass the choices on in the URL so the results page can be refreshed and bookmarked
        return redirect(url_for("retrieve_portfolio",
                                portfolio_ticker=','.join(form.tickers),
                                time_frame=form.time_frame.data,
                                time_interval=form.time_interval.data))
    return render_template('form_render.html', form=form)

@app.route('/portfolio/', methods=['GET'])
def retrieve_portfolio():

    #read the choices back from the URL with the same form; a GET has no CSRF token to check
    form = PortfolioForm(formdata=request.args)
    form.validate()
    if any(field.errors for field in form if field.name != 'csrf_token'):
        return render_template('form_render.html', form=form), 400

    tickers = form.tickers
    time_frame = form.time_frame.data
    time_interval = form.time_interval.data

    error = None
    try:
        #this is a dataframe
        data = fetch_prices(tickers, time_frame, time_interval)
    except Exception:
        app.logger.exception('Downloading %s failed', tickers)
        data = None
        error = 'Could not download data from Yahoo Finance, please try again in a moment.'

    prices, found, missing = prepare_prices(data, tickers)
    chart_data = build_chart_payload(prices, found, time_interval) if found else None
    table_html = build_table_html(prices, found, time_interval) if found else None

    #render template and pass variables for Jinja
    return render_template("results_render.html", tickers=tickers, time_frame=time_frame,
                           time_interval=time_interval, chart_data=chart_data,
                           table_html=table_html, missing=missing, error=error)

if __name__ == "__main__":
    app.run(port=5000, debug= True)
