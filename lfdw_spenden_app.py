import dash
import yaml
import os
import setup
from dash import dash_table
from dash import dcc
from dash import html
from datetime import datetime as dt
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from dash.dash_table.Format import Format, Group, Prefix, Scheme, Symbol
from dash import dash_table

config_filename = 'config.yml'
configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
config = yaml.safe_load (configstream)
address = config["database"].get('address')
username = config["database"].get('username')
password = config["database"].get('password')
database = config["database"].get('database')
startdate= dt.fromisoformat(config.get('starttime'))
enddate= dt.fromisoformat(config.get('endtime'))


app = dash.Dash(__name__)

@app.callback(
    Output(component_id='Komplettgrafik', component_property='figure'),
    Output(component_id='Komplettabelle', component_property='data'),
    Input('button_reload', 'n_clicks'),
)
def update_app(n_clicks):
    connection = setup.create_connection(username=username,password=password,address=address,database=database)

    df = pd.read_sql(sql='SELECT donated_at,donated_amount_in_cents FROM donations ORDER BY donated_at ASC',con=connection,parse_dates=['donated_at'])
    df['donated_amount_in_Euro'] = df.donated_amount_in_cents.div(100).round(2)
    df['cumulated_sum'] = df.donated_amount_in_Euro.cumsum(axis = 0, skipna = True)
    
    fig = px.line(data_frame=df, x="donated_at", y="cumulated_sum",
                hover_data=['donated_at','cumulated_sum'],
                color_discrete_sequence=["red"],
                range_x=[startdate,enddate])
    #fig.update_layout(transition_duration=500)
    df=df.sort_values(by='donated_at', ascending=False)
    return fig,df.to_dict('records')

money = dash_table.FormatTemplate.money(2)
columns = [
    dict(id='donated_at', name='Zeitpunkt'),
    dict(id='donated_amount_in_Euro', name='Spende', type='numeric', format=Format(symbol=Symbol.yes, symbol_suffix=' €', decimal_delimiter=',').scheme('f').precision(2))
]
app.layout = html.Div([
    html.Button("Reload", id="button_reload"),
    dcc.Graph(
        id='Komplettgrafik',
        #figure=fig
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
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
