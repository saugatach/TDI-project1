# file needs to executed by running streamlit
# $ streamlit run <filename>
import argparse
import os
import warnings

import numpy as np
import pandas as pd
import streamlit as st
from pandas.core.common import SettingWithCopyWarning

import SessionState
import helpers
import pdk_maps
from getmlsimages import loadmlsimages

st.set_page_config(layout="wide")
session = SessionState.get(a=5)
st.write(session.a)
helpers.initiate_logging()
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)


def getargs():
    # parse command-line arguments using argparse()
    parser = argparse.ArgumentParser(description='Downloads gradebooks from Moodle automatically.')
    parser.add_argument('-l', '--login', help='Stay logged in [Default=Off]. Keep it Off when analysing gradebooks',
                        action='store_true')
    parser.add_argument('-f', '--forcefetchdata', help='Force fetch gradebook [Default=Off]', action='store_true')
    parser.add_argument('-i', '--forcefetchids', help='Force fetch student IDs [Default=Off]', action='store_true')
    parser.add_argument('-o', '--headless', help='Headless mode [Default=Off]', action='store_true')
    parser.add_argument('-v', '--verbose', help='Verbose mode [Default=Off]', action='store_true')
    parser.add_argument('-m', '--hw-links', help='get hw links', action='store_true')

    args = parser.parse_args()
    return args


def update(analyzedfile, dfhousedata):
    if not os.path.exists(analyzedfile):
        return dfhousedata

    mlsno = int(dfhousedata['mlsno'])
    df_analyzed = pd.read_csv(analyzedfile)
    ismlsnopresent = df_analyzed['mlsno'].astype('str').str.contains(str(mlsno))
    if ismlsnopresent.any():
        dftemp = df_analyzed[ismlsnopresent]
        if len(dftemp) > 0:
            dftemp = dftemp[0:1]
        dftemp1 = dfhousedata.set_index('mlsno')
        dftemp2 = dftemp.set_index('mlsno')
        dftemp1.update(dftemp2)
        dfhousedata = dftemp1.reset_index()
    return dfhousedata


def getdecision(analyzedfile, dfhousedata):
    if not os.path.exists(analyzedfile):
        return "No decision yet"

    mlsno = int(dfhousedata['mlsno'])
    df_analyzed = pd.read_csv(analyzedfile)
    ismlsnopresent = df_analyzed['mlsno'].astype('str').str.contains(str(mlsno))
    if ismlsnopresent.any():
        decision = df_analyzed['decision'][ismlsnopresent].to_list()[0]
    else:
        decision = "No decision yet"
    return decision


def goodbadugly(analyzedfile, dfhousedata):
    if not os.path.exists(analyzedfile):
        return 0

    condition = 0

    mlsno = int(dfhousedata['mlsno'])
    df_analyzed = pd.read_csv(analyzedfile)
    ismlsnopresent = df_analyzed['mlsno'].astype('str').str.contains(str(mlsno))
    if ismlsnopresent.any():
        goodorugly = df_analyzed['condition'][ismlsnopresent].to_list()[0]
        if goodorugly == "Ugly":
            condition = 1
    return condition


def loadimagegallery(dfhousedata):
    # start picture gallery
    col1, col2, col3 = st.beta_columns(3)
    images = loadmlsimages(dfhousedata, verbose=True)
    imiter = iter(images)
    while True:
        try:
            im = next(imiter)
            col1.image(im, width=500)
        except:
            break
        try:
            im = next(imiter)
            col2.image(im, width=500)
        except:
            break
        try:
            im = next(imiter)
            col3.image(im, width=500)
        except:
            break


