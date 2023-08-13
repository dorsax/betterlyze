from typing import OrderedDict
from django_plotly_dash import DjangoDash
import dash
from dash import dash_table
from dash import dcc
from pandas import Timestamp as ts
from dash.dependencies import Input, Output
from datetime import timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dash_table.Format import Format, Group, Prefix, Scheme, Symbol
from dash import dash_table
import dash_daq as daq
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html
from functools import cache
from django.utils import timezone

from .models import Event, Donation


external_stylesheets = ['https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css']

app = DjangoDash('comparison',external_stylesheets=external_stylesheets)

# rewritten for django context
@cache
def process_event (event,lastdonationtimestamp):
    del lastdonationtimestamp
    starttime = ts(event.start)
    endtime = ts(event.end)
    df = pd.DataFrame.from_records(Donation.objects.filter(event_id=event.id).values())
    df['donated_amount_in_Euro'] = df.donated_amount_in_cents.div(100).round(2)
    df['cumulated_sum'] = df.donated_amount_in_Euro.cumsum(axis = 0, skipna = True)
    
    template_pie= {'donations': [0,0,0,0],'categories':['bis 10 €','10 bis 100 €','100 bis 1000 €', 'über 1000 €'],'donation_sum':[0,0,0,0]}
    maxtime=df['donated_at'].max()

    if (maxtime>endtime):
        maxtime=endtime
    # 1st hour
    
    df.donated_at=df.donated_at.dt.tz_convert(timezone.localtime().tzinfo)
    ts_template = pd.date_range(starttime,maxtime,freq='H').tz_convert(timezone.localtime().tzinfo)
    template_df = pd.DataFrame ({'timestamps' : ts_template})
    template_df['donors']=0
    template_df['donations']=0
    template_times = template_df.to_dict()

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
    return df,df_time,df_pie

def compare_events (events):
    df_all = list()
    df_times = list()
    df_pies = list()
    event_to_be_compared_with = events[0]
    for event in events :

        df, df_time, df_pie = process_event(event, Donation.objects.filter(event_id=event.id).latest('donated_at'))
        time_between_events = ts(event_to_be_compared_with.start)-ts(event.start)
        # ensure to not modify any cached dataframes to avoid calculating back more and more

        df2=df.copy()
        df_time2=df_time.copy()
        df_pie2=df_pie.copy()
        df2['donated_at']=df2['donated_at']+time_between_events
        df_time2['timestamps']=df_time2['timestamps']+time_between_events

        df_all.append(df2)
        df_times.append(df_time2)
        df_pies.append(df_pie2)
    
    return events, df_all, df_times, df_pies

def query_events( event_id_new, event_ids_old = list()):
    try:
        events = list()
        events.append(Event.objects.get(pk=event_id_new))
        try:
            for event_id in event_ids_old:
                events.append(Event.objects.get(pk=event_id))
        except Exception as exc:
            pass
        return compare_events(events)
    except Exception as exc:
        raise PreventUpdate

@app.callback(
    Output(component_id='event_id_old', component_property='options'),
    Output(component_id='event_id_new', component_property='options'),
    Input(component_id='event_id_old', component_property='value'),
    Input(component_id='event_id_new', component_property='value'),
)
def update_dropdowns (event_id_old, event_id_new):
    all_events = Event.objects.all().values('id','description')
    all_events_dropdown = []
    old_events_dropdown = []
    for event in all_events:
        dropdown_item = {
            'label' : event['description'],
            'value' : event['id'],
        }
        if (event['id'] == event_id_new):
            all_events_dropdown.append(dropdown_item)
        else:
            all_events_dropdown.append(dropdown_item)
            old_events_dropdown.append(dropdown_item)

    return old_events_dropdown, all_events_dropdown

@app.callback(
    Output(component_id='graphs', component_property='style'),
    Output(component_id='sums', component_property='style'),
    Input(component_id='event_id_new', component_property='value'),
)
def show_hide_graphs (event_id_old):
    style = {'display': 'none'}
    if event_id_old is None:
        style = {'display': 'none'}
    else:
        style = {'display': 'block'}
    return style, style


