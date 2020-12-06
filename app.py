import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objects as go
from pymongo import MongoClient
import pandas as pd

#from database import fetch_all_bpa_as_df

# Definitions of constants. This projects uses extra CSS stylesheet at `./assets/style.css`
COLORS = ['rgb(637,657,687)', 'rgb(80,80,80)', 'rgb(100,100,100)', 'rgb(115,115,115)', 'rgb(135,67,69)',
          'rgb(189,189,189)', 'rgb(67,80,100)', 'rgb(123,33,67)', 'rgb(138,45,69)', 'rgb(167,167,167)',
          'rgb(87,67,87)', 'rgb(67,67,67)', 'rgb(49,130,189)', 'rgb(467,67,35)', 'rgb(168,168,168)',
          'rgb(6,33,105)', 'rgb(8,14,215)', 'rgb(47,47,47)']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', '/assets/style.css']

# Define the dash app first
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def page_header():
    """
    Returns the page header as a dash `html.Div`
    """
    return html.Div(id='header', children=[
        html.Div([html.H3('Visualization with datashader and Plotly')],
                 className="ten columns"),
        html.A([html.Img(id='logo', src=app.get_asset_url('github.png'),
                         style={'height': '35px', 'paddingTop': '7%'}),
                html.Span('yangyinke', style={'fontSize': '2rem', 'height': '35px', 'bottom': 0,
                                                'paddingLeft': '4px', 'color': '#a3a7b0',
                                                'textDecoration': 'none'})],
               className="two columns row",
               href='https://github.com/yangyinke'),
    ], className="row")

def description():
    """
    Returns overall project description in markdown
    """
    return html.Div(children=[dcc.Markdown('''
        # Covid case number and stock price
        Explore the relationship between stock price and covid case number

        
        ### Data Source
        This project utilizes up-to-date covid case data from [The COVID Tracking Project](https://covidtracking.com/data/national/cases)
        and stock price data from [Yahoo Finance](https://finance.yahoo.com/). 
        All data in the database are **updated every day**. 
        ''', className='eleven columns', style={'paddingLeft': '5%'})], className="row")

def stock_price_trend():
    """
    Returns description of plots about stock price trend and covid case number
    """
    return html.Div(children=[dcc.Markdown('''
        
        ### Stock Price Trend
        The plots below are about stock price trend and covid case number. Stocks were divided into three 
        plots based on their corresponding scale.
        ''', className='eleven columns', style={'paddingLeft': '5%'})], className="row")

def stock_price_fluc():
    """
    Returns description of plots about stock price fluctuation and covid case number
    """
    return html.Div(children=[dcc.Markdown('''
        
        ### Stock Price Fluctuation
        The plots below are about stock price fluctuation and covid case number. Stocks were divided into three 
        plots based on their types of fluctuation rate
        ''', className='eleven columns', style={'paddingLeft': '5%'})], className="row")

def get_covid_case():
    # get covid data from MongoDB
    connection_string = "mongodb+srv://enmin:data1050@sandbox.skbnz.mongodb.net/test"
    client = MongoClient(connection_string)
    db = client.get_database("covid")
    collection = db.get_collection("cases")
    data = list(collection.find())
    covid_df = pd.DataFrame.from_records(data)    
    covid_df.drop('_id', axis=1, inplace=True)
    covid_df['date'] = pd.to_datetime(covid_df['date'])
    return covid_df

def get_stock_data():
    connection_string = "mongodb+srv://enmin:data1050@sandbox.skbnz.mongodb.net/test"

    client = MongoClient(connection_string)
    db = client.get_database("stock")
    collection = db.get_collection("historical")
    data = list(collection.find())
    stock_df = pd.DataFrame.from_records(data)    
    stock_df.drop('_id', axis=1, inplace=True)
    stock_df['date'] = pd.to_datetime(stock_df['date'])
    stock_df = stock_df.dropna()

    # create a new column in stock_df to show price fluctuation
    # columns = ['AAPL', 'MSFT', 'GOOG', 'FB', 'AMZN', 'WMT', 'GE', 'MMM', 'AMT', 'JNJ', 'PFE', 'JPM', 'V', 'XOM', '^GSPC', '^DJI', 'GC=F', 'CL=F']
    codes = stock_df['code'].unique()
    fluc = dict()
    for code in codes:
        fluc[code] = [0] + [(stock_df[stock_df['code']==code].iloc[i]['close'] - stock_df[stock_df['code']==code].iloc[i-1]['close'])/stock_df[stock_df['code']==code].iloc[i-1]['close'] 
                            for i in range(1,stock_df[stock_df['code']==code]['date'].nunique())]
    record = []
    for code in codes:
        record += fluc[code]
    stock_df['fluctuation'] = record
    return stock_df


