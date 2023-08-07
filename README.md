# Fullstack portfolio screener

## Description 

The Fullstack Portfolio Screener is a web application that empowers users to track selected stocks within a specified period and interval. The app utilizes YFinance to retrieve stock data in the form of a dataframe. Jinja and HTML are employed to create the form rendering.



## Dependencies

- Flask: A micro web framework for building web applications using Python.
- Flask-WTF: An extension for Flask that simplifies the integration of WTForms, a library for handling web forms.
- yfinance: A Python library for retrieving historical stock market data from Yahoo Finance.
- Bootstrap: A popular front-end framework for building responsive and visually appealing web interfaces.

## Files

1. **form.py**: This file contains the definition of the `PortfolioForm` class, which inherits from `FlaskForm` from the `flask_wtf` library. This form is used to capture user input for the stock ticker, time frame, and time interval. The available choices for time frames and intervals are defined as constants (`time_frame_choices` and `time_interval_choices`).

2. **app.py**: This is the main body of the Flask application. It imports necessary libraries, initializes the Flask app, sets up CSRF protection, and defines two routes (`/` and `/portfolio/`) to handle user interactions.

   - `start_page()`: This route renders the initial form page. If the form is submitted with valid data, it redirects to the `retrieve_portfolio` route.
   - `retrieve_portfolio()`: This route handles the retrieval of stock market data based on the user's input. It processes the form data, determines the time frame, retrieves historical stock data using the `yfinance` library, and returns the data in HTML format for rendering.

3. **base.html**: This is the base HTML template for the web application. It provides the basic structure for the web pages and includes necessary Bootstrap styles and scripts. The `{% block content %}` and `{% endblock %}` tags define where content from other templates will be inserted.

## Usage

1. Install required libraries by running `pip install flask flask-wtf yfinance`.

2. Run the Flask app by executing `python app.py`.

3. Access the web application through a browser by visiting `http://localhost:5000/`.

4. On the initial page, users can enter a stock ticker symbol, select a time frame, and choose a time interval. After clicking the "See your portfolio!" button, the application will redirect to the portfolio page.

5. The portfolio page will display historical stock market data for the selected stock ticker, time frame, and time interval.

## Notes

- The `csrf` module is used to provide CSRF (Cross-Site Request Forgery) protection to the forms in the application.

- The application uses the `yfinance` library to retrieve historical stock data based on the user's input.

- The application's base template (`base.html`) provides a consistent layout and styling for all pages.

- The project is intended as a first iteration, using HTML and Flask to create a simple web app for tracking a stock portfolio.

#### Current errors (SOLVED - 04.23)

It currently fails to show data once the form has been submitted, there seems to be an error in passing input data from the form as a value/variable for
the data we want to retrieve for the stocks?
i.e. interval=none (EVEN THOUGH INTERVAL HAS BEEN SELECTED IN FORM)

## Progress

#### Progress (08.23)

***The app only retrieves data for one ticker, the default specified in the form.*** 

- [ ] Investigating the correct way to transform data from the form into a format so that it can be passed as a string or list to the variable to retrieve the dataframe.
- [x] Next steps would also involve rendering the page where the results are returned.



#### Screenshots/Instructions:



Results Screenshot

Rendered Table

Please note that further refinements, optimizations, and additional features can be added to the application based on specific requirements and needs. The project is designed to evolve and improve over time.

1) Input your preferred stock(s) along with the desired time frame and interval within the form:

![image](https://github.com/AEchRod/Fullstack-portfolio-screener-beta-/assets/85241651/33c58584-52b2-4f66-a6df-4b404226d8cd)

2) After submission, you'll be presented with the extracted price data based on your selections. Note that this display will be enhanced to utilize the base template/block and be properly rendered:

![image](https://github.com/AEchRod/Fullstack-portfolio-screener-beta-/assets/85241651/18a0834a-8913-4e84-8088-9bbb77890acc)

Properly rendered as a table as per 07.08.23!

![image](https://github.com/AEchRod/Fullstack-portfolio-screener-beta-/assets/85241651/e99282f7-17ab-4f1f-98ee-ff263679e2ea)

Please note that further refinements, optimizations, and additional features can be added to the application based on specific requirements and needs. The project is designed to evolve and improve over time.

