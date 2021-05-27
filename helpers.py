# this is a class file (not executable)
import argparse
import configparser
import logging
import os
import re
import time

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
from tabulate import tabulate

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

helperlogs = logging.getLogger("helpers")

headers1 = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/83.0.4103.97 Safari/537.36",
}

headers2 = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Host": "duckduckgo.com",
    "Referer": "https://duckduckgo.com/",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0",
}

headers3 = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
}


def initiate_logging():
    logfile = './logs/scrapemlslogs.log'
    if os.path.exists(logfile):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=logfile)
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=logfile,
                            filemode='w')

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-5s: %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger().addHandler(console)


# def genrandomheaders(verbose):
#     headerslist = [headers1, headers2, headers3]
#     n = np.random.randint(1,3)
#     if verbose:
#         print("Using header #", n)
#     return headerslist[n]


def load_settings(settingsfile='settings'):
    # load configurations from settings file
    if os.path.exists(settingsfile):
        config = configparser.ConfigParser()
        config._interpolation = configparser.ExtendedInterpolation()
        config.read(settingsfile)
        paths = config['Paths']

        PARENT_DIRECTORY = paths['data_dir'] + "/"
        htmldir = paths['data_html'] + "/"
        housingdata = paths['data_housing'] + "/"
        valuationdata = paths['data_valuation'] + "/"
        propertydata = paths['propertydata']
        pricehistoryfile = paths['pricehistoryfile']
        comps = paths['comps']
        mls_search_data = paths['mls_search_data']
        gmail_search_data = paths['gmail_search_data']
        zillow_search_data = paths['zillow_search_data']
        mlsurlsfile = paths['mlsurlsfile']
    else:
        parent_directory = '.'
        PARENT_DIRECTORY = parent_directory + '/data/'
        htmldir = parent_directory + 'scrapedhtml/'
        housingdata = parent_directory + 'housing/'
        valuationdata = parent_directory + "valuation/"
        propertydata = housingdata + 'propertydata.csv'
        pricehistoryfile = housingdata + 'pricehistoryfile.csv'
        comps = valuationdata + 'comps.csv'
        mls_search_data = housingdata + 'mls_search_data.csv'
        gmail_search_data = housingdata + 'gmail_search_data.csv'
        zillow_search_data = housingdata + 'zillow_search_data.csv'
        mlsurlsfile = housingdata + 'mlsurls.csv'

    settings = {'PARENT_DIRECTORY': PARENT_DIRECTORY, 'htmldir': htmldir, 'housingdata': housingdata, 'comps': comps,
                'valuationdata': valuationdata, 'propertydata': propertydata, 'pricehistoryfile': pricehistoryfile,
                'mls_search_data': mls_search_data, 'gmail_search_data': gmail_search_data,
                'zillow_search_data': zillow_search_data, 'mlsurlsfile': mlsurlsfile}

    return settings


def sleepy(sleepytime=2, verbose=False):
    sleeptime = np.random.randint(2, 5) + sleepytime
    if verbose:
        helperlogs.info("Sleeping ... " + str(sleeptime) + " seconds")
    time.sleep(sleeptime)


def extract_dict(df):
    if len(df) == 1:
        extracted_data_row = df.to_dict('index')
        index = list(extracted_data_row.keys())[0]
        extracted_data = extracted_data_row[index]
    else:
        helperlogs.error("Dataframe needs to be of length 1")
        extracted_data = dict()
    return extracted_data


def extractnos(s):
    """
    Extracts number (int or float) from a string. Returns 0 if no number is found.
    :param s:
    :return:
    """
    num = ''.join(re.findall(r'[0-9+]|\.', s)).strip()
    num = re.sub(r'\.+', '.', num)
    try:
        n = int(num)
    except ValueError:
        try:
            n = float(num)
        except ValueError:
            return 0
    return n


