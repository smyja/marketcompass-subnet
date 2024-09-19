import asyncio
import os
import logging
import json
from twikit import Client


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def search_tweets(query: str, max_results: int = 50):
    client = Client('en-US')

    if os.path.exists('twitter_cookies.json'):
        logger.info("Loading existing cookies...")
        client.load_cookies('twitter_cookies.json')
    else:
        logger.info("No existing cookies found. Logging in...")
        username = os.getenv('TWITTER_USERNAME')
        email = os.getenv('TWITTER_EMAIL')
        password = os.getenv('TWITTER_PASSWORD')

        if not all([username, email, password]):
            logger.error("Missing Twitter credentials. Please check your .env file or environment variables.")
            raise ValueError("Missing Twitter credentials")

        try:
            await client.login(auth_info_1=username, auth_info_2=email, password=password)
            client.save_cookies('twitter_cookies.json')
            logger.info("Login successful. Cookies saved.")
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return []

    logger.info(f"Searching for tweets with query: '{query}'...")
    try:
        tweets = await client.search_tweet(query, 'Latest')
    except Exception as e:
        logger.error(f"Error searching tweets: {str(e)}")
        return []

    results = []
    for tweet in tweets:
        tweet_data = {
            "author_id": getattr(tweet.user, 'id', None),
            "created_at": getattr(tweet, 'created_at', None),
            "id": getattr(tweet, 'id', None),
            "text": getattr(tweet, 'full_text', getattr(tweet, 'text', None))
        }
        results.append(tweet_data)
        
        if len(results) >= max_results:
            break
        await asyncio.sleep(0.5)

    logger.info(f"Found {len(results)} tweets")
    return results

async def main():
    search_query = "Taylor swift"
    tweet_results = await search_tweets(search_query, max_results=10)
    
    if not tweet_results:
        logger.warning("No results found or an error occurred.")
        return

    output = {"data": tweet_results}
    print(json.dumps(output, indent=4))

if __name__ == "__main__":
    asyncio.run(main())