import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Geocoder
from streamlit_folium import folium_static

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

# Display the logo image directly to check if it's accessible
st.sidebar.image(logo_url, width=250)  # Display the image directly

# Set the title and sidebar header
st.markdown("## Postcode Data")

# Add a paragraph to the sidebar
st.sidebar.markdown("""
     This app allows you to explore GRM project data through an interactive map and detailed project information. 
     You can filter projects by Project ID and Geology Code.
     The map shows project locations, helping you compare laboratory data with geology and location information.
""")

# Read and preprocess the Parquet data
filename = 'POINTS.parquet'  # replace with your actual Parquet file path
df = pd.read_parquet(filename)

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

    marker_cluster = MarkerCluster(
        icon_create_function="""function(cluster) {
                var count = cluster.getChildCount();
                var size = Math.min(30 + Math.pow(count, 0.5) * 5, 70);  // Exponential growth for larger clusters
                return L.divIcon({
                    html: '<div style="background-color: blue; border-radius: 50%; padding: 10px; text-align: center; font-size: 16px; color: white; width: ' + size + 'px; height: ' + size + 'px; display: flex; align-items: center; justify-content: center; opacity: 0.7;"><b>' + count + '</b></div>',
                    className: 'marker-cluster',
                    iconSize: new L.Point(size, size)
                });
            }"""
    ).add_to(m)

    # Iterate over the filtered DataFrame rows and add markers to the cluster
    for _, row in filter_df.iterrows():
        location = [row['Latitude'], row['Longitude']]
        popup_content = (
            f"<div style='font-size: 14px;'>"
            f"<b>Postcode:</b> {row['Postcode']}<br>"
            f"<b>Project ID:</b> {row['ProjectID']}<br>"
            f"<b>Location ID:</b> {row['LocationID']}<br>"
            f"<b>Depth (m):</b> {row['Depth']}<br>"
            f"<b>Geology:</b> {row['Geology Code']}<br>"
            f"<b>Plastic Limit:</b> {row['PlasticLimit']}<br>"
            f"<b>Liquid Limit:</b> {row['LiquidLimit']}<br>"
            f"<b>Plasticity Index:</b> {row['PlasticityIndex']}<br>"
            f"<b>Moisture Content:</b> {row['MoistureContent']}<br>"
            f"<b>Date:</b> {pd.to_datetime(row['Date'], dayfirst=True).strftime('%d/%m/%Y')}<br>"
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
    return m  # Return the map object so it can be used outside


# Define the layout using Streamlit's grid system
row1 = st.columns([2, 1, 1])
row2 = st.columns([3, 1])
row3 = st.columns([1])

# Initialize session state variables if not already present
if 'selected_project_id' not in st.session_state:
    st.session_state.selected_project_id = ""
if 'selected_geology_code' not in st.session_state:
    st.session_state.selected_geology_code = ""

plasticity_options = ["< 10", "10 - 20", "20 - 40", ">= 40"]
icon_map = {
    "< 10": "🟢 < 10",  # Green circle
    "10 - 20": "🟡 10 - 20",  # Yellow circle
    "20 - 40": "🟠 20 - 40",  # Orange circle
    ">= 40": "🔴 &ge; 40",  # Red circle (HTML entity for >=)
}


def format_func(option):
    return icon_map[option]

# Row 1: Filters and Searches
with row1[0]:
    selected_plasticity = st.pills(
        "Select Plasticity Index",
        options=plasticity_options,
        format_func=format_func,
        selection_mode="multi"
    )

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
                df[df['ProjectID'].astype(str) == st.session_state.selected_project_id]['Geology Code'].astype(
                    str).unique())
        else:
            geology_codes = sorted(df['Geology Code'].astype(str).unique())

        selected_geology_code = st.selectbox("Select Geology Code", options=[""] + geology_codes, key="geology_code")

        # Update session state for Geology Code
        if selected_geology_code != st.session_state.selected_geology_code:
            st.session_state.selected_geology_code = selected_geology_code


filtered_df = df.copy()  # Start with a copy of the original DataFrame

# Apply ProjectID filter
if selected_project_id:
    filtered_df = filtered_df[filtered_df['ProjectID'].astype(str) == selected_project_id]

# Apply Geology Code filter
if selected_geology_code:
    filtered_df = filtered_df[filtered_df['Geology Code'].astype(str) == selected_geology_code]

# Apply Plasticity Index filter
plasticity_filters = []
if selected_plasticity:
    if "< 10" in selected_plasticity:
        plasticity_filters.append((filtered_df['PlasticityIndex'] < 10))
    if "10 - 20" in selected_plasticity:
        plasticity_filters.append((filtered_df['PlasticityIndex'] >= 10) & (filtered_df['PlasticityIndex'] < 20))
    if "20 - 40" in selected_plasticity:
        plasticity_filters.append((filtered_df['PlasticityIndex'] >= 20) & (filtered_df['PlasticityIndex'] < 40))
    if ">= 40" in selected_plasticity:
        plasticity_filters.append((filtered_df['PlasticityIndex'] >= 40))

    if plasticity_filters:
        filtered_df = filtered_df[pd.concat(plasticity_filters, axis=1).any(axis=1)]

# Define column groups
columns_to_display = []


# Always show these columns and reorder them
always_display_columns = ['Date', 'ProjectID', 'LocationID', 'Depth', 'Postcode', 'Geology Code', 'Fines',
                          'PlasticLimit',
                          'LiquidLimit',
                          'PlasticityIndex', 'MoistureContent']

# Combine always displayed columns with selected columns
columns_to_display = always_display_columns

# Filter DataFrame for display
filtered_df_display = filtered_df[columns_to_display]

column_rename_map = {
    'Geology Code': 'Geology',
    'Depth': 'Depth (m)',
    'MoistureContent': 'MC (%)',
    'PlasticityIndex': 'PI (%)',
    'PlasticLimit': 'PL (%)',
    'LiquidLimit': 'LL (%)',
    'Latitude': 'Lat',
    'Longitude': 'Lon'
}

filtered_df_display = filtered_df_display.rename(columns=column_rename_map)

# Row 2: Map
with row2[0]:
    st.subheader("Map", divider='grey')

    # Show the map with the filtered data
    m = show_map(filtered_df)
    folium_static(m, width=1100, height=600)  # Adjust the width and height here

# Row 3: Dataframe
with row3[0]:
    st.subheader("Table", divider='grey')
    st.dataframe(filtered_df_display, hide_index=True)
