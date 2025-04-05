import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # This is needed for Render deployment

# Use relative file paths
# Place your CSV files in the same directory as your app.py file
current_dir = os.path.dirname(os.path.abspath(__file__))
merged_df = pd.read_csv(os.path.join(current_dir, "merged_dashboard_data.csv"))
health_df = pd.read_csv(os.path.join(current_dir, "world_health_indicators.csv"))
mental_health_df = pd.read_csv(os.path.join(current_dir, "mental_health_survey.csv"))

# Choropleth Map
map_fig = px.choropleth(
    merged_df,
    locations="country_code",
    color="pct_treatment",
    hover_name="country",
    custom_data=["life_expect", "pct_treatment"],
    color_continuous_scale=[[0, '#99ccff'], [0.5, '#3366cc'], [1.0, '#003366']],
    projection="natural earth",
    title="Global Treatment Rates"
)
map_fig.update_layout(
    coloraxis_colorbar=dict(
        title="Treatment Rate (%)",  # More readable label
        len=0.8,
        thickness=16,
        y=0.5
    )
)

# Custom hover template
map_fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>" +
                  "Treatment Rate: %{customdata[1]:.1f}%<br>" +
                  "Life Expectancy: %{customdata[0]:.1f} years<br><extra></extra>"
)

map_fig.update_layout(
    margin={"r":0,"t":50,"l":0,"b":0},
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="white",
    coloraxis_colorbar=dict(len=0.8, thickness=16, y=0.5),
    height=420
)

# Generate pictograph using actual silhouette images
def render_image_pictograph(count, filled_src, unfilled_src, label_text):
    icons = []
    for i in range(10):
        img_src = filled_src if i < count else unfilled_src
        icons.append(html.Img(src=img_src, style={"height": "65px", "margin": "0 5px"}))
    return html.Div([
        html.Div(label_text, style={"textAlign": "center", "color": "white", "marginBottom": "8px", "fontFamily": "Arial", "fontSize": "16px"}),
        html.Div(icons, style={"display": "flex", "justifyContent": "center"})
    ], style={"backgroundColor": "#1976d2", "borderRadius": "10px", "padding": "20px 15px", "width": "100%", "boxSizing": "border-box"})

# Compute global values from the merged data
global_coping_rate = round(merged_df["pct_coping_struggles"].mean() / 10)
global_history_rate = round(merged_df["pct_history"].mean() / 10)

# Layout
app.layout = html.Div([
    html.H1("GLOBAL MENTAL HEALTH INDICATORS 2020", style={"textAlign": "center", "color": "white", "padding": "10px", "fontFamily": "Arial"}),

    html.Div([
        html.Div([dcc.Graph(id="choropleth-map", figure=map_fig)], style={"width": "58%", "padding": "5px"}),
        html.Div([
            dcc.Graph(id="line-chart", style={"height": "220px", "marginBottom": "10px"}),
            dcc.Graph(id="histogram", style={"height": "220px"})
        ], style={"width": "40%", "padding": "5px"})
    ], style={"display": "flex", "flexDirection": "row"}),

    html.Div([
        html.Div([
            render_image_pictograph(global_coping_rate, "/assets/red.png", "/assets/white.png", f"{global_coping_rate} out of 10 People Struggle with Coping")
        ], style={"width": "48%"}),

        html.Div([
            render_image_pictograph(global_history_rate, "/assets/red.png", "/assets/white.png", f"{global_history_rate} out of 10 People had a previous history of mental health disorders")
        ], style={"width": "48%"})
    ], style={"display": "flex", "justifyContent": "space-between", "padding": "20px 5%", "gap": "4%", "boxSizing": "border-box"})

], style={"background": "linear-gradient(to bottom right, #144579, #0a1e3f)"})

# Callbacks
@app.callback(
    [Output("line-chart", "figure"), Output("histogram", "figure")],
    [Input("choropleth-map", "clickData")]
)
def update_charts(click_data):
    country = "United States"
    if click_data:
        country = click_data["points"][0]["hovertext"]

    # Line chart from health expenditure data
    filtered_exp = health_df[health_df["country"] == country]
    line_fig = px.line(
        filtered_exp,
        x="year", y="health_exp", markers=True,
        title=f"Healthcare Expenditure Trend for {country}",
        labels={
            "year": "Year",
            "health_exp": "Expenditure"
        },
        color_discrete_sequence=["#3daff5"]
    )

    line_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="white", margin={"t": 50, "b": 30}, height=220
    )

    # Histogram: dynamically compute occupation distribution if available
    occ_data = mental_health_df[mental_health_df["Country"] == country]

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
        title=f"Occupation Distribution with Mental Health Survey in {country}",
        labels={
            "Occupation": "Occupation Group",
            "Percentage": "Population Share"
        },
        color="Occupation",
        color_discrete_sequence=["#144579", "#4ba2db", "#41c6c6", "#cce5f6", "#f3f3f3"]
    )

    hist_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="white", margin={"t": 50, "b": 30}, height=220,
        showlegend=False
    )

    return line_fig, hist_fig

if __name__ == '__main__':
    # Use PORT environment variable if it exists (for Render compatibility)
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
