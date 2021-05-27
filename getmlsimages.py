#!/usr/bin/env python
import argparse
import logging
import os
import re
import warnings

import pandas as pd
import requests
from PIL import Image
import helpers
from pandas.core.common import SettingWithCopyWarning
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

getmlsimages_logs = logging.getLogger('getmlsimages')

# load configurations from settings file
settings = helpers.load_settings()
datafile = settings['propertydata']
htmldir = settings['htmldir']


def loadmlsimages(dfhousedata, sleep=0, verbose=False):

    if verbose:
        getmlsimages_logs.info("loadmlsimages()")

    if isinstance(dfhousedata, pd.DataFrame):
        url = dfhousedata['url_mls'][dfhousedata.index[0]]
    elif isinstance(dfhousedata, pd.Series):
        url = dfhousedata['url_mls']
    elif isinstance(dfhousedata, dict):
        url = dfhousedata['url_mls']
    else:
        getmlsimages_logs.error("Wrong dtype passed to loadmlsimages()")

    if verbose:
        getmlsimages_logs.info("Getting images for MLS URL " + url)

    listingkey = re.findall(r'listings/(\d+)', url)[0]
    datafile_mls = htmldir + str(listingkey) + '.html'
    pagetext = helpers.getdatafile(datafile=datafile_mls, verbose=verbose)
    # if the HTML data cannot be loaded or forceload=TRUE then fetch webpage
    if pagetext == -1:
        pagetext = helpers.geturl(url)
        # and save it in file
        helpers.savehtmldata(datafile=datafile_mls, data=pagetext, verbose=verbose)

    mlsimages = re.findall('https.*?resize.*?jpg', pagetext)
    images = []
    for url in mlsimages:
        # check if images are present locally
        imagefile = htmldir + re.findall(r'/(\d+\-o\.jpg)', url)[0]

        if os.path.exists(imagefile):
            if verbose:
                getmlsimages_logs.info("Getting from file: " + imagefile)
            image = Image.open(imagefile)
        else:
            if verbose:
                getmlsimages_logs.info("Getting from URL: " + url)
            response = requests.get(url, stream=True)
            response.raw.decode_content = True
            try:
                image = Image.open(response.raw)
            except:
                getmlsimages_logs.error("Unable to grab image")
                continue
            image.save(imagefile)
            helpers.sleepy(sleep)

        images.append(image)

    return images


def loadsettings():
    # load configurations from settings file
    settings = helpers.load_settings()
    incsv = settings['mlsurlsfile']
    housingdata = settings['housingdata']
    propertydatafile = settings['propertydata']
    tempcsv = housingdata + 'temp.csv'
    analyzedfile = housingdata + 'analyzed-properties.csv'
    return propertydatafile, analyzedfile


def filterproperty(args):
    verbose = args.verbose
    dfactive = helpers.propertylist(inphx=True, indesiredzone=False, active=True)
    for i, df in dfactive.iterrows():
        images = loadmlsimages(df, sleep=0, verbose=verbose)


if __name__ == '__main__':
    helpers.initiate_logging()
    args = helpers.getargs()
    filterproperty(args)









