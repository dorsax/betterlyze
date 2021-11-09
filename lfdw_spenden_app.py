import dash
import yaml
import os
import setup
from dash import dash_table
from dash import dcc
from dash import html
from pandas import Timestamp as ts
from dash.dependencies import Input, Output
from datetime import timedelta
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
current_event = config["current_year"].get('event')
last_event = config["past_year"].get('event')
startdate= ts(config["current_year"].get('starttime'))
enddate= ts(config["current_year"].get('endtime'))
startdate_last= ts(config["past_year"].get('starttime'))
enddate_last= ts(config["past_year"].get('endtime'))


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})

def process_data (dataframe):
    df=dataframe
    df['donated_amount_in_Euro'] = df.donated_amount_in_cents.div(100).round(2)
    df['cumulated_sum'] = df.donated_amount_in_Euro.cumsum(axis = 0, skipna = True)
    
    template_pie= {'donations': [0,0,0,0],'categories':['bis 10 €','10 bis 100 €','100 bis 1000 €', 'über 1000 €'],'donation_sum':[0,0,0,0]}
    maxtime=df['donated_at'].max()
    if (maxtime>enddate):
        maxtime=enddate
    # 1st hour
    template_times = {'timestamps': [ts(startdate.year,startdate.month,startdate.day,startdate.hour,0,0,0)], 'donors': [0], 'donations': [0]}
    currenttime = startdate #
    count=1
    while (currenttime <= maxtime):
        currenttime = startdate+timedelta(hours=count)
        template_times['timestamps'].append(currenttime)
        template_times['donors'].append(0)
        template_times['donations'].append(0)
        count+=1
        if (count>1000):
            exit("Fatal error while computing timetables!")

    haventfoundit = True

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

        if (False):#row['donated_at']<template_times['timestamps'][1]):
            template_times['donors'][0]+=1
            template_times['donations'][0]+=row['donated_amount_in_Euro']
        else:
            for index2 in range (0,len(template_times['timestamps'])-1):
                if ((row['donated_at']>=template_times['timestamps'][index2]) and (row['donated_at']<=template_times['timestamps'][index2+1])):
                    if (haventfoundit):
                        haventfoundit=False
                    template_times['donors'][index2]+=1
                    template_times['donations'][index2]+=row['donated_amount_in_Euro']
                    break
        if (haventfoundit):
            haventfoundit=False
            template_times['donors'][len(template_times['timestamps'])-1]+=1
            template_times['donations'][len(template_times['timestamps'])-1]+=row['donated_amount_in_Euro']

    df=df.sort_values(by='donated_at', ascending=False) # newest to earliest
    df_time = pd.DataFrame(data=template_times)        
    df_pie= pd.DataFrame(data=template_pie)
    return df,df_pie,df_time

@cache.memoize(timeout=CACHE_TIME)
def query_data():
    connection = setup.create_connection(username=username,password=password,address=address,database=database)

    df_old = pd.read_sql(sql='SELECT donated_at,donated_amount_in_cents FROM donations WHERE event_id=%s ORDER BY donated_at ASC',params=[last_event],con=connection,parse_dates=['donated_at'])
    df_new = pd.read_sql(sql='SELECT donated_at,donated_amount_in_cents FROM donations WHERE event_id=%s ORDER BY donated_at ASC',params=[current_event],con=connection,parse_dates=['donated_at'])
    
    time_between_events=startdate-startdate_last
    df_old,df_pie,df_time=process_data(df_old)

    df_old['donated_at']=df_old['donated_at']+time_between_events
    #df_time['timestamps']=df_time['timestamps']+time_between_events
    
    df_new,df_pie,df_time_new=process_data(df_new)
    
    return df_new,df_pie,df_time_new,df_old,df_time



@app.callback(
    Output(component_id='Komplettgrafik', component_property='figure'),
    Output(component_id='Komplettabelle', component_property='data'),
    Output(component_id='10_100_k_pie', component_property='figure'),
    Output(component_id='hourly_donations', component_property='figure'),
    Output(component_id='hourly_donors', component_property='figure'),
    Input('button_reload', 'n_clicks'),
)
def update_app(n_clicks):
    
    df,df_pie,df_time,df_old,df_time_old = query_data()

    # linechart = px.line(data_frame=df, x="donated_at", y="cumulated_sum",
    #             hover_data=['donated_at','cumulated_sum'],
    #             labels={
    #                 "donated_at":"Zeitpunkt der Spende",
    #                 "cumulated_sum" : "Spendenstand"
    #             },
    #             color_discrete_sequence=["red"],
    #             range_x=[startdate,enddate],
    #             title="Spendenverlauf")
    # 
    
    linechart = go.Figure( data=[
        go.Scatter(name='2021',
            x=df["donated_at"],
            y=df["cumulated_sum"],),
        go.Scatter(name='2020',
            x=df_old["donated_at"],
            y=df_old["cumulated_sum"],),
    ])
    # change the graph to only show the current maximum time
    maxentry=df["donated_at"].max()
    if (enddate>=maxentry) and (maxentry>=startdate):
        linechart.update_xaxes(
            range=[startdate,maxentry],
        )
    else:
        linechart.update_xaxes(
            range=[startdate,enddate],
        )
    linechart.update_layout(
        title={
            'text': "Spendenverlauf",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        })
    hourlydonor = go.Figure(data=[
        go.Bar(name='2021', x=df_time['timestamps'], y=df_time['donors']),
        go.Bar(name='2020', x=df_time_old['timestamps'], y=df_time_old['donors']),        
    ])
    hourlydonor.update_layout(
        title={
            'text': "Spender",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        })
    
    hourlydonations = go.Figure(data=[
        go.Bar(name='2021', x=df_time['timestamps'], y=df_time['donations']),
        go.Bar(name='2020', x=df_time_old['timestamps'], y=df_time_old['donations']),
    ])
    hourlydonations.update_layout(
        title={
            'text': "Spenden",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        })
    
    
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
    
    return linechart,df.to_dict('records'),piecharts, hourlydonations, hourlydonor

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
        # html.A(html.Button('Home'),
        #     href='https://www.xn--lootfrdiewelt-0ob.de/'),
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
    dcc.Graph(
        id="hourly_donations"
    ),
    dcc.Graph(
        id="hourly_donors"
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
