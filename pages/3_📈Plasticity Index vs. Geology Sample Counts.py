import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from statsmodels.nonparametric.smoothers_lowess import lowess

# Set up the Streamlit page
st.set_page_config(page_title="Plasticity vs Count", page_icon="📊", layout="wide")


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

     Data visualisation of Plasticity Index and its relationship to different geologies, by analysing the count of samples for each geology.
""")

# URL of the logo image
logo_url = "https://grmdevelopment.wpengine.com/wp-content/uploads/2020/07/GRM-master-logo-02.png"

# Add the logo with a specified height and resize using CSS
add_logo(logo_url, height=100)

st.markdown("## Plasticity Index vs. Count of Samples")

@st.cache_data
def load_data():
    data = pd.read_csv('Pointdate.csv')
    data['Date'] = pd.to_datetime(data['Date'])
    return data

data = load_data()

geology_options = ['GLACIAL DEPOSITS', 'LONDON CLAY FORMATION', 'MERCIA MUDSTONE GROUP', 'OADBY TILL MEMBER']
selected_geology = st.selectbox('Geology Code:', geology_options)

filtered_data = data[data['GeologyCode'] == selected_geology]

count_data = filtered_data['PlasticityIndex'].value_counts().reset_index()
count_data.columns = ['PlasticityIndex', 'Count of Samples']
count_data = count_data[count_data['PlasticityIndex'] != 0]
count_data = count_data.sort_values(by='PlasticityIndex')

lowess_result = lowess(count_data['Count of Samples'], count_data['PlasticityIndex'], frac=0.2)
x_lowess, y_lowess = lowess_result[:, 0], lowess_result[:, 1]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=count_data['PlasticityIndex'],
    y=count_data['Count of Samples'],
    mode='markers',
    name='PI vs. Count point data',
    hovertemplate='<span style="font-size: 16px; color: #97eaff; ">Plasticity Index: %{x}<br>Count: %{y:.1f}</span><extra></extra>'
))
fig.add_trace(go.Scatter(
    x=x_lowess,
    y=y_lowess,
    mode='lines',
    name='Average Count across PI',
    hovertemplate='<span style="font-size: 16px; color: #7ab2f7; ">Plasticity Index: %{x}<br>Estimated Count: %{y:.1f}</span><extra></extra>'
))

fig.update_layout(
    xaxis_title='Plasticity Index',
    yaxis_title='Count of Samples',
    title=dict(text=f'Plasticity Index vs. Count of Samples with Trendline for {selected_geology}', x=0.2),
    xaxis=dict(tickmode='linear', dtick=5)
)

col1, col2 = st.columns([1, 2])
with col1:
    st.write("Plasticity Index Count Data:")
    sorted_count_data = count_data.sort_values(by='Count of Samples', ascending=False)
    st.dataframe(
        sorted_count_data,
        hide_index=True,
        use_container_width=True,
        column_config={
            "PlasticityIndex": st.column_config.NumberColumn("Plasticity Index"),
            "Count of Samples": st.column_config.NumberColumn("Count of Samples")
        }
    )
with col2:
    st.plotly_chart(fig, use_container_width=True)