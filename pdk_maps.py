# this is a helper file contains methods only
# not executable
import urllib

import streamlit as st
import pandas as pd
import pydeck as pdk


def jsondata(df):

    dfmap = df[['latitude', 'longitude', 'radius', 'price']]
    datadict = dfmap.to_dict('index')
    data = []
    for k, v in datadict.items():
        data.append(v)
    return data


def gridplot(df):
    # 3D plots
    gridlayer = pdk.Layer(
        "GridLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_elevation="pricepersqft",
        pickable=True,
        extruded=True,
        cell_size=200,
        elevation_scale=4,
    )

    view_state = pdk.ViewState(latitude=df['latitude'].mean(), longitude=df['longitude'].mean(),
                               zoom=11, bearing=0, pitch=45)
    tooltip = {"text": "Price: <b>${price}</b> noi_monthly <b>${noi_monthly}</b>"}

    # Render
    r = pdk.Deck(layers=[gridlayer], initial_view_state=view_state, tooltip=tooltip, )
    return r


def scatterplot(df, json=False):

    if not json:
        data = jsondata(df)
    else:
        data = df

    df = pd.DataFrame(data)
    longitudecenter = df["longitude"].mean()
    latitudecenter = df["latitude"].mean()
    print(data)

    ALL_LAYERS=[
        pdk.Layer(
            "ScatterplotLayer",
            data=data,
            get_position=["longitude", "latitude"],
            get_radius="radius",
            pickable=True,
            opacity=0.8,
            stroked=True,
            filled=True,
            get_color=[255, 165, 0,],
            radius_scale=6,

        ),
        ]

    # Set the viewport location
    # view_state = pdk.ViewState(latitude=33.5, longitude=-112,
    #                            zoom=10, bearing=0, pitch=0)

    # tooltip = {"text": "Price: {price}\nPrice/sqft: {pricesqft}pricesqft\n{address}"}
    # tooltip = {"html": "Price: <b>${price}</b> NOI/mo <b>${noi_monthly}</b> ROI <b>{ROI}%</b> <br>{index}:{address}"}

    # Render
    r = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={"latitude": latitudecenter, "longitude": longitudecenter, "zoom": 10, "pitch": 0},
        layers=ALL_LAYERS,
    )
    return r


def hexagonplot(df):
    data = df.to_json()
    try:
        ALL_LAYERS = {
            "Bike Rentals": pdk.Layer(
                "HexagonLayer",
                data=data,
                get_position=["longitude", "latitude"],
                radius=200,
                elevation_scale=4,
                elevation_range=[0, 1000],
                extruded=True,
            ),

            "Bart Stop Names": pdk.Layer(
                "TextLayer",
                data=data,
                get_position=["longitude", "latitude"],
                get_text="price",
                get_color=[0, 0, 0, 200],
                get_size=15,
                get_alignment_baseline="'bottom'",
            ),
        }
    except urllib.error.URLError as e:
        st.error("""
            **This demo requires internet access.**

            Connection error: %s
        """ % e.reason)
        return

    # Set the viewport location
    view_state = pdk.ViewState(latitude=33.5, longitude=-112,
                               zoom=10, bearing=0, pitch=0)

    # tooltip = {"text": "Price: {price}\nPrice/sqft: {pricesqft}pricesqft\n{address}"}
    tooltip = {"html": "Price: <b>${price}</b> NOI/mo <b>${noi_monthly}</b> ROI <b>{ROI}%</b> <br>{index}:{address}"}

    # Render
    r = pdk.Deck(layers=ALL_LAYERS, initial_view_state=view_state, tooltip=tooltip)
    return r