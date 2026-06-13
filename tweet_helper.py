from requests_oauthlib import OAuth1Session

from constants import (
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET,
    CONSUMER_KEY,
    CONSUMER_SECRET,
    HTTP_CREATED,
    SOCIAL_POST_FOOTER,
)
from yourplace_messages.bot import send_yourplace_post


def publish_tweet(
    tweet_text: str,
    api_url: str,
    *,
    footer_separator: str = "",
    yourplace_first: bool = True,
) -> None:
    tweet_text = f"{tweet_text}{footer_separator}{SOCIAL_POST_FOOTER}"

    if yourplace_first:
        send_yourplace_post(tweet_text)

    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_TOKEN_SECRET,
    )
    response = oauth.post(api_url, json={"text": tweet_text})
    if response.status_code != HTTP_CREATED:
        raise RuntimeError(
            f"Twitter error {response.status_code}: {response.text}"
        )

    print("Tweeted:", tweet_text)

    if not yourplace_first:
        send_yourplace_post(tweet_text)