def static_trend_graph(codes, scale, target, covid_df, stock_df, stack=False):
    """
    Returns a plot of stock price and covid case
    """
    if covid_df is None or stock_df is None:
        return go.Figure()
    fig = go.Figure()
    
    # plot the trend of close stock price
    for i, code in enumerate(codes):
        df = stock_df[stock_df['code'] == code]
        #df = df[df['date'] >= '2020-01-22']
        fig.add_trace(go.Scatter(x=df['date'], y=df[target], mode='lines', name=code,
                                 line={'width': 2, 'color': COLORS[i]},
                                 stackgroup='stack' if stack else None))
    
    # plot the trend of new cases
    if scale == 100:
        name = 'new cases scaled by hundredth'
    elif scale == 1000:
        name = 'new cases scaled by thousandth'
    elif scale == 10:
        name = 'new cases scaled by tenth'
    elif scale == 1000000:
        name = 'new cases scaled by millionth'
    elif scale == 100000:
        name = 'new cases scaled by 1/100,000'
    else:
        name = None
    fig.add_trace(go.Scatter(x=covid_df['date'], y=covid_df['new_case']/scale, mode='lines', name=name,
                             line={'width': 2, 'color': 'orange'}))

    fig.update_layout(template='plotly_dark',
                      title=None,
                      plot_bgcolor='#23272c',
                      paper_bgcolor='#23272c',
                      yaxis_title='number of new cases/stock price',
                      xaxis_title='Date')
    return fig

def low_stock_price_plot(covid_df, stock_df):
    codes = ['AAPL', 'MSFT', 'FB', 'WMT','GE', 'MMM', 'AMT', 'JNJ', 'PFE', 'JPM', 'V', 'XOM', 'CL=F']
    fig = static_trend_graph(codes, 1000, 'close', covid_df, stock_df, stack=False)
    fig.update_layout(title='cheap stock price & number of new cases')
    return fig

def exp_stock_price_plot(covid_df, stock_df):
    codes = ['GOOG', 'AMZN', '^GSPC', 'GC=F',]
    fig = static_trend_graph(codes, 100, 'close', covid_df, stock_df, stack=False)
    fig.update_layout(title='expensive stock price & number of new cases')
    return fig

def dj_plot(covid_df, stock_df):
    codes = ['^DJI',]
    fig = static_trend_graph(codes, 10, 'close', covid_df, stock_df, stack=False)
    fig.update_layout(title='Dow Jones Industrial Average & number of new cases')
    return fig

def stock_price_fluc_plot(covid_df, stock_df):
    codes = ['AAPL', 'MSFT', 'GOOG', 'FB', 'AMZN', 'WMT', 'GE', 'MMM', 'AMT', 'JNJ', 'PFE', 'JPM', 'V', 'XOM']
    fig = static_trend_graph(codes, 1000000, 'fluctuation',covid_df, stock_df, stack=False)
    fig.update_layout(yaxis_title='number of new cases/fluctuation percentage',
                  title='stock price fluctuation in percentage & number of new cases')
    return fig

def market_index_fluc_plot(covid_df, stock_df):
    codes = ['^GSPC', '^DJI', 'GC=F']#, 'CL=F']
    fig = static_trend_graph(codes, 1000000, 'fluctuation',covid_df, stock_df, stack=False)
    fig.update_layout(yaxis_title='number of new cases/fluctuation percentage',
                    title='market index fluctuation in percentage & number of new cases')
    return fig

def co_fluc_plot(covid_df, stock_df):
    codes = ['CL=F']
    fig = static_trend_graph(codes, 100000, 'fluctuation',covid_df, stock_df, stack=False)
    fig.update_layout(title='Crude Oil Jan 21 fluctuation & number of new cases')
    return fig

# def what_if_description():
#     """
#     Returns description of "What-If" - the interactive component
#     """
#     return html.Div(children=[
#         dcc.Markdown('''
#         # " What If "
#         So far, BPA has been relying on hydro power to balance the demand and supply of power. 
#         Could our city survive an outage of hydro power and use up-scaled wind power as an
#         alternative? Find below **what would happen with 2.5x wind power and no hydro power at 
#         all**.   
#         Feel free to try out more combinations with the sliders. For the clarity of demo code,
#         only two sliders are included here. A fully-functioning What-If tool should support
#         playing with other interesting aspects of the problem (e.g. instability of load).
#         ''', className='eleven columns', style={'paddingLeft': '5%'})
#     ], className="row")


# def what_if_tool():
#     """
#     Returns the What-If tool as a dash `html.Div`. The view is a 8:3 division between
#     demand-supply plot and rescale sliders.
#     """
#     return html.Div(children=[
#         html.Div(children=[dcc.Graph(id='what-if-figure')], className='nine columns'),

#         html.Div(children=[
#             html.H5("Rescale Power Supply", style={'marginTop': '2rem'}),
#             html.Div(children=[
#                 dcc.Slider(id='wind-scale-slider', min=0, max=4, step=0.1, value=2.5, className='row',
#                            marks={x: str(x) for x in np.arange(0, 4.1, 1)})
#             ], style={'marginTop': '5rem'}),