def extractno(s):
    """
    Extracts number (int or float) from a string. Returns the string if no number is found.
    :param s:
    :return:
    """
    num = ''.join(re.findall(r'[0-9+]|\.', s)).strip()
    num = re.sub(r'\.+', '.', num)
    try:
        n = int(num)
    except ValueError:
        try:
            n = float(num)
        except ValueError:
            return s
    return n


def extractnofromlist(l):
    try:
        newlist = list(map(lambda x: extractno(x), l))
    except:
        return l
    return newlist


def extractlistingid(out_urls):
    """Extract MLS listing ID"""
    if isinstance(out_urls, list):
        # extract MLS listing ID
        lids = []
        for x in out_urls:
            p = re.findall(r'\d+', x)
            if len(p) > 1:
                lids.append(int(p[1]))
            else:
                lids.append('NA')
        return lids
        # return list(map(lambda x: int(re.findall(r'\d+', x)[1]), out_urls))
    elif isinstance(out_urls, str):
        p = re.findall(r'\d+', out_urls)
        if len(p) > 1:
            return int(p[1])
        else:
            return 'NA'
    else:
        return out_urls


def r(n):
    return np.round(n, 2)


def getvalue(pagesoup, attrib, attribval):
    """Extracts attributes (like class or div) from BeautifulSoup objects"""
    try:
        attribdata = pagesoup.find_all(attrs={attrib: attribval})
        if len(attribdata) == 0:
            return 'NA'
    except:
        return 'NA'

    dataraw = attribdata[0].text

    if len(dataraw) > 0:
        return extractno(dataraw)
    else:
        return dataraw


def gettextfromlist(l):
    try:
        newlist = list(map(lambda x: x.text.strip(), l))
    except:
        return l
    return newlist


def getargs(description=''):
    # parse command-line arguments using argparse()
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--verbose', help='Verbose mode [Default=Off]', action='store_true')

    args = parser.parse_args()

    return args


def geturl(url, header='mls', verbose=False):
    """
    Gets page using requests library. Uses rotating headers.
    :rtype: str
    """
    if url == '':
        helperlogs.error("Error. Empty URL.")
        return -1

    if header == 'zillow':
        header = headers3
    else:
        header = headers1

    page = requests.get(url, headers=header)

    if verbose:
        helperlogs.info("Status code: " + str(page.status_code))

    if page.status_code != 200:
        helperlogs.error("Error. URL not found")
        exit(-1)
    return page.text


def geturl_mod(url, verbose=True):

    if url == '':
        helperlogs.error("Error. Empty URL.")
        return -1

    page = requests.get(url, headers=headers2)

    if verbose:
        helperlogs.info("Status code " + str(page.status_code))

    if page.status_code != 200:
        helperlogs.error("Error. URL not found")
        exit(-1)
    return page.text


def getdatafile(datafile, verbose=True):
    if verbose:
        helperlogs.info("Getting HTML data from file " + datafile)

    if os.path.exists(datafile):
        f = open(datafile, 'r')
        pagetext = f.read()
        f.close()
    else:
        helperlogs.error("File {0} not found.".format(datafile))
        return -1
    return pagetext


def mlslinkfromgooglesearch(googlelinks, websitename):
    links = [x for x in googlelinks if len(re.findall(websitename, x.text)) > 0]
    if len(links) > 0:
        exactmatch = links[0]
        url = exactmatch['href']
        return url
    return ''


def savehtmldata(datafile, data, verbose=False):
    if verbose:
        helperlogs.info("Saving HTML data to file " + datafile)
    f = open(datafile, 'w')
    f.write(data)
    f.close()


