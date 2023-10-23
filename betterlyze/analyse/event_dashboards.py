from typing import OrderedDict
from django_plotly_dash import DjangoDash
import dash
from dash import dash_table
from dash import dcc
from pandas import Timestamp as ts
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash.dash_table.Format import Format, Symbol
import dash_daq as daq
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html
from functools import cache
from django.utils import timezone
from django.conf import settings

from .models import Event, Donation


external_stylesheets = [settings.BOOTSTRAP5['css_url'],
                        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.2/font/bootstrap-icons.css" ,
                        "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css", # fixes some issues with dash compoments
                        ]

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

    maxtime=df['donated_at'].max()

    if (maxtime>endtime):
        maxtime=endtime

    df.donated_at=df.donated_at.dt.tz_convert(timezone.localtime().tzinfo)
    ts_template = pd.date_range(starttime,maxtime,freq='H').tz_convert(timezone.localtime().tzinfo)
    ts_label = list(range(len(ts_template)-1))
    bar_count = df["donor"].groupby(pd.cut(df['donated_at'], ts_template, labels=ts_label), observed=False).count()
    bar_sum = df["donated_amount_in_Euro"].groupby(pd.cut(df['donated_at'], ts_template, labels=ts_label), observed=False).sum()
    df_time = pd.concat([bar_count,bar_sum], axis=1)
    
    donation_ranges = [0,1000,10000,100000,1000000000000000]
    donation_labels = ['<= 10 €','<= 100 €','<= 1000 €','> 1000 €']
    pie_count = df["donor"].groupby(pd.cut(df['donated_amount_in_cents'], donation_ranges, labels=donation_labels), observed=False).count()
    pie_sum = df["donated_amount_in_Euro"].groupby(pd.cut(df['donated_amount_in_cents'], donation_ranges,labels=donation_labels), observed=False).sum()
    df_pie = pd.concat([pie_count,pie_sum], axis=1)

    df=df.sort_values(by='donated_at', ascending=False) # newest to earliest
    return df,df_time,df_pie

def compare_events (events: list):

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
        except Exception:
            pass
        return compare_events(events)
    except Exception as exc:
        raise PreventUpdate from exc

@app.expanded_callback(
    Output(component_id='events_dropdown', component_property='options'),
    Output(component_id='current_event_dropdown', component_property='options'),
    Output(component_id='events_dropdown', component_property='value'),
    Output(component_id='current_event_dropdown', component_property='value'),
    Input(component_id='events_dropdown', component_property='value'),
    Input(component_id='current_event_dropdown', component_property='value'),    
)
def update_dropdowns (event_ids, current_event, session_state=None, **kwargs):

    # Session handling
    if session_state is None:
        raise NotImplementedError("Cannot handle a missing session state")
    events_to_compare = session_state.get('to_compare', list())
    session_state['to_compare'] = events_to_compare

    if event_ids is None :
        if len (session_state['to_compare']) > 0:
            event_ids = session_state['to_compare']
    else:
        session_state['to_compare'] = event_ids
    

    # Dropdown options
    all_events = Event.objects.all().values('id','description')
    current_event_dropdown_options = []
    events_dropdown_options = []
    for event in all_events:
        dropdown_item = {
            'label' : event['description'],
            'value' : event['id'],
        }
        if event['id'] in session_state['to_compare']:
            current_event_dropdown_options.append(dropdown_item)
        events_dropdown_options.append(dropdown_item)

    if not (current_event in session_state['to_compare']) :
        current_event = None

    if (current_event is None) and (len(session_state["to_compare"])>0): current_event = session_state["to_compare"][0]

    return events_dropdown_options, current_event_dropdown_options, event_ids, current_event

