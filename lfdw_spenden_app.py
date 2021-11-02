import dash
import yaml
import os
import setup
from dash import dash_table
from dash import dcc
from dash import html
from pandas import Timestamp as ts
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dash_table.Format import Format, Group, Prefix, Scheme, Symbol
from dash import dash_table
from flask_caching import Cache

config_filename = 'config.yml'
configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
config = yaml.safe_load (configstream)
address = config["database"].get('address')
username = config["database"].get('username')
password = config["database"].get('password')
database = config["database"].get('database')
CACHE_TIME = config.get('cachetime')  # seconds
startdate= ts(config.get('starttime'))
enddate= ts(config.get('endtime'))

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})



@cache.memoize(timeout=CACHE_TIME)
def query_data():
    connection = setup.create_connection(username=username,password=password,address=address,database=database)

    df = pd.read_sql(sql='SELECT donated_at,donated_amount_in_cents FROM donations ORDER BY donated_at ASC',con=connection,parse_dates=['donated_at'])
    df['donated_amount_in_Euro'] = df.donated_amount_in_cents.div(100).round(2)
    df['cumulated_sum'] = df.donated_amount_in_Euro.cumsum(axis = 0, skipna = True)
    df=df.sort_values(by='donated_at', ascending=False)
    template_pie= {'donations': [0,0,0,0],'categories':['bis 10 €','10 bis 100 €','100 bis 1000 €', 'über 1000 €'],'donation_sum':[0,0,0,0]}
    for index, row in df.iterrows():
        if (row['donated_amount_in_cents']<1000):
            template_pie['donations'][0] += 1
            template_pie['donation_sum'][0] += row["donated_amount_in_Euro"]

        elif (row['donated_amount_in_cents']<10000):
            template_pie['donations'][1] += 1
            template_pie['donation_sum'][1] += row["donated_amount_in_Euro"]

        elif (row['donated_amount_in_cents']<100000):
            template_pie['donations'][2] += 1
            template_pie['donation_sum'][2] += row["donated_amount_in_Euro"]

        elif (row['donated_amount_in_cents']>=100000):
            template_pie['donations'][3] += 1
            template_pie['donation_sum'][3] += row["donated_amount_in_Euro"]

    df_pie= pd.DataFrame(data=template_pie)
    return df,df_pie

@app.callback(
    Output(component_id='Komplettgrafik', component_property='figure'),
    Output(component_id='Komplettabelle', component_property='data'),
    Output(component_id='10_100_k_pie', component_property='figure'),
    Input('button_reload', 'n_clicks'),
)
def update_app(n_clicks):
    df,df_pie = query_data()
    linechart = px.line(data_frame=df, x="donated_at", y="cumulated_sum",
                hover_data=['donated_at','cumulated_sum'],
                labels={
                    "donated_at":"Zeitpunkt der Spende",
                    "cumulated_sum" : "Spendenstand"
                },
                color_discrete_sequence=["red"],
                range_x=[startdate,enddate])
    # change the graph to only show the current maximum time
    maxentry=df["donated_at"].max()
    if (enddate>=maxentry):
        linechart.update_xaxes(
            range=[startdate,maxentry]
        )

    labels=df_pie['categories']
    piecharts = make_subplots (rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
    piecharts.add_trace (go.Pie(labels=labels,values=df_pie['donations'],
                    name='Spender',sort=False),1,1)
    piecharts.add_trace (go.Pie(labels=labels,values=df_pie['donation_sum'],
                    name='Spenden',sort=False),1,2)
        
    piecharts.update_traces(hole=.4, hovertemplate ="%{label}: <br>%{percent} </br> %{value}")

    piecharts.update_layout(
        legend_title_text='Spendenkategorie',
        title={
            'text': "Verteilung von Spenden und -summen",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        legend_x=0.44,
        # Add annotations in the center of the donut pies.
        annotations=[dict(text='Spenden', x=0.0, y=0.5, font_size=20, showarrow=False),
                    dict(text='Summen', x=1.0, y=0.5, font_size=20, showarrow=False)])
    

    return linechart,df.to_dict('records'),piecharts

money = dash_table.FormatTemplate.money(2)
columns = [
    dict(id='donated_at', name='Zeitpunkt'),
    dict(id='donated_amount_in_Euro', name='Spende', type='numeric', format=Format(symbol=Symbol.yes, symbol_suffix=' €', decimal_delimiter=',').scheme('f').precision(2))
]

footer_text = '''
© dor_sax & nib0t. Source code available [on GitHub](https://github.com/dorsax/betterplace_fetch)
'''
app.layout = html.Div([
    html.Div([
        html.Button("Reload", id="button_reload", 
        ),
        html.A(html.Button('Home'),
            href='https://www.xn--lootfrdiewelt-0ob.de/'),
        html.A(html.Button('Source Code'),
            href='https://github.com/dorsax/betterplace_fetch', target="_blank"),

    ],),
    dcc.Graph(
        id='Komplettgrafik',
        #figure=fig
    ),
    dcc.Graph(
        id="10_100_k_pie"
    ),
    html.H4(
        id='Title_Table',
        children='Letzte Spenden'
    ),
    dash_table.DataTable(
        id='Komplettabelle',
        #data=df.to_dict('records')
        columns=columns,
        page_size=20,
    ),
    html.Footer(
        dcc.Markdown(footer_text)        
    ),
])

app.title='analytics'
app._favicon=("favicon.png")
if __name__ == '__main__':
    app.run_server(debug=True,host="0.0.0.0")
