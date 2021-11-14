# tweetutilities.py
"""Utility functions for interacting with Tweepy objects."""
from geopy import OpenMapQuest
import keys
from textblob import TextBlob 
import time 
import tweepy
import streamlit as st

def get_API(wait=True, notify=True):
    """Authenticate with Twitter and return API object."""
    # configure the OAuthHandler
    auth = tweepy.OAuthHandler(st.secrets["consumer_key"], st.secrets["consumer_secret"])
    auth.set_access_token(st.secrets["access_token"], st.secrets["access_token_secret"])
    # auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
    # auth.set_access_token(keys.access_token, keys.access_token_secret)

    # get the API object
    return tweepy.API(auth, wait_on_rate_limit=wait, 
                      wait_on_rate_limit_notify=notify)

def print_tweets(tweets):
    """For each Tweepy Status object in tweets, display the 
    user's screen_name and tweet text. If the language is not
    English, translate the text with TextBlob."""
    for tweet in tweets:
        print(f'{tweet.user.screen_name}:', end=' ')
    
        if 'en' in tweet.lang:
            print(f'{tweet.text}\n')
        elif 'und' not in tweet.lang:  # translate to English first
            print(f'\n  ORIGINAL: {tweet.text}')
            print(f'TRANSLATED: {TextBlob(tweet.text).translate()}\n')

def get_tweet_content(tweet, crypto, location=False):
    """Return dictionary with data from tweet (a Status object)."""
    fields = {}
    fields['crypto'] = crypto
    fields['screen_name'] = tweet.user.screen_name
    dtime = tweet.created_at
    d_time = dtime.strftime("%m/%d/%Y, %H:%M:%S")
    fields['created_at'] = d_time
    # get the tweet's text
    try:  
        fields['text'] = tweet.extended_tweet.full_text
    except: 
        fields['text'] = tweet.text

    if location:
        fields['location'] = tweet.user.location

    return fields

def get_geocodes(tweet_list):
    """Get the latitude and longitude for each tweet's location.
    Returns the number of tweets with invalid location data."""
    print('Getting coordinates for tweet locations...')
    geo = OpenMapQuest(api_key=st.secrets["mapquest_key"])  # geocoder
    # geo = OpenMapQuest(api_key=keys.mapquest_key)
    bad_locations = 0  

    for tweet in tweet_list:
        processed = False
        delay = .1  # used if OpenMapQuest times out to delay next call
        while not processed:
            try:  # get coordinates for tweet['location']
                geo_location = geo.geocode(tweet['location'])
                processed = True
            except:  # timed out, so wait before trying again
                print('OpenMapQuest service timed out. Waiting.')
                time.sleep(delay)
                delay += .1

        if geo_location and geo_location.latitude != None:  
            tweet['latitude'] = geo_location.latitude
            tweet['longitude'] = geo_location.longitude
        else:  
            bad_locations += 1  # tweet['location'] was invalid
    
    print('Done geocoding')
    return bad_locations