@app.callback(
    Output(component_id='graphs', component_property='style'),
    Output(component_id='sums', component_property='style'),
    Input(component_id='current_event_dropdown', component_property='value'),
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
    Output(component_id='Spendenstaende', component_property='data'),
    Output(component_id='Komplettgrafik', component_property='figure'),
    Output(component_id='10_100_k_pie', component_property='figure'),
    Output(component_id='hourly_donations', component_property='figure'),
    Output(component_id='hourly_donors', component_property='figure'),
    Input(component_id='events_dropdown', component_property='value'),
    Input(component_id='current_event_dropdown', component_property='value'),
    Input('refresh_switch', 'on'),
    Input('button_reload', 'n_clicks'),
    Input('interval-component', 'n_intervals'),
)
def update_app(
            event_id_old,
            event_id_new,
            on,
            n_clicks=0, # pylint: disable=unused-variable
            n_intervals=0, # pylint: disable=unused-variable
            ):

    event_ids_old = list()
    event_ids_old=event_id_old
    event_ids_old.remove(event_id_new) # TODO: refactor code to better reflect whats happening

    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'].split('.')[0]== 'refresh_switch':
            raise PreventUpdate
        if ((ctx.triggered[0]['prop_id'].split('.')[0]== 'interval-component') and (on==False)):
            raise PreventUpdate
    except Exception as e:
        raise PreventUpdate from e

    events, df_all, df_times, df_pies = query_events (event_id_new=event_id_new, event_ids_old=event_ids_old)
    
    # create sum table
    maxsums=OrderedDict(
        [
            ("Event", []),
            ("Summe", []),
        ]
    )
    for index in range(0,len(events)):  # pylint: disable=consider-using-enumerate
        maxsums["Event"].append(events[index].description)
        maxsums["Summe"].append(df_all[index]["cumulated_sum"].max())
  
    # create line chart

    data_linechart=list()
    for index in range(0,len(events)): # pylint: disable=consider-using-enumerate
        data_linechart.append(
             go.Scatter(name=events[index].description,
                x=df_all[index]["donated_at"],
                y=df_all[index]["cumulated_sum"],),
        )
    
    linechart = go.Figure(data = data_linechart)
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

    # create pie charts

    labels=df_pies[0].index.categories.tolist()
    piecharts = make_subplots (rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
    piecharts.add_trace (go.Pie(labels=labels,values=df_pies[0]['donor'],
                    name='Spender',sort=False),1,1)
    piecharts.add_trace (go.Pie(labels=labels,values=df_pies[0]['donated_amount_in_Euro'],
                    name='Spenden',sort=False),1,2)

    piecharts.update_traces(hole=.4, hovertemplate ="%{label}: <br>%{percent} </br>%{value}")

    piecharts.update_layout(
        legend_title_text='Spendenkategorie',
        title={
            'text': f'Verteilung von Spenden und -summen {events[0].description}',
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        legend_x=0.44,
        # Add annotations in the center of the donut pies.
        annotations=[dict(text='Spenden', x=0.0, y=0.5, font_size=20, showarrow=False),
                    dict(text='Summen', x=1.0, y=0.5, font_size=20, showarrow=False)])


    # create bar charts 

    data_hourlydonor= list()
    data_hourlydonations = list()
    for index in range(0,len(events)):  # pylint: disable=consider-using-enumerate
        data_hourlydonor.append(
            go.Bar(name=events[index].description, x=df_times[index].index.categories.tolist(), y=df_times[index]['donor'])
        )
        data_hourlydonations.append(
            go.Bar(name=events[index].description, x=df_times[index].index.categories.tolist(), y=df_times[index]['donated_amount_in_Euro']),
        )

    hourlydonor = go.Figure(data=data_hourlydonor)
    hourlydonations = go.Figure(data=data_hourlydonations)
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
    
    # return components

    return "", pd.DataFrame(maxsums).to_dict('records'),linechart , piecharts , hourlydonor, hourlydonations


description = '''
# Beschreibung

Die hier dargestellten Daten kommen von der Betterplace-API und stellen die Verläufe der gewählten Events dar.
Die Ringdiagramme beziehen sich nur auf das aktuelle Event.

## Bedienung

In den oberen beiden Dropdowns kann ausgewählt werden, welches Event angezeigt und verglichen werden soll.

Die einzenen Grafiken können gezoomt werden, Doppelklick setzt den Zoom zurück.

Die obere Grafik setzt sich derzeit zu weit zurück, weshalb auf den Reload-Button geklickt werden muss.
Der **Reload-Button** aktualisiert alle Grafiken. **Ein Reload der Seite über den Browser selbst setzt auch den Inhalt der DropDown-Felder zurück*

Die Daten werden im Hintergrund alle 5 Minuten geholt, und im Frontend automatisch alle 3 Minuten aktualisiert.
Dabei werden aktuell auch alle Ansichten zurückgesetzt.

Der Autoreload kann in der Einstellungen ausgeschaltet werden.

#### Hinweis zu Spenden und Spendern

Die Zeitabschnitte richten sich nach der Länge des aktuellen Events und zeigen im Gegensatz zum Spendenverlauf nur die Daten innerhalb der x-ten Stunde an.
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

dropdownmenu = dbc.DropdownMenu(
                            in_navbar=True,
                            id = 'eventmenu',
                            label=html.Span(className="bi bi-gear"),
                            color="info",
                            caret=False,
                            children=[                        
                                dbc.DropdownMenuItem(dbc.Button("Reload", 
                                                                id="button_reload",
                                                                color="info",
                                                                n_clicks=0,
                                                                className="ms-2"
                                                    ),
                                ),        
                                # pylint: disable=not-callable
                                dbc.DropdownMenuItem(
                                        daq.BooleanSwitch(
                                            id='refresh_switch',
                                            on=True,
                                            label="Autoreload",
                                            labelPosition="left",
                                        ),
                                    ),
                                # pylint: enable=not-callable
                                dbc.DropdownMenuItem(divider=True),
                                dbc.DropdownMenuItem("Hilfe", id='open-offcanvas', n_clicks=0, ),
                            ],
)

loading_asset =  dcc.Loading(
            id="loading-1",
            type="default",
            children=html.Div(id="loading-output-1"),
            # fixes the loading asset being stuck inside the dropdownmenu
            style= {
                "margin-right": "50px"
            },
        )

navbar = dbc.Nav(
    [
        loading_asset,
        dropdownmenu,
    ],
    fill=True,
    horizontal='end',
    class_name="sticky-top",
)


app.layout = html.Div([
    navbar,
    html.Div(id='test'),
    html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                  [
                    dbc.Row([
                        dbc.Col(html.Label ("Zu vergleichende Events", id='events_Label'),
                                width="5",),
                        dbc.Col(dcc.Dropdown(id='events_dropdown',
                                    multi=True,),
                                width="5",),
                    ]),
                    dbc.Row([
                        dbc.Col(html.Label ("Referenzevent", id='current_event_Label'),
                                width="5",),
                        dbc.Col(dcc.Dropdown(id='current_event_dropdown',
                                clearable=False,),
                                width="5",),
                    ]),
                  ],
                  width=6, 
                ),
                dbc.Col(
                            dash_table.DataTable(
                                style_as_list_view=True,
                                id='Spendenstaende',
                                columns=[
                                    dict(id='Event', name='Event', ),
                                    dict(id='Summe', name='Summe', type='numeric', format=Format(symbol=Symbol.yes, symbol_suffix=' €', decimal_delimiter=',', group_delimiter='.').scheme('f').precision(2).group(True))
                                ],
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'Event'},
                                        'textAlign': 'left'
                                    }
                                ],
                            ),
                        width=6,
                        className="dbc",
                ),
            ]
        ),
        dbc.Row(
            [
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

            ],id='graphs',),
    dcc.Interval(
        id='interval-component',
        interval=3*60*1000, # in milliseconds
        n_intervals=0,
    ),

])
