import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # This is needed for Render deployment

# Use relative file paths
current_dir = os.path.dirname(os.path.abspath(__file__))
merged_df = pd.read_csv(os.path.join(current_dir, "merged_dashboard_data.csv"))
health_df = pd.read_csv(os.path.join(current_dir, "world_health_indicators.csv"))

# Load mental health survey data
occ_data_full = pd.read_csv(os.path.join(current_dir, "mental_health_survey_2020.csv"))
occ_data_full["Timestamp"] = pd.to_datetime(occ_data_full["Timestamp"])
occ_data_full["year"] = occ_data_full["Timestamp"].dt.year

# Choropleth Map
map_fig = px.choropleth(
    merged_df,
    locations="country_code",
    color="pct_treatment",
    hover_name="country",
    custom_data=["life_expect", "pct_treatment"],
    color_continuous_scale=[[0, '#99ccff'], [0.5, '#3366cc'], [1.0, '#003366']],
    projection="natural earth",
    title="Global Mental Health Treatment Rates"
)
map_fig.update_layout(
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="white",
    coloraxis_colorbar=dict(
        title="Rate (%)",
        len=0.8,
        thickness=16,
        y=0.5,
        x=0.87
    ),
    height=440
)

# Custom hover template
map_fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>" +
                  "Mental Health Treatment Rate: %{customdata[1]:.1f}%<br>" +
                  "Life Expectancy: %{customdata[0]:.1f} years<br><extra></extra>"
)

# Generate pictograph using actual silhouette images
def render_image_pictograph(count, filled_src, unfilled_src, label_text, percentage, country):
    icons = []
    for i in range(10):
        img_src = filled_src if i < count else unfilled_src
        icons.append(html.Img(src=img_src, style={"height": "65px", "margin": "0 5px"}))
    return html.Div([
        html.Div([
            html.Div(label_text, style={"textAlign": "center", "color": "white", "fontFamily": "Arial", "fontSize": "16px"}),
            html.Div(f"({percentage:.1f}%)", style={"textAlign": "center", "color": "white", "fontFamily": "Arial", "fontSize": "13px", "marginBottom": "8px"})
        ]),
        html.Div(icons, style={"display": "flex", "justifyContent": "center"})
    ], style={"backgroundColor": "#1976d2", "borderRadius": "10px", "padding": "20px 15px", "width": "100%", "boxSizing": "border-box"}, key=f"{label_text}-{count}")

# Dropdown options
country_options = [{'label': c, 'value': c} for c in sorted(merged_df['country'].unique())]

# Layout
app.layout = html.Div([
    html.H1("GLOBAL MENTAL HEALTH INDICATORS 2020", style={"textAlign": "center", "color": "white", "padding": "10px", "fontFamily": "Arial"}),

    html.P("You can change dashboard views using the dropdown or by clicking a country on the map.", style={"textAlign": "center", "color": "white", "fontSize": "14px"}),

    dcc.Dropdown(
        id="country-dropdown",
        options=country_options,
        value="United States",
        placeholder="Select a country",
        style={"width": "50%", "margin": "auto", "marginBottom": "10px"}
    ),

    html.Div([
        html.Div([dcc.Graph(id="choropleth-map", figure=map_fig)], style={"width": "58%", "padding": "5px"}),
        html.Div([
            dcc.Graph(id="line-chart", style={"height": "220px", "marginBottom": "10px"}),
            dcc.Graph(id="histogram", style={"height": "220px"})
        ], style={"width": "40%", "padding": "5px"})
    ], style={"display": "flex", "flexDirection": "row"}),

    html.Div([
        html.Div(id="coping-pictograph", style={"width": "48%"}),
        html.Div(id="history-pictograph", style={"width": "48%"})
    ], style={"display": "flex", "justifyContent": "space-between", "padding": "20px 5%", "gap": "4%", "boxSizing": "border-box"})

], style={"background": "linear-gradient(to bottom right, #144579, #0a1e3f)"})

# Callback
@app.callback(
    [Output("line-chart", "figure"),
     Output("histogram", "figure"),
     Output("coping-pictograph", "children"),
     Output("history-pictograph", "children"),
     Output("country-dropdown", "value")],
    [Input("choropleth-map", "clickData"),
     Input("country-dropdown", "value")]
)
def update_dashboard(click_data, dropdown_value):
    ctx = dash.callback_context
    country = "United States"

    if ctx.triggered and ctx.triggered[0]["prop_id"].startswith("choropleth-map") and click_data:
        country = click_data["points"][0]["hovertext"]
    elif dropdown_value:
        country = dropdown_value

    # Line chart
    filtered_exp = health_df[health_df["country"] == country]
    line_fig = px.line(
        filtered_exp,
        x="year", y="health_exp", markers=True,
        title=f"Healthcare Expenditure Trend for {country}",
        labels={"year": "Year", "health_exp": "Expenditure (% of GDP)"},
        color_discrete_sequence=["#3daff5"]
    )
    line_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        margin={"t": 50, "b": 30}, height=220,
        yaxis=dict(title_font=dict(size=11))
    )

    # Histogram
    occ_data = occ_data_full[
        (occ_data_full["Country"] == country) &
        (occ_data_full["Mental_Health_History"].str.strip().str.lower() == "yes") 
    ]

    if not occ_data.empty:
        occ_counts = occ_data["Occupation"].value_counts(normalize=True).mul(100).reset_index()
        occ_counts.columns = ["Occupation", "Percentage"]
    else:
        occ_counts = pd.DataFrame({
            "Occupation": ["Housewife", "Student", "Business", "Corporate", "Others"],
            "Percentage": [0, 0, 0, 0, 0]
        })

    hist_fig = px.bar(
        occ_counts, x="Occupation", y="Percentage",
        title=f"Distribution of Occupations with Mental Health Disorder History in {country} (2020)",
        labels={"Occupation": "Occupation Group", "Percentage": "Population Share"},
        color="Occupation",
        color_discrete_sequence=["#144579", "#4ba2db", "#41c6c6", "#cce5f6", "#f3f3f3"]
    )
    hist_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=11),  
        margin={"t": 50, "b": 30},
        height=220,
        showlegend=False
    )

    # Pictographs
    filtered_survey = occ_data_full[(occ_data_full["Country"] == country)]

    if not filtered_survey.empty:
        coping_yes = (filtered_survey["Coping_Struggles"].str.strip().str.lower() == "yes")
        history_yes = (filtered_survey["Mental_Health_History"].str.strip().str.lower() == "yes")
        coping_pct = coping_yes.mean() * 100
        history_pct = history_yes.mean() * 100
        coping_rate = round(coping_pct / 10)
        history_rate = round(history_pct / 10)
    else:
        coping_rate = 5
        history_rate = 5
        coping_pct = 50.0
        history_pct = 50.0

    coping_pic = render_image_pictograph(
        coping_rate,
        "/assets/red.png",
        "/assets/white.png",
        f"{coping_rate} out of 10 People in {country} Struggle with Coping as of 2020",
        coping_pct,
        country
    )

    history_pic = render_image_pictograph(
        history_rate,
        "/assets/red.png",
        "/assets/white.png",
        f"{history_rate} out of 10 People in {country} had a previous history of mental health disorders as of 2020",
        history_pct,
        country
    )

    return line_fig, hist_fig, coping_pic, history_pic, country

if __name__ == '__main__':
    # Use PORT environment variable if it exists (for Render compatibility)
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
