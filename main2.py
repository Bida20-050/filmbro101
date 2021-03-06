
import random
import tweepy
import logging
import os
import time
import datetime

MAX_TWEET_SIZE = 1000
WAIT_TIME_HOURS_DEFAULT = 6
WAIT_TIME_HOURS = float(os.getenv("WAIT_TIME_HOURS", default=WAIT_TIME_HOURS_DEFAULT))

START_HOUR = os.getenv('START_HOUR')

ACCOUNT_NAME = os.getenv('ACCOUNT_NAME', default='slowburn2502')


def run_bot(input_file: str, wait_time_hours: float) -> None:
    """Get texts from file, format into tweets, tweet and wait"""

    texts = get_texts('tweets.txt', shuffle=True)
    while True:
        for text in texts:
            logging.info(text)
            tweets = get_individual_tweets_from_text(text)
            id_of_thread_tweet_to_reply_to = None
            for tweet in tweets:
                logging.info(tweet)
                delete_existing_tweets_with_same_text(api, tweet)  # remove old same tweet as duplicate tweets are not allowed by Twitter
                call_return_status = api.update_status(tweet, id_of_thread_tweet_to_reply_to)
                logging.info(call_return_status)
                id_of_thread_tweet_to_reply_to = call_return_status.id

                time.sleep(60*60*wait_time_hours)  # turn hours into seconds


auth = tweepy.OAuthHandler("PXytT3aIBJsjfpiMwOjrI1pWy",
    "cRTYBrCpauE4gZU69mzabErj2tmHVKyjslPsulTyaQzo9nOcWu")
auth.set_access_token("1504421699206459392-Ff7RKf0kLfw8MwDZ55OjljAQjJudz9",
    "a6ZKcRVx4TxM3tr6khbxKfeouhhj2YtrIUdEanVuA59Pc")
api = tweepy.API(auth, wait_on_rate_limit=True)

def get_texts(tweets: str, shuffle=False) -> list:

    with open('tweets.txt', 'r') as f:
        texts = f.read().splitlines()

    if shuffle:
        random.shuffle(texts)

    return texts


def get_individual_tweets_from_text(text, max_length=MAX_TWEET_SIZE) -> list:
    """Check whether we can take the text as-is as tweet or have to split it into multiple tweets"""
    if len(text) <= max_length:
        tweets = [text]
    else:
        tweets = list(split_text_into_multiple_tweets(text, max_length))
        tweets = [tweet.replace('/0', f'/{len(tweets)}') for tweet in tweets]

    return tweets


def split_text_into_multiple_tweets(text: str, max_length: int = MAX_TWEET_SIZE) -> list:

    words = text.split()

    # start string with first word, then begin loop on second
    tweet_number = 1
    new_tweet = f"{tweet_number}/0"

    for word in words:

        if len(new_tweet + ' ' + word + ' ...') < max_length:  # if tweet is short enough with word appended, keep appending
            new_tweet = new_tweet + ' ' + word
        else:
            yield new_tweet + ' ...'
            tweet_number += 1
            new_tweet = f"{tweet_number}/0 ... " + word
    yield new_tweet


def wait_until_certain_hour_to_start(start_hour: int) -> None:
    """Tweeting should start at a certain hour, not when the script starts"""
    while datetime.datetime.now().hour != start_hour:
        logging.info("Current hour: {datetime.datetime.now().hour},  start hour: {start_hour}  -> waiting ...")
        time.sleep(30*60)   # wait half an hour, then check again
    logging.info("Current hour: {datetime.datetime.now().hour} ==  start hour: {start_hour}")


def delete_existing_tweets_with_same_text(api: tweepy.API, tweet: str) -> None:
    results = api.search_tweets(q=tweet, tweet_mode='extended')

    for result in results:

        if result.user.screen_name == ACCOUNT_NAME and result.full_text == tweet:
            print(f"Deleting tweet {result.id}")
            api.destroy_status(result.id)


if __name__ == '__main__':

    if START_HOUR is not None:
        wait_until_certain_hour_to_start(start_hour=int(START_HOUR))
        run_bot(wait_time_hours=WAIT_TIME_HOURS, input_file='tweets.txt')
