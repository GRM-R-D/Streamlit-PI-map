import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Geocoder
from streamlit_folium import folium_static
import streamlit.components.v1 as components

# Set up the page configuration
st.set_page_config(page_title="Postcode Data", page_icon="🗄️", layout="wide")


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


# URL of the logo image
logo_url = "https://grmdevelopment.wpengine.com/wp-content/uploads/2020/07/GRM-master-logo-02.png"

# Add the logo with a specified height and resize using CSS
add_logo(logo_url, height=100)

# Set the title and sidebar header
st.markdown("## Postcode Data")

# Add a paragraph to the sidebar
st.sidebar.markdown("""

     This app allows you to explore GRM project data through an interactive map and detailed project information. 

     You can filter projects by Plasticity Index, Project ID, and Geology Code.

     The map shows project locations with color-coded markers based on Plasticity Index values, helping you compare 
     laboratory data with geology and location information, as well as explore relationships with nearby projects.

""")

# Read and preprocess the Parquet data
filename = 'Points.parquet'  # replace with your actual Parquet file path
df = pd.read_parquet(filename)

# Determine the range for Plasticity Index slider
plasticity_rng = (df['PlasticityIndex'].min(), df['PlasticityIndex'].max())

geojson_file = 'postcodes.geojson'


def get_color(plasticity_index):
    if plasticity_index >= 40:
        return 'red'
    elif 20 <= plasticity_index < 40:
        return 'orange'
    elif 10 <= plasticity_index < 20:
        return 'beige'
    else:
        return 'green'

@st.cache_resource
def create_map(filter_df, geojson_file):
    # Check if the filtered DataFrame is empty
    if filter_df.empty:
        return folium.Map(location=[0, 0], zoom_start=6)  # Default location if no data

    m = folium.Map(location=[filter_df['Latitude'].mean(), filter_df['Longitude'].mean()], zoom_start=6)

    # Add the GeoJSON layer for postcodes with styled hover tooltips
    folium.GeoJson(
        geojson_file,
        name="Postcode Boundaries",
        style_function=lambda feature: {
            'fillColor': '#blue',
            'color': 'black',
            'weight': 2,
            'fillOpacity': 0.1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['name'],
            aliases=['Postcode:'],
            localize=True,
            sticky=True,
            direction='top',
            style=(
                "background-color: white; "
                "color: black; "
                "font-size: 16px; "  # Ensure this is set correctly
                "font-weight: bold; "
                "padding: 5px;"
                "border-radius: 3px; "
                "border: 1px solid black;"
            )
        )
    ).add_to(m)

    marker_cluster = MarkerCluster().add_to(m)

    # Iterate over the filtered DataFrame rows and add markers to the cluster
    for _, row in filter_df.iterrows():
        location = [row['Latitude'], row['Longitude']]
        popup_content = (
            f"<div style='font-size: 14px;'>"
            f"<b>Postcode:</b> {row['Postcode']}<br>"
            f"<b>Project ID:</b> {row['ProjectID']}<br>"
            f"<b>Geology:</b> {row['GeologyCode']}<br>"
            f"<b>Plastic Limit:</b> {row['PlasticLimit']}<br>"
            f"<b>Liquid Limit:</b> {row['LiquidLimit']}<br>"
            f"<b>Plasticity Index:</b> {row['PlasticityIndex']}<br>"
            f"<b>Moisture Content:</b> {row['MoistureContent']}"
            f"</div>"
        )
        popup = folium.Popup(popup_content, max_width=300)
        folium.Marker(location=location, popup=popup, icon=folium.Icon(color=get_color(row['PlasticityIndex']))).add_to(
            marker_cluster)

    # Add Geocoder plugin
    Geocoder().add_to(m)
    return m


def show_map(filtered_df):
    m = create_map(filtered_df, geojson_file)  # Pass the GeoJSON file
    folium_static(m)  # Display the map


# Define the layout using Streamlit's grid system
row1 = st.columns([2, 1, 1])
row2 = st.columns([1, 1])
row3 = st.columns([1, 1])

# Initialize session state variables if not already present
if 'selected_project_id' not in st.session_state:
    st.session_state.selected_project_id = ""
if 'selected_geology_code' not in st.session_state:
    st.session_state.selected_geology_code = ""

# Row 1: Filters and Searches
with row1[0]:
    with st.expander("Plasticity Index Filter", expanded=False):
        plasticity_min, plasticity_max = plasticity_rng
        plasticity_filter = st.slider("Plasticity Index", min_value=int(plasticity_min), max_value=int(plasticity_max),
                                      value=(int(plasticity_min), int(plasticity_max)))