def save_to_database(filename, df, keyname1, keyname2=None, overwrite=False, col_order=None, verbose=True):
    """Save a full dataframe by iterating over its rows and making sure the key values are unique.
    (Similar to INSERT of SQL)"""

    if verbose:
        helperlogs.info("save_to_database()")

    if len(df) > 1:
        for index, row in df.iterrows():
            df_one_row = pd.DataFrame(row).T
            keyvalue1 = df_one_row[keyname1].iloc[0]
            if keyname2 is not None:
                keyvalue2 = df_one_row[keyname2].iloc[0]
            else:
                keyvalue2 = ''
            save_to_database_one_row(filename=filename, df=df_one_row, keyname1=keyname1, keyvalue1=keyvalue1,
                                     keyname2=keyname2, keyvalue2=keyvalue2, overwrite=overwrite,
                                     col_order=col_order, verbose=verbose)


def save_to_database_one_row(filename, df, keyname1, keyvalue1='', keyname2=None, keyvalue2='',
                             overwrite=False, col_order=None, verbose=True):
    if verbose:
        helperlogs.info("save_to_database_one_row()")

    # convert all dtypes to str
    df = df.astype(str)

    # if no default column order is given then use dataframe column order
    if col_order is None:
        col_order = df.columns.to_list()

    # save price history
    if os.path.exists(filename):
        df_old = pd.read_csv(filename, dtype=str)

        # if file already contains the data do not add
        mlsno_location = df_old[keyname1].astype('str').str.contains(str(keyvalue1))
        # print(keyname1, keyname2)
        if keyname2 is not None:
            mlsno_location2 = df_old[keyname2].astype('str').str.contains(str(keyvalue2))
            mlsno_location = mlsno_location & mlsno_location2

        if mlsno_location.any() and not overwrite:
            if verbose:
                helperlogs.info(" [ {0}, {1} ] already present in {2} ... Not saving".format(keyvalue1, keyvalue2,
                                                                                             filename))
        else:
            dfnew = make_df_uniq(df_old, keyname1)
            dfnew = dfnew.astype(str)
            dfnew = dfnew.append(df, ignore_index=True)
            dfnew = make_df_uniq(dfnew, keyname1)
            dfnew = dfnew[col_order]
            dfnew.to_csv(filename, index=False)
            if verbose:
                helperlogs.info("Saved {0} to {1}".format(keyvalue1, filename))
    else:
        df = df[col_order]
        df.to_csv(filename, index=False)
        if verbose:
            helperlogs.info("Saved data to " + filename)


def make_df_uniq(df_old, keyname1):
    # make the keyvalue column unique
    uniqlist = []
    keyvalueslist = []
    for i, x in df_old[::-1].iterrows():
        keyval = x[keyname1]
        if not keyval in keyvalueslist:
            keyvalueslist.append(keyval)
            uniqlist.append(x)
    dfnew = pd.DataFrame(uniqlist)
    return dfnew[::-1]


def propertylist(inphx=True, indesiredzone=False, active=True):

    # load configurations from settings file
    settings = load_settings()
    propertydatafile = settings['propertydata']

    if os.path.exists(propertydatafile):
        df = pd.read_csv(propertydatafile)
    else:
        helperlogs.error(propertydatafile + " does not exist")
        exit(-1)
    # data cleaning
    # remove missing data
    df = df[~df['mlsno'].isna()]
    dfmap = df[df['longitude'] != 0]

    # remove properties outside Phoenix
    if inphx:
        dfmap = dfmap[dfmap['longitude'] < -110]
        dfmap = dfmap[dfmap['longitude'] > -112.5]
        dfmap = dfmap[dfmap['latitude'] < 34]
        dfmap = dfmap[dfmap['latitude'] > 33]

    # remove properties outside like zone
    if indesiredzone:
        dfmap = dfmap[dfmap['longitude'] < -111.78]
        dfmap = dfmap[dfmap['longitude'] > -111.997]
        dfmap = dfmap[dfmap['latitude'] < 33.52]
        dfmap = dfmap[dfmap['latitude'] > 33]

    # keep only active properties
    if active:
        df = dfmap[dfmap['Status'] == 'Active']
    else:
        df = dfmap
    return df

