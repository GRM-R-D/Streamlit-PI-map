import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess
import folium
from streamlit_folium import folium_static
import streamlit.components.v1 as components

# Set up the Streamlit page
st.set_page_config(page_title="Moisture Content and Depth vs Time", page_icon="📊", layout="wide")

@st.cache_resource
def add_logo(logo_url: str, width: int = 250, height: int = 300):
    """Add a logo (from logo_url) on the top of the navigation page of a multipage app."""
    logo_css = f"""
        <style>
            [data-testid="stSidebarNav"] {{
                background-image: url({logo_url});
                background-repeat: no-repeat;
                background-size: {width}px {height}px; /* Set the size of the logo */
                padding-top: {height + 20}px;
                background-position: 20px 0px;
            }}
        </style>
    """
    st.markdown(logo_css, unsafe_allow_html=True)

st.sidebar.markdown("""
     Data visualization of Moisture Content and Depth over time, alongside historical climate and subsidence data, to identify possible links.
""")

# URL of the logo image
logo_url = "https://grmdevelopment.wpengine.com/wp-content/uploads/2020/07/GRM-master-logo-02.png"

# Add the logo with a specified height and resize using CSS
add_logo(logo_url, height=100)

st.markdown("## Moisture Content and Depth vs. Time")

@st.cache_data
def load_data():
    data = pd.read_csv('Pointdate.csv')
    data['Date'] = pd.to_datetime(data['Date'])
    return data

data = load_data()

# Define the function to determine color based on Moisture Content
def get_color(moisture_content):
    if moisture_content >= 40:
        return 'red'
    elif 20 <= moisture_content < 40:
        return 'orange'
    elif 10 <= moisture_content < 20:
        return 'beige'
    else:
        return 'green'

# Define the layout using Streamlit's grid system
row1 = st.columns([2, 1, 1])  # Adjust column ratios for controls
row2 = st.columns([3, 5, 1.5])  # Adjust column ratios for map, legend, and dataframe
row3 = st.columns([1])

# Row 1 - Geology Filter and Graph Type
with row1[0]:
    with st.expander("Geology Filter", expanded=False):
        geology_options = ['GLACIAL DEPOSITS', 'LONDON CLAY FORMATION', 'MERCIA MUDSTONE GROUP', 'OADBY TILL MEMBER']
        selected_geology = st.selectbox('', geology_options, label_visibility='collapsed')

with row1[1]:
    with st.expander("Graph Type", expanded=False):
        graph_options = ['Scatter Plot', 'Box Plot']
        selected_graph = st.selectbox('', graph_options, label_visibility='collapsed')

# Filter data based on selected geology
filtered_data = data[data['GeologyCode'] == selected_geology]

# Row 2 - Date Range, Map, and DataFrame
with row2[0]:
    min_date = min(filtered_data['Date']).date()
    max_date = max(filtered_data['Date']).date()
    start_date, end_date = st.slider(
        "Select Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="DD/MM/YYYY"
    )

    # Apply the date range filter to the data
    mask = (filtered_data['Date'].dt.date >= start_date) & (filtered_data['Date'].dt.date <= end_date)
    date_filtered_data = filtered_data.loc[mask]
    date_filtered_data['Year'] = date_filtered_data['Date'].dt.year

    if selected_graph == 'Scatter Plot':
        st.write("Moisture Content and Depth with Date Data:")
        filtered_df = date_filtered_data[['Date', 'MoistureContent', 'DepthValue']].copy()
        filtered_df['Date'] = filtered_df['Date'].dt.strftime('%d/%m/%Y')
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    elif selected_graph == 'Box Plot':
        st.write("Moisture Content Data by Year:")
        # Convert 'Year' to datetime, but only extract the year
        date_filtered_data['YearDate'] = pd.to_datetime(date_filtered_data['Year'], format='%Y')
        st.dataframe(
            date_filtered_data[['YearDate', 'MoistureContent']],
            hide_index=True,
            column_config={
                "YearDate": st.column_config.DateColumn("Year", format="YYYY", width="medium"),
                "MoistureContent": st.column_config.NumberColumn("Moisture Content")
            }
        )

with row2[1]:
    st.markdown("##### Map")

    # Compute the average Moisture Content per Date and Location
    avg_data = date_filtered_data.groupby(['Date', 'GeologyCode', 'Latitude', 'Longitude'], as_index=False)['MoistureContent'].mean()

    # Create the Folium map centered around the mean location of filtered data
    m = folium.Map(location=[avg_data['Latitude'].mean(), avg_data['Longitude'].mean()], zoom_start=6)

    # Plot each point on the map with the color determined by the average Moisture Content
    for idx, row in avg_data.iterrows():
        avg_moisture = row['MoistureContent']
        color = get_color(avg_moisture)

        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=5,
            popup=folium.Popup(
                f"<div style='font-size: 14px;'><b>Average Moisture:</b> {avg_moisture:.2f}</div>",
                max_width=200
            ),
            color=color,  # Border color
            fill=True,  # Enable fill
            fillColor=color,  # Fill color
            fillOpacity=1  # Set fill opacity to 1 for opaque fill
        ).add_to(m)

    folium_static(m)

