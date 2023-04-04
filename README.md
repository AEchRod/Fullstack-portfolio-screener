# Fullstack-portfolio-screener (beta)

## Description 

A fullstack app which allows the users to select stocks which they want to track and select the period and interval they want to track and then be
shown the data once the form has been submitted, using YFinance to retrieve the stock data as dataframe.
Using Jinja and HTML to create the form rendering.

#### Installation/requirements

WTForms, flask_wtf, yfinance, pytz

#### Current errors (SOLVED - 04.23)

It currently fails to show data once the form has been submitted, there seems to be an error in passing input data from the form as a value/variable for
the data we want to retrieve for the stocks?
i.e. interval=none (EVEN THOUGH INTERVAL HAS BEEN SELECTED IN FORM)

#### Progress (04.23)

***The app only retrieves data for one ticker, the default specified in the form.*** 
Investigating the correct way to transform data from the form into a format so that it can be passed as a string or list to the variable to retrieve the dataframe.

Next steps would also involve rendering the page where the results are returned.
