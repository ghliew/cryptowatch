import json, tweepy, keys, geopy
import streamlit as st
import pandas as pd
import yfinance as yf
import datetime as dt
import numpy as np
from dateutil.relativedelta import relativedelta
from pandas_datareader import data as pdr
from tweetutilities import get_API, get_geocodes
from locationlistener import LocationListener
from pymongo import MongoClient
import folium
import folium.plugins as plugins
from streamlit_folium import folium_static

#Database
atlas_client = MongoClient(st.secrets["mongo_connection_string"])
# atlas_client = MongoClient(keys.mongo_connection_string)
db = atlas_client.crypto 

# Crypto list of top 10 crypto by market cap
crypto_list = ['Bitcoin - BTC-USD', 'Ethereum - ETH-USD', 'Cardano - ADA-USD', 'BinanceCoin - BNB-USD', 
               'Ripple -XRP-USD ', 'Solana - SOL1-USD', 'Polkadot - DOT1-USD', 'Dogecoin - DOGE-USD', 
               'Avalanche - AVAX-USD', 'LunaTerra - LUNA1-USD', 'Select a Cryptocurrency']

#System Strings
TEXT_SIDEBAR = '''#### Connect With Me:
- 🌐 [Website](https://ghliew.github.io)
- 💻 [GitHub](https://github.com/ghliew/cryptowatch)
- 👨‍💻 [LinkedIn](https://www.linkedin.com/in/guang-hui-liew/)
'''
TEXT_PRICE = '''## {} - {} 
## Current Price: {}  {}
'''

@st.cache()
def get_crypto_data():
    '''Read Crypto table into a Dataframe'''
    SNP_TABLE_URL = "https://codepen.io/npatel023/pen/eapKPo#!"
    html = pd.read_html(SNP_TABLE_URL, header=0)
    df = html[0]
    return df

def get_stock_df(ticker):
    '''Get a ticker's price from start date to end date and return in a Dataframe'''
    # enddate = dt.datetime.now()
    # startdate = dt.datetime.now() - relativedelta(years=1)
    # df = pdr.get_data_yahoo(ticker, start=startdate, end=enddate)
    enddate = dt.datetime.now()
    startdate = dt.datetime.now() - relativedelta(hours=24)
    df = yf.download(ticker, start=startdate, end=enddate, interval='1h')
    return df

def get_price_chg_str(df_sym):
    '''Return a str with stock price and percentage change from yesterday'''
    close_prev = df_sym['Close'].values[0]
    close_latest =  df_sym['Close'].values[-1]
    price_chg = (close_latest/close_prev-1)*100
    price_chg_color = 'green' if price_chg>0 else 'red'
    price_chg_sign = '+' if price_chg>0 else ''
    price_chg_str = '<span style="color:{}">{}{:.2f}%</span>'.format(price_chg_color, price_chg_sign, price_chg)
    return price_chg_str

def get_tweets(crypto_name, num_tweet):
    '''Get tweets and store in database'''
    api = get_API()
    tweets = []
    counts = {'total_tweets': 0, 'locations': 0}
    location_listener = LocationListener(api, counts_dict=counts, 
        tweets_list=tweets, topic=crypto_name, limit=num_tweet)
    stream = tweepy.Stream(auth=api.auth, listener=location_listener)
    stream.filter(track=[crypto_name], languages=['en'], is_async=False)  
    bad_locations = get_geocodes(tweets)
    num = counts['locations'] - bad_locations
    st.sidebar.write(f'{num} tweets with valid locations stored in database')
    df = pd.DataFrame(tweets)
    df = df.dropna()
    crypto_dict = df.to_dict('records')
    return crypto_dict

# @st.cache()
def get_data():
    df_db = pd.DataFrame(list(db.tweets.find()))
    return df_db


#####################
### Streamlit UI  ###
#####################
st.set_page_config(page_title="Crypto Watch 💰")

st.title("Crypto Watch 💰")

st.markdown(''' 
    Crypto currencies are highly speculative, at lease for the moment. \n
    Prices can greatly fluctuate over regulation news, rumours, etc. So it is good to keep an eye on on-going discussions
    on Twitter and see where the discussions are coming from. \n
    This application provides:
    * Latest price of crypto currencies
    * Display tweets stored in database
    * Pull and store live tweets into database
    * Map of tweets stored in database
''')

select_string = st.selectbox("", crypto_list, index=(len(crypto_list)-1))
crypto_name = select_string.split()[0]
crypto_ticker = select_string.split()[2]

## Sidebar Section
st.sidebar.header("Database")
num_display = st.sidebar.slider("Number of Tweets to Display", 1, 20, 10, 1)
num_tweet = st.sidebar.slider("Number of Live Tweets to Pull into Database", 1, 10, 5, 1)
if st.sidebar.button("Stream Tweets Into Database"):
    if crypto_name != 'Select':
        crypto_dict = get_tweets(crypto_name, num_tweet)
        for t in crypto_dict:
            json_object = json.dumps(t)
            json_data = json.loads(json_object)  # convert string to JSON
            db.tweets.insert_one(json_data)  # store in tweets collection
    else: st.sidebar.write('Please select a cryptocurrency first')
st.sidebar.write(TEXT_SIDEBAR)

## Main Section
if crypto_ticker!="Cryptocurrency":
    crypto_price = yf.Ticker(crypto_ticker)
    
    # with st.expander(f"📘 - See {crypto_ticker} Explanation"):
        # st.write(crypto_price.info['description'])
    df_crypto_price = get_stock_df(crypto_ticker)
    price_chg_str = get_price_chg_str(df_crypto_price)
    st.write(TEXT_PRICE.format(
        crypto_name,
        crypto_ticker,
        "{:.2f}".format(df_crypto_price['Close'].values[-1]),
        price_chg_str
    ), 
    unsafe_allow_html=1)

   
    st.header('Recent Tweets')
    # crypto_df = pd.DataFrame(list(db.tweets.find()))
    crypto_df = get_data()
    del crypto_df['_id']
    crypto_ticker_df = crypto_df[crypto_df['crypto']==crypto_name]
    # crypto_ticker_df.index = np.arange(1, len(crypto_ticker_df)+1)
    st.write(crypto_ticker_df.tail(num_display))

    st.header('Tweet Map')
    # Load map centred on US
    usmap = folium.Map(location=[39.8283, -98.5795], zoom_start=5, detect_retina=True)
    # Load a marker cluster called "Crypto tweet cluster"
    marker_cluster = plugins.MarkerCluster().add_to(usmap)
    
    for t in crypto_ticker_df.itertuples():
        # text = ': '.join([t.screen_name, t.text, t.created_at])
        text = f'{t.screen_name}: {t.text}, Created at: {t.created_at}'
        popup = folium.Popup(text, parse_html=True)
        marker = folium.Marker((t.latitude, t.longitude), popup=popup).add_to(marker_cluster)
        # marker.add_to(usmap)
       
    folium_static(usmap)
