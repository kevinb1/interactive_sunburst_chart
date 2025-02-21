from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import io
import base64
import dash
import plotly.io as pio

# Create a Dash app
app = dash.Dash(__name__)
server = app.server

# Layout with a File Upload, Dropdown, and Graph
app.layout = html.Div([
    # File upload
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload File'),
        multiple=False  # Only one file at a time
    ),

    # Dropdown for selecting multiple columns
    dcc.Dropdown(
        id='column-selector',
        options=[],  # Options will be dynamically populated after file upload
        value=[],  # Default value (will be updated after file upload)
        multi=True  # Allow multiple columns to be selected
    ),

    # Graph for the Sunburst chart, centered using CSS
    html.Div(
        dcc.Graph(id='sunburst-chart'),
        style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'height': '80vh'}
    ),

    # Save image button
    html.Button('Save Image', id='save-image-button'),
    html.Div(id='output-state')
])

# Callback to update the sunburst chart and dropdown options based on uploaded file
@app.callback(
    [Output('sunburst-chart', 'figure'),
     Output('column-selector', 'options'),
     Output('column-selector', 'value')],
    [Input('upload-data', 'contents'),
     Input('column-selector', 'value')]
)
def update_sunburst_chart(uploaded_file, selected_columns):
    if uploaded_file is not None:
        # Decode and read the uploaded file
        content_type, content_string = uploaded_file.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))

        url = "https://raw.githubusercontent.com/kevinb1/interactive_sunburst_chart/main/mojo_data_chart.xlsx"
        df = pd.read_excel(url)
        
        df = df.fillna("geen antwoord beschikbaar")  # Fill missing values

        # Update the dropdown options with column names
        options = [{'label': col, 'value': col} for col in df.columns]

        # If no columns are selected, return an empty figure
        if not selected_columns:
            return {}, options, []

        # Explode data if columns are selected (split lists into separate entries)
        for column in selected_columns:
            try:
                # Check if the column can be exploded into lists
                if "keywords" in column:
                    df[column] = df[column].str.split(", ")
                    df = df.explode(column)
            except:
                pass  # If error, just continue

        # Column to color is the one with the most unique values
        column_to_color = max({col: df[col].nunique() for col in selected_columns}, key=lambda col: df[col].nunique())

        # Sunburst chart
        fig = px.sunburst(df,
                          path=selected_columns,
                          color=column_to_color,
                          labels={column_to_color: "Category"})

        # Generate the title based on the selected path
        path_title = " → ".join(selected_columns)
        
        fig.update_traces(
            textinfo='label+percent entry',  # Show labels and percentages
            insidetextfont_size=18  # Increase font size of text inside the chart
        )

        # Add the title to the chart
        fig.update_layout(
            autosize=True,
            width=1000,
            height=1000,
            title=f"{path_title}",  # Dynamic title based on path
            title_x=0.5,  # Center the title
            title_y=0.95,  # Adjust the vertical position of the title
            title_font_size=24,  # Increase title font size
            legend_font_size=18  # Increase legend font size
        )

        return fig, options, selected_columns

    return {}, [], []  # Return an empty figure and no options if no file is uploaded

# Callback to save the image of the chart
@app.callback(
    Output('output-state', 'children'),
    [Input('save-image-button', 'n_clicks')],
    [State('sunburst-chart', 'figure')]
)
def save_image(n_clicks, figure):
    if n_clicks is None or figure is None:
        return ""
    
    try:
        # Save the figure to a PNG file
        pio.write_image(figure, 'output/images/sunburst_chart.png')
        return "Image saved successfully!"
    except Exception as e:
        return f"Error saving chart: {str(e)}"

if __name__ == '__main__':
    app.run_server(debug=True)
