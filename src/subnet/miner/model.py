import os
import asyncio
from twikit import Client
from communex.module import Module, endpoint
from communex.key import generate_keypair
from keylimiter import TokenBucketLimiter

class Miner(Module):
    def __init__(self):
        super().__init__()
        self.client = Client('en-US')

    @endpoint
    async def generate(self, prompt: str, start_time: str = '2024-04-01T5:00:00Z', max_results: int = 50):
        if os.path.exists('twitter_cookies.json'):
            self.client.load_cookies('twitter_cookies.json')
        else:
            username = os.getenv('TWITTER_USERNAME')
            email = os.getenv('TWITTER_EMAIL')
            password = os.getenv('TWITTER_PASSWORD')
            if not all([username, email, password]):
                raise ValueError("Missing Twitter credentials. Please check your environment variables.")
            await self.client.login(auth_info_1=username, auth_info_2=email, password=password)
            self.client.save_cookies('twitter_cookies.json')

        tweets = await self.client.search_tweet(prompt, 'Latest')
        
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

        return {"data": results}

if __name__ == "__main__":
    from communex.module.server import ModuleServer
    import uvicorn

    key = generate_keypair()
    miner = Miner()
    refill_rate = 1 / 400
    bucket = TokenBucketLimiter(2, refill_rate)
    server = ModuleServer(miner, key, ip_limiter=bucket, subnets_whitelist=[17])
    app = server.get_fastapi_app()
    
    # Only allow local connections
    uvicorn.run(app, host="0.0.0.0", port=8000)