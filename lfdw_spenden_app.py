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

config_filename = 'config.yml'
configstream = open(os.path.dirname(os.path.realpath(__file__))+os.path.sep+config_filename, 'r')
config = yaml.safe_load (configstream)
address = config["database"].get('address')
username = config["database"].get('username')
password = config["database"].get('password')
database = config["database"].get('database')
startdate= dt.fromisoformat(config.get('starttime'))
enddate= dt.fromisoformat(config.get('endtime'))

connection = setup.create_connection(username=username,password=password,address=address,database=database)

df = pd.read_sql(sql='SELECT donated_at,donated_amount_in_cents FROM donations ORDER BY donated_at ASC',con=connection,parse_dates=['donated_at'])
df['donated_amount_in_Euro'] = df.donated_amount_in_cents.div(100).round(2)
df['cumulated_sum'] = df.donated_amount_in_Euro.cumsum(axis = 0, skipna = True)

fig = px.line(data_frame=df, x="donated_at", y="cumulated_sum",
            hover_data=['donated_at','cumulated_sum'],
            color_discrete_sequence=["red"],
            range_x=[startdate,enddate])

def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in ['Spendenzeitpunkt','Euro']])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in [0,2]
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])

app = dash.Dash(__name__)
from dash.dash_table.Format import Format, Group, Prefix, Scheme, Symbol


from dash import dash_table
money = dash_table.FormatTemplate.money(2)
columns = [
    dict(id='donated_at', name='Zeitpunkt'),
    dict(id='donated_amount_in_Euro', name='Spende', type='numeric', format=Format(symbol=Symbol.yes, symbol_suffix=' €', decimal_delimiter=',').scheme('f').precision(2))
]
app.layout = html.Div([
    dcc.Graph(
        id='Zeittabelle',
        figure=fig
    ),
    html.H4(children='Letzte Spenden'),
    dash_table.DataTable(
        data=df.to_dict('records'),
        #columns=[{'id': 'donated_at', 'name': 'Spendenzeit'}, {'id': 'donated_amount_in_Euro', 'name': 'Spende in Euro'},],
        columns=columns,
        page_size=20,
    )
    #generate_table(df)

])

if __name__ == '__main__':
    app.run_server(debug=True)