with row2[2]:
    # HTML for the legend
    legend_html = """
    <div style="
        width: 150px; 
        height: 100x; 
        background-color: black; 
        border: 2px solid grey; 
        border-radius: 8px; 
        font-size: 14px; 
        padding: 10px; 
        font-family: 'Arial', sans-serif; 
        color: #FAFAFA;
        display: flex;
        flex-direction: column;
        align-items: flex-start;">
        <b style="font-family: 'Arial', sans-serif; margin-bottom: 10px;">Moisture Content</b>
        <div style="display: flex; flex-direction: column;">
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <i style="background:green; width: 20px; height: 20px; display: inline-block; margin-right: 10px;"></i> &lt; 10
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <i style="background:#eed9c4; width: 20px; height: 20px; display: inline-block; margin-right: 10px;"></i> 10 - 20
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <i style="background:orange; width: 20px; height: 20px; display: inline-block; margin-right: 10px;"></i> 20 - 40
            </div>
            <div style="display: flex; align-items: center;">
                <i style="background:red; width: 20px; height: 20px; display: inline-block; margin-right: 10px;"></i> ≥ 40
            </div>
        </div>
    </div>
    """

    # Render the legend using components.html to maintain the style
    st.components.v1.html(legend_html, height=250)

# Plot/Graph
with row3[0]:
    if selected_graph == 'Scatter Plot':
        fig = go.Figure()

        # Add main scatter plot
        fig.add_trace(go.Scatter(
            x=date_filtered_data['Date'],
            y=date_filtered_data['MoistureContent'],
            mode='markers',
            name='Moisture Content',
            marker=dict(color='cyan'),
            hovertemplate='<span style="font-size: 16px; color: #97eaff;">Date: %{x}<br>Moisture Content: %{y}</span><extra></extra>'
        ))

        # Find MAX Moisture Content points for each year
        max_points = date_filtered_data.loc[date_filtered_data.groupby('Year')['MoistureContent'].idxmax()]

        # Add MAX points in red
        fig.add_trace(go.Scatter(
            x=max_points['Date'],
            y=max_points['MoistureContent'],
            mode='markers',
            name='MAX Moisture per Year',
            marker=dict(color='red', size=10, symbol='star'),
            hovertemplate='<b><span style="font-size: 16px; color: #ff5e5f;">Year: %{text}<br>Max Moisture: %{y}<br></span></b><span style="font-size: 16px; color: #ff5e5f;">Date: %{x|%d/%m/%Y}</span><extra></extra>',
            text=max_points['Year']
        ))

        # Calculate LOWESS trendline
        x_numeric = date_filtered_data['Date'].astype('int64').astype('float64')
        lowess_result = lowess(date_filtered_data['MoistureContent'], x_numeric, frac=0.2)
        x_lowess, y_lowess = lowess_result[:, 0], lowess_result[:, 1]

        # Add LOWESS trendline
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(x_lowess),
            y=y_lowess,
            mode='lines',
            name='Average Moisture Content',
            line=dict(color='#7ab2f7', width=2),
            hovertemplate='<span style="font-size: 16px; color: #7ab2f7;">Date: %{x}<br>Average Moisture Content: %{y:.2f}</span><extra></extra>'
        ))

        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Moisture Content',
            title=dict(text=f'Moisture Content vs. Date with Trendline for {selected_geology}', x=0.2),
        )

        st.plotly_chart(fig, use_container_width=True)

    elif selected_graph == 'Box Plot':
        filtered_data['Year'] = filtered_data['Date'].dt.year
        filtered_data['Year'] = filtered_data['Year'].astype(str)

        fig = go.Figure()
        for year in sorted(filtered_data['Year'].unique()):
            year_data = filtered_data[filtered_data['Year'] == year]
            fig.add_trace(go.Box(
                y=year_data['MoistureContent'],
                name=year,
                boxmean='sd',
                hoveron='boxes+points',
                hovertemplate='Year: %{x}<br>Moisture Content: %{y}<extra></extra>'
            ))

        fig.update_layout(
            xaxis_title='Year',
            yaxis_title='Moisture Content',
            title=dict(text=f'Box Plot of Moisture Content by Year for {selected_geology}', x=0.2),
        )

        st.plotly_chart(fig, use_container_width=True)