def dashboard(datafile, data_housing):

    analyzedfile = data_housing + 'analyzed-properties.csv'

    df = pd.read_csv(datafile)

    df = pd.read_csv(datafile)

    # data cleaning
    # remove missing data
    df = df[~df['mlsno'].isna()]
    dfmap = df[df['longitude'] != 0]
    # dfmap = dfmap.dropna()

    col1, col2, col3 = st.beta_columns([2, 2, 1])

    with col1:
        if st.checkbox("Only keep properties in the desired zone", value=True):
            # remove properties outside like zone
            dfmap = dfmap[dfmap['longitude'] < -111.78]
            dfmap = dfmap[dfmap['longitude'] > -111.997]
            dfmap = dfmap[dfmap['latitude'] < 33.52]
            dfmap = dfmap[dfmap['latitude'] > 33]
        else:
            # remove properties outside Phoenix
            dfmap = dfmap[dfmap['longitude'] < -110]
            dfmap = dfmap[dfmap['longitude'] > -112.5]
            dfmap = dfmap[dfmap['latitude'] < 34]
            dfmap = dfmap[dfmap['latitude'] > 33]

        # keep only active properties
        dfactive = dfmap[dfmap['Status'] == 'Active']
        dfactive["radius"] = 40
        # sort by ROI
        dfactive.sort_values(by='ROI', ascending=False, inplace=True, ignore_index=True)

        if st.checkbox("Remove properties with a Decision: No "):
            removeno = True
        else:
            removeno = False

        if st.button("Previous"):
            if removeno:
                while True:
                    index = session.a - 1
                    session.a = index
                    if index < 1:
                        index = 1
                        session.a = index
                    dfhousedata = dfactive.iloc[index - 1:index]
                    print(dfhousedata)
                    decision = getdecision(analyzedfile, dfhousedata)
                    print(index)
                    if index == 1:
                        break
                    if decision != 'no':
                        break
            else:
                index = session.a - 1
                session.a = index
                if index < 1:
                    index = 1
                    session.a = index
                index = session.a
                dfhousedata = dfactive.iloc[index - 1:index]

            mlsno = int(dfhousedata['mlsno'])
            # dfhousedata contains only data from propertydata file. It does not contain the user assigned properties
            # like condition:{Good/Ugly} and decision:{Yes/No/Maybe}
            # Load that information from a separate file called analyzed-properties.csv
            decision = getdecision(analyzedfile, dfhousedata)
            condition = goodbadugly(analyzedfile=analyzedfile, dfhousedata=dfhousedata)
            dfhousedata['decision'] = decision
            dfhousedata['condition'] = ['Good', 'Ugly'][condition]

        if st.button("Next"):
            if removeno:
                while True:
                    index = session.a + 1
                    session.a = index
                    if index >= len(dfactive):
                        index = len(dfactive)
                        session.a = index
                    dfhousedata = dfactive.iloc[index - 1:index]
                    decision = getdecision(analyzedfile, dfhousedata)
                    print(index)
                    if index == len(dfactive):
                        break
                    if decision != 'no':
                        break
            else:
                index = session.a + 1
                session.a = index
                if index >= len(dfactive):
                    index = len(dfactive) - 1
                    session.a = index
                index = session.a
                dfhousedata = dfactive.iloc[index - 1:index]

            print(dfhousedata)
            mlsno = int(dfhousedata['mlsno'])
            # dfhousedata contains only data from propertydata file. It does not contain the user assigned properties
            # like condition:{Good/Ugly} and decision:{Yes/No/Maybe}
            # Load that information from a separate file called analyzed-properties.csv
            decision = getdecision(analyzedfile, dfhousedata)
            condition = goodbadugly(analyzedfile=analyzedfile, dfhousedata=dfhousedata)
            dfhousedata['decision'] = decision
            dfhousedata['condition'] = ['Good', 'Ugly'][condition]

        index = session.a
        # set the radius parameter to display scatterplot and then increase radius of selected point
        dfactive['radius'].iloc[index - 1] = 100
        dfhousedata = dfactive.iloc[index - 1:index]

        if st.checkbox("Update data from user chosen RENT and PRICE values"):
            # updata data with saved values
            dfhousedata = update(analyzedfile, dfhousedata)

        housedata = helpers.extract_dict(dfhousedata)
        dfhousedata['PMT'] = dfhousedata['mortgage'] + dfhousedata['hoa'] + dfhousedata['pmi']
        colstodisplay = ['price', 'beds', 'baths', 'sqft', 'pricepersqft', 'rent', 'mortgage', 'hoa', 'pmi', 'PMT',
                         'gestimate_5yr_yoy', 'gestimatecaprate', 'gestimate_sqft', 'zestimate', 'noi_monthly', 'ROI',
                         'Status']
        housedata_display = dfhousedata[colstodisplay]

        # allow user to select rent
        rent = st.slider("Rent:", 700, 3000, int(housedata['rent']))
        # save rent info
        dfhousedata['rent'] = rent
        # allow user to select price
        price = st.slider("Price:", 120000, 300000, int(housedata['price']))
        dfhousedata['price'] = price
        st.success(housedata['url_zillow'])

    with col2:
        st.title('RE property analysis dashboard')
        # st.map(dfactive)
        r = pdk_maps.scatterplot(dfactive, json=False)
        st.pydeck_chart(r)

        condition = goodbadugly(analyzedfile=analyzedfile, dfhousedata=dfhousedata)
        goodorugly = st.radio("Good or Ugly", ("Good", "Ugly"), condition)
        if goodorugly == "Good":
            dfhousedata['condition'] = 'Good'
        if goodorugly == "Ugly":
            dfhousedata['condition'] = 'Ugly'

    with col3:

        decision = getdecision(analyzedfile, dfhousedata)

        if decision is np.nan:
            decision = "No decision yet"

        st.success("Decision: " + decision)
        mlsno = int(dfhousedata['mlsno'])

        if st.button("Yes"):
            dfhousedata['decision'] = 'yes'
            dfnew = helpers.save_to_database_one_row(filename=analyzedfile, df=dfhousedata,
                                                     keyname1='mlsno', keyvalue1=mlsno,
                                                     overwrite=True, verbose=False)
        if st.button("No"):
            dfhousedata['decision'] = 'no'
            helpers.save_to_database_one_row(filename=analyzedfile, df=dfhousedata,
                                             keyname1='mlsno', keyvalue1=mlsno,
                                             overwrite=True, verbose=False)
        if st.button("Maybe"):
            dfhousedata['decision'] = 'maybe'
            print(dfhousedata.to_dict('index'))
            dfnew = helpers.save_to_database_one_row(filename=analyzedfile, df=dfhousedata,
                                                     keyname1='mlsno', keyvalue1=mlsno,
                                                     overwrite=True, verbose=False)

    loadimagegallery(dfhousedata)


if __name__ == '__main__':
    # load configurations from settings file
    settings = helpers.load_settings()
    datafile = settings['propertydata']
    htmldir = settings['htmldir']
    data_housing = settings['housingdata']
    dashboard(datafile, data_housing)
