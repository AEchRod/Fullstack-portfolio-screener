import os
from flask import Flask, render_template, jsonify, redirect, url_for #request
from form import PortfolioForm, csrf, time_frame_choices, time_interval_choices
import yfinance as yf

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
csrf.init_app(app)

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
    port_tick_split = port_tick.split(" ")
    tim_fr = dict(time_frame_choices).get(forms.time_frame.data)
    tim_int = dict(time_interval_choices).get(forms.time_interval.data)

    #this is a dataframe
    data = yf.download(tickers=port_tick_split, period=str(tim_fr), interval=str(tim_int))

    #data.to_html() -> to convert the dataframe to HTML, or data.values.tolist()
    #return jsonify(data.to_dict())
    return data.to_json()


if __name__ == "main":
    app.run(port=5000, debug= True)