with row1[1]:
    with st.expander("Project ID Search", expanded=False):
        project_ids = sorted(df['ProjectID'].astype(str).unique())
        selected_project_id = st.selectbox("Select Project ID", options=[""] + project_ids, key="project_id")

        # Update session state for Project ID
        if selected_project_id != st.session_state.selected_project_id:
            st.session_state.selected_project_id = selected_project_id
            st.session_state.selected_geology_code = ""  # Reset Geology Code when Project ID changes

with row1[2]:
    with st.expander("Geology Code Search", expanded=False):
        # Update Geology Code options based on selected Project ID
        if st.session_state.selected_project_id:
            geology_codes = sorted(
                df[df['ProjectID'].astype(str) == st.session_state.selected_project_id]['GeologyCode'].astype(
                    str).unique())
        else:
            geology_codes = sorted(df['GeologyCode'].astype(str).unique())

        selected_geology_code = st.selectbox("Select Geology Code", options=[""] + geology_codes, key="geology_code")

        # Update session state for Geology Code
        if selected_geology_code != st.session_state.selected_geology_code:
            st.session_state.selected_geology_code = selected_geology_code

# Apply filters based on selections
filtered_df = df[(df['PlasticityIndex'] >= plasticity_filter[0]) &
                 (df['PlasticityIndex'] <= plasticity_filter[1])]

if st.session_state.selected_project_id:
    filtered_df = filtered_df[filtered_df['ProjectID'].astype(str) == st.session_state.selected_project_id]

if st.session_state.selected_geology_code:
    filtered_df = filtered_df[filtered_df['GeologyCode'].astype(str) == st.session_state.selected_geology_code]

# Row 2: Legend and Checkboxes
with row2[0]:
    legend_html = """<div style="position: fixed; bottom: 10px; left: 10px; width: auto; height: 40px; 
    background-color: black; border:2px solid grey; border-radius:8px; z-index:9999; font-size:14px; padding: 10px 
    10px 25px 10px;; white-space: nowrap; font-family: 'Arial', sans-serif; color: #FAFAFA;"> <b style="font-family: 
    'Arial', sans-serif; display: block; margin-bottom: 10px;">Plasticity Index</b> <i style="background:green; 
    width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> < 10 <i style="background:#eed9c4; 
    width: 20px; height: 20px; display: inline-block; margin-right: 5px; margin-left: 10px;"></i> 10 - 20 <i 
    style="background:orange; width: 20px; height: 20px; display: inline-block; margin-right: 5px; margin-left: 
    10px;"></i> 20 - 40 <i style="background:red; width: 20px; height: 20px; display: inline-block; margin-right: 
    5px; margin-left: 10px;"></i> ≥ 40 </div>"""
    components.html(legend_html, height=100)

with row2[1]:
    show_utm = st.checkbox('Show UTM Coordinates', value=True)
    show_latlong = st.checkbox('Show LATLONG Coordinates', value=True)
    st.caption("Use the checkboxes to toggle the display of UTM and Latitude/Longitude coordinates in the data table.")

# Define column groups
utm_columns = ['Easting', 'Northing']
latlong_columns = ['Latitude', 'Longitude']

# Determine which columns to display
columns_to_display = []
if show_utm:
    columns_to_display.extend(utm_columns)
if show_latlong:
    columns_to_display.extend(latlong_columns)

# Always show these columns and reorder them
always_display_columns = ['ProjectID', 'LocationID', 'Postcode', 'GeologyCode', 'Fines', 'PlasticLimit', 'LiquidLimit',
                          'PlasticityIndex', 'MoistureContent']

# Combine always displayed columns with selected columns
columns_to_display = always_display_columns + columns_to_display

# Ensure only existing columns are included
columns_to_display = [col for col in columns_to_display if col in df.columns]

# Filter DataFrame for display
filtered_df_display = filtered_df[columns_to_display]

column_rename_map = {
    'GeologyCode': 'Geology',
    'MoistureContent': 'MC (%)',
    'PlasticityIndex': 'PI (%)',
    'PlasticLimit': 'PL (%)',
    'LiquidLimit': 'LL (%)',
    'Easting': 'E',
    'Northing': 'N',
    'Latitude': 'Lat',
    'Longitude': 'Long',
    'Postcode': 'PC',
    'Fines': 'Fines (%)'
}

# Rename the columns
filtered_df_display = filtered_df_display.rename(columns=column_rename_map)

# Row 3: Data Table
with row3[0]:
    st.dataframe(filtered_df_display)

# Show the filtered map
show_map(filtered_df)