@app.callback(
    Output(component_id='loading-output-1', component_property='children'),
    Output(component_id='spendensumme_new', component_property='children'),
    Output(component_id='Spendenstaende', component_property='data'),
    Output(component_id='Komplettgrafik', component_property='figure'),
    Output(component_id='Kompletttabelle', component_property='data'),
    Output(component_id='10_100_k_pie', component_property='figure'),
    Output(component_id='hourly_donations', component_property='figure'),
    Output(component_id='hourly_donors', component_property='figure'),
    Input(component_id='event_id_old', component_property='value'),
    Input(component_id='event_id_new', component_property='value'),
    Input('refresh_switch', 'on'),
    Input('button_reload', 'n_clicks'),
    Input('interval-component', 'n_intervals'),
)
def update_app(
            event_id_old, 
            event_id_new, 
            on,
            n_clicks=0,
            n_intervals=0,
            ):

    event_ids_old = list()
    event_ids_old=event_id_old

    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'].split('.')[0]== 'refresh_switch':
            raise PreventUpdate
        if ((ctx.triggered[0]['prop_id'].split('.')[0]== 'interval-component') and (on==False)):
            raise PreventUpdate
    except Exception as e:
        raise PreventUpdate

    events, df_all, df_times, df_pies = query_events (event_id_new=event_id_new, event_ids_old=event_ids_old)
    
    data_linechart=list()
    data_hourlydonor= list()
    data_hourlydonations = list()
    maxsums=OrderedDict(
        [
            ("Event", []),
            ("Summe", []),
        ]
    )
    for index in range(0,len(events)):
        maxsums["Event"].append(events[index].description)
        maxsums["Summe"].append(df_all[index]["cumulated_sum"].max())
        data_linechart.append(
             go.Scatter(name=events[index].description,
                x=df_all[index]["donated_at"],
                y=df_all[index]["cumulated_sum"],),
        )
        data_hourlydonor.append(
            go.Bar(name=events[index].description, x=df_times[index]['timestamps'], y=df_times[index]['donors'])
        )
        data_hourlydonations.append(
            go.Bar(name=events[index].description, x=df_times[index]['timestamps'], y=df_times[index]['donations']),
        )
    linechart = go.Figure(data = data_linechart)
    hourlydonor = go.Figure(data=data_hourlydonor)
    hourlydonations = go.Figure(data=data_hourlydonations)
    
    
    # change the graph to only show the current maximum time
    maxentry=df_all[0]["donated_at"].max()
    if (ts(events[0].end)>=maxentry) and (maxentry>=ts(events[0].start)):
        linechart.update_xaxes(
            range=[ts(events[0].start),maxentry],
        )
    else:
        linechart.update_xaxes(
            range=[ts(events[0].start),ts(events[0].end)],
        )
    linechart.update_layout(
        title={
            'text': "Spendenverlauf",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        })

    hourlydonor.update_layout(
        title={
            'text': "Spender",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        barmode='group',)

    hourlydonations.update_layout(
        title={
            'text': "Spenden",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        barmode='group',)
    
    
    labels=df_pies[0]['categories']
    piecharts = make_subplots (rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
    piecharts.add_trace (go.Pie(labels=labels,values=df_pies[0]['donations'],
                    name='Spender',sort=False),1,1)
    piecharts.add_trace (go.Pie(labels=labels,values=df_pies[0]['donation_sum'],
                    name='Spenden',sort=False),1,2)
        
    piecharts.update_traces(hole=.4, hovertemplate ="%{label}: <br>%{percent} </br>%{value}")

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
    
    maxsum=df_all[0]["cumulated_sum"].max()
    maxsumstr = f"{maxsum:.2f}"+" €"




    return "",maxsumstr, pd.DataFrame(maxsums).to_dict('records') ,linechart,df_all[0].to_dict('records'),piecharts, hourlydonations, hourlydonor
    

description = '''
# Beschreibung

Die hier dargestellten Daten kommen von der Betterplace-API und stellen die Verläufe der gewählten Events dar.
Die Ringdiagramme beziehen sich nur auf das aktuelle Event.

## Bedienung 

In den oberen beiden Dropdowns kann ausgewählt werden, welches Event angezeigt und verglichen werden soll. \
Die einzenen Grafiken können gezoomt werden.
Doppelklick setzt den Zoom zurück.
Die obere Grafik setzt sich derzeit zu weit zurück, weshalb auf den Reload-Button geklickt werden muss. 
Der **Reload-Button** aktualisiert alle Grafiken. **Ein Reload der Seite über den Browser selbst setzt auch den Inhalt der DropDown-Felder zurück*
Die Daten werden im Hintergrund alle 5 Minuten geholt, und im Frontend automatisch alle 3 Minuten aktualisiert. 
Dabei werden aktuell auch alle Ansichten zurückgesetzt.
Der Autoreload kann ausgeschaltet werden.

'''

@app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    [State("offcanvas", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open

def buildMenu ():
    menu_items_static = [
        # dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem(
                daq.BooleanSwitch(
                    id='refresh_switch',
                    on=True,
                    label="Autoreload",
                    labelPosition="left",
                ),
            ),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem("Hilfe", id='open-offcanvas', n_clicks=0, ),
    ]
    return menu_items_static
    menu_items_dynamic = []
    events = Event.objects.all().order_by('-start')
    for event in events:
        menu_items_dynamic.append(
            dbc.DropdownMenuItem (
                event.description,
                href = f'/analyse/{event.id}',
                external_link=True,
            )
        )

    return menu_items_dynamic + menu_items_static

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("Analyse", href="#"),
                dbc.Row(
                    [
                        dbc.Col(
                                dcc.Loading(
                                    id="loading-1",
                                    type="default",
                                    children=html.Div(id="loading-output-1",style = {'display': 'none'})
                                ),
                        ),
                        dbc.Col(),
                        dbc.Col(
                            dbc.Button(
                                "Reload", id="button_reload",color="primary", n_clicks=0, className="ms-2"
                            ),
                            
                        ),
                        dbc.Col( dbc.DropdownMenu(
                            id = 'eventmenu',
                            label="Menü",
                            children=buildMenu(),
                            align_end=True
                        )),
                    ],
                    align="center",
                ),
        ]
    ),
    className="mb-5",
    sticky="top",
)


app.layout = html.Div([
    navbar,
    html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.Label ("Aktuelles Event", id='event_id_new_Label'),
                                width="2",),
                dbc.Col(dcc.Dropdown(id='event_id_new',
                                clearable=False,),
                                width="3",), 
                dbc.Col(html.Div([
                    html.H4 (
                            id='spendensumme_new',
                            children="",
                        ),
                ], id = 'sums'),),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Label ("Vergangenes Event", id='event_id_old'),
                                width="2",),
                dbc.Col(dcc.Dropdown(id='event_id_old',
                                    multi=True,),
                                width="3",), 
                dbc.Col(html.Div([
                    html.H4 (
                            id='spendensumme_old',
                            children="",
                        ),
                ], id = 'sums'),),
            ]
        ),
    ], ),
    html.Div(
    [
        dbc.Offcanvas(
            dcc.Markdown(description),
            id="offcanvas",
            title="Hilfe und Über",
            is_open=False,
            placement='end',
        ),
    ]),
    html.Div([
                dcc.Graph(
                    id='Komplettgrafik',
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
                dbc.Row([
                    dbc.Col(html.H4 ("Endstände"),
                                        width="6",
                    ),
                    dbc.Col(html.H4 ("Aktuelles Event"),
                                        width="6",
                    ),
                ]),
                dbc.Row(
                    [
                        dbc.Col(
                            dash_table.DataTable(
                                id='Spendenstaende',
                                columns=[
                                    dict(id='Event', name='Event', ),
                                    dict(id='Summe', name='Summe', type='numeric', format=Format(symbol=Symbol.yes, symbol_suffix=' €', decimal_delimiter=',').scheme('f').precision(2))
                                ],
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'Event'},
                                        'textAlign': 'left'
                                    }
                                ],
                            )           
                        ),
                        dbc.Col(dash_table.DataTable(
                                    id='Kompletttabelle',
                                    columns=[
                                            dict(id='donated_at', name='Zeitpunkt'),
                                            dict(id='donated_amount_in_Euro', name='Spende', type='numeric', format=Format(symbol=Symbol.yes, symbol_suffix=' €', decimal_delimiter=',').scheme('f').precision(2))
                                        ],
                                    style_cell_conditional=[
                                        {'if': {'column_id': 'donated_at'},
                                        'width': '120px'},
                                        {'if': {'column_id': 'donated_amount_in_Euro'},
                                        'width': '240px'},
                                    ],
                                    page_size=20,
                        ),
                        width="6",),
                    ]
                ),
                
            ],id='graphs',),
    dcc.Interval(
        id='interval-component',
        interval=3*60*1000, # in milliseconds
        n_intervals=0,
    ),
])

if __name__ == '__main__':
    app.run_server(debug=True)
