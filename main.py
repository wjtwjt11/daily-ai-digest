import argparse
import asyncio
from datetime import datetime
from pathlib import Path

import aiohttp
import feedparser

# Simulated LLM scoring (replace with actual LLM API call in production)
def llm_score(title, description):
    # Simple heuristic: longer title + description with keywords = higher score
    keywords = ['ai', 'llm', 'release', 'paper', 'update', 'trending']
    combined = f"{title} {description}".lower()
    return sum(1 for kw in keywords if kw in combined) + len(title) / 50

async def fetch_feed(session, url):
    async with session.get(url) as resp:
        if resp.status != 200:
            return []
        text = await resp.text()
        parsed = feedparser.parse(text)
        items = []
        for entry in parsed.entries[:10]:
            items.append({
                'title': entry.get('title', ''),
                'description': entry.get('summary', '')[:200],
                'link': entry.get('link', ''),
            })
        return items

async def main(feeds_file, output_file):
    aggregate = []
    async with aiohttp.ClientSession() as session:
        # Read feeds from local file (one URL per line)
        feeds = Path(feeds_file).read_text().splitlines() if Path(feeds_file).exists() else [
            'https://news.ycombinator.com/rss',
            'https://www.phoronix.com/rss.php'
        ]
        for feed_url in feeds:
            if not feed_url.strip():
                continue
            items = await fetch_feed(session, feed_url.strip())
            aggregate.extend(items)
    
    # Score and rank
    for item in aggregate:
        item['score'] = llm_score(item['title'], item['description'])
    aggregate.sort(key=lambda x: x['score'], reverse=True)
    
    # Generate daily digest markdown
    top5 = aggregate[:5]
    today = datetime.now().strftime('%Y-%m-%d')
    content = f"# Daily Digest {today}\n\n"
    for i, item in enumerate(top5, 1):
        content += f"## {i}. {item['title']}\n\n"
        content += f"{item['description']}... [link]({item['link']})\n\n"
    
    Path(output_file).write_text(content)
    print(f"Digest written to {output_file} with {len(top5)} items.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--feeds', default='feeds.txt', help='File with RSS URLs')
    parser.add_argument('--output', default='daily_digest.md', help='Output markdown file')
    args = parser.parse_args()
    asyncio.run(main(args.feeds, args.output))