#             html.Div(id='wind-scale-text', style={'marginTop': '1rem'}),

#             html.Div(children=[
#                 dcc.Slider(id='hydro-scale-slider', min=0, max=4, step=0.1, value=0,
#                            className='row', marks={x: str(x) for x in np.arange(0, 4.1, 1)})
#             ], style={'marginTop': '3rem'}),
#             html.Div(id='hydro-scale-text', style={'marginTop': '1rem'}),
#         ], className='three columns', style={'marginLeft': 5, 'marginTop': '10%'}),
#     ], className='row eleven columns')


# def architecture_summary():
#     """
#     Returns the text and image of architecture summary of the project.
#     """
#     return html.Div(children=[
#         dcc.Markdown('''
#             # Project Architecture
#             This project uses MongoDB as the database. All data acquired are stored in raw form to the
#             database (with de-duplication). An abstract layer is built in `database.py` so all queries
#             can be done via function call. For a more complicated app, the layer will also be
#             responsible for schema consistency. A `plot.ly` & `dash` app is serving this web page
#             through. Actions on responsive components on the page is redirected to `app.py` which will
#             then update certain components on the page.  
#         ''', className='row eleven columns', style={'paddingLeft': '5%'}),

#         html.Div(children=[
#             html.Img(src="https://docs.google.com/drawings/d/e/2PACX-1vQNerIIsLZU2zMdRhIl3ZZkDMIt7jhE_fjZ6ZxhnJ9bKe1emPcjI92lT5L7aZRYVhJgPZ7EURN0AqRh/pub?w=670&amp;h=457",
#                      className='row'),
#         ], className='row', style={'textAlign': 'center'}),

#         dcc.Markdown('''
        
#         ''')
#     ], className='row')


# Sequentially add page components to the app's layout

def dynamic_layout():
    # get data first
    covid_df = get_covid_case()
    stock_df = get_stock_data()

    return html.Div([
        page_header(),
        html.Hr(),
        description(),
        stock_price_trend(),
        #dcc.Graph(id='trend-graph', figure=static_stacked_trend_graph(stack=False)),
        dcc.Graph(id='stock_price1', figure=low_stock_price_plot(covid_df, stock_df)),
        dcc.Graph(id='stock_price2', figure=exp_stock_price_plot(covid_df, stock_df)),
        dcc.Graph(id='stock_price3', figure=dj_plot(covid_df, stock_df)),
        stock_price_fluc(),
        dcc.Graph(id='stock_fluc1', figure=stock_price_fluc_plot(covid_df, stock_df)),
        dcc.Graph(id='stock_fluc2', figure=market_index_fluc_plot(covid_df, stock_df)),
        dcc.Graph(id='stock_fluc3', figure=co_fluc_plot(covid_df, stock_df)),
        # what_if_description(),
        # what_if_tool(),
        # architecture_summary(),
    ], className='row', id='content')


# set layout to a function which updates upon reloading
app.layout = dynamic_layout


# Defines the dependencies of interactive components

# @app.callback(
#     dash.dependencies.Output('wind-scale-text', 'children'),
#     [dash.dependencies.Input('wind-scale-slider', 'value')])
# def update_wind_sacle_text(value):
#     """Changes the display text of the wind slider"""
#     return "Wind Power Scale {:.2f}x".format(value)


# @app.callback(
#     dash.dependencies.Output('hydro-scale-text', 'children'),
#     [dash.dependencies.Input('hydro-scale-slider', 'value')])
# def update_hydro_sacle_text(value):
#     """Changes the display text of the hydro slider"""
#     return "Hydro Power Scale {:.2f}x".format(value)



# @app.callback(
#     dash.dependencies.Output('what-if-figure', 'figure'),
#     [dash.dependencies.Input('wind-scale-slider', 'value'),
#      dash.dependencies.Input('hydro-scale-slider', 'value')])
# def what_if_handler(wind, hydro):
#     """Changes the display graph of supply-demand"""
#     df = fetch_all_bpa_as_df(allow_cached=True)
#     x = df['Datetime']
#     supply = df['Wind'] * wind + df['Hydro'] * hydro + df['Fossil/Biomass'] + df['Nuclear']
#     load = df['Load']

#     fig = go.Figure()
#     fig.add_trace(go.Scatter(x=x, y=supply, mode='none', name='supply', line={'width': 2, 'color': 'pink'},
#                   fill='tozeroy'))
#     fig.add_trace(go.Scatter(x=x, y=load, mode='none', name='demand', line={'width': 2, 'color': 'orange'},
#                   fill='tonexty'))
#     fig.update_layout(template='plotly_dark', title='Supply/Demand after Power Scaling',
#                       plot_bgcolor='#23272c', paper_bgcolor='#23272c', yaxis_title='MW',
#                       xaxis_title='Date/Time')
#     return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=1050, host='0.0.0.0')
