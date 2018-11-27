from datetime import datetime, timedelta
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import json
import tweepy

# If modifying these scopes, delete the file token.json.
SCOPES = "https://www.googleapis.com/auth/calendar.readonly"


def get_next_event():
    """
    Calls the Calendar API with token.json,
    which stores the user"s access to access the google account.
    Puts next upcoming event in a list.
    """
    store = file.Storage("token.json")
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets("credentials.json", SCOPES)
        creds = tools.run_flow(flow, store)
    service = build("calendar", "v3", http=creds.authorize(Http()))
    now = datetime.utcnow().isoformat() + "Z" # "Z" indicates UTC time
    events_result = service.events().list(calendarId="primary", timeMin=now,
                                        maxResults=1, singleEvents=True,
                                        orderBy="startTime").execute()
    next_event = events_result.get("items", [])
    return next_event


def select_event_data(next_event):
    """
    Selects summary, turns start and end into datetime objects,
    creates target_date as datetime.date object, formated for scheduling.
    Saves data in a dictionary.
    """
    if not next_event:
        raise NoEventsFound(Exception)

    event = next_event[0]
    summary = event["summary"]
    start = event["start"].get("dateTime", event["start"].get("date"))
    end = event["end"].get("dateTime", event["end"].get("date"))
    start_datetime = datetime.strptime(f"{start}", "%Y-%m-%dT%H:%M:%SZ")
    end_datetime = datetime.strptime(f"{end}", "%Y-%m-%dT%H:%M:%SZ")
    
    data_event = {"target_date": start_datetime.date(),
                  "summary": f"{summary}",
                  "start": start_datetime,
                  "end": end_datetime
                  }
    return data_event


        
def time_to_event(data_event):
    """
    Calculates and returns time from now to next event.
    """
    if not data_event:
        raise NoEventsFound()
    now = datetime.now().date()
    target_date = data_event["target_date"]
    diff = now - target_date
    return(diff)


def format_date(dt):
    """
    Function to format datetime object as string: weekday, day, month, year.
    """
    return datetime.strftime(dt, "%A, %d %B %Y")


def format_date_short(dt):
    return datetime.strftime(dt, "%d %B")


def format_hour(dt):
    """
    Function to format datetime object as string: hour, minute, AM/PM.
    """
    return datetime.strftime(dt, "%I.%M %p")


def create_tweet(data_event, diff):
    """
    If next event at a certain interval to now, returns tweet.
    """
    summary = data_event["summary"]
    date_month_year = format_date(data_event["start"])
    start_hour = format_hour(data_event["start"])
    end_hour = format_hour(data_event["end"])
    date_month = format_date_short(data_event["start"])

    if diff == timedelta(days=-7):
        tweet = f"Our next {summary} will take place" \
                + f" on {date_month_year}, from {start_hour}" \
                + f" to {end_hour}." \
                + " Send us a DM on the day to receive a link to the private chat on Telegram."

        return tweet

    elif diff == timedelta(days=-4):
        tweet = f"We hold private chats for #bisexual survivors every two weeks." \
                + f" The next one will be this {date_month_year}, from {start_hour}" \
                + f" to {end_hour}." \
                + " Send us a DM on the day to receive a link to the chat on Telegram."

        return tweet

    elif diff == timedelta(days=-3):
        tweet = f"We'll be hosting our next {summary} on {date_time_year}." \
                + " It’s private, online and moderated by a non-monosexual survivor." \
                + " Send us a DM on the day to receive a link to the chat on Telegram."

    elif diff == timedelta(days=-1):
        tweet = "As always, you can receive the secret link to our chat tomorrow" \
                + " by sending us a DM! The chat will be moderated by a non-monosexual"\
                + f" survivor and take place from {start_hour}" \
                + f" to {end_hour}, UK time."

##                f"Quick reminder! Our chat for #bisexual survivors will be" \
##                + f"going live tomorrow, {start_hour} UK time." \
##                + " Download Telegram in advance so you’re ready!"

        return tweet

    elif diff == timedelta(days=0):
        tweet = "Our next private chat for bi survivors is happening tonight," \
                + f" from {start_hour} to {end_hour}." \
                + " Send us a DM to receive a link to the chat on Telegram."

        return tweet

    else:
        raise EventNotInRange(Exception)
    

def send_tweet(tweet):
    """
    Opens json file with access tokens and twitter api keys.
    Checks length of tweet, if over 240 raises error.
    Otherwise, publishes tweet on timeline.
    """
    with open ("twitter_access_token.json", "r") as f:
        tokens = json.load(f)
        access_token = tokens["access_token"]
        access_token_secret = tokens["access_token_secret"]
        
    with open ("twitter_api_key.json", "r") as f:
        keys = json.load(f)
        api_key = keys["api_key"]
        api_secret_key = keys["api_secret_key"]

    auth = tweepy.OAuthHandler(f"{api_key}", f"{api_secret_key}")
    auth.set_access_token(f"{access_token}", f"{access_token_secret}") 
    api = tweepy.API(auth)

    if len(tweet) > 240:
        raise TweetTooLong(Exception)

    else:
        print(tweet)
        api.update_status(tweet) # Uncomment to send tweet


def get_last_10_tweets():
    '''
    Checks access to twitter by
    retrieving last 10 tweets from timeline.
    '''
    with open ("twitter_access_token.json", "r") as f:
        tokens = json.load(f)
        access_token = tokens["access_token"]
        access_token_secret = tokens["access_token_secret"]
    with open ("twitter_api_key.json", "r") as f:
        keys = json.load(f)
        api_key = keys["api_key"]
        api_secret_key = keys["api_secret_key"]
        
    auth = tweepy.OAuthHandler(f"{api_key}", f"{api_secret_key}")
    auth.set_access_token(f"{access_token}", f"{access_token_secret}") 
    api = tweepy.API(auth)
    
    public_tweets = api.home_timeline()
    for tweet in public_tweets:
        print(tweet.text)


def main():
    # Put a try here because of NoEventsFound error??
    next_event = get_next_event()
    data_event = select_event_data(next_event)
    diff = time_to_event(data_event)
    # get_last_10_tweets()  # Uncomment to check twitter access
    try:
        tweet = create_tweet(data_event, diff)
        send_tweet(tweet)
    except NoEventsFound:
        print("No events found.")
    except EventNotInRange:
        print("Event is not in range.")
    except TweetTooLong:
        print("Tweet has over 240 characters.")


class EventNotInRange(Exception):
    pass


class NoEventsFound(Exception):
    pass


class TweetTooLong(Exception):
    pass


if __name__ == "__main__":
    main()
