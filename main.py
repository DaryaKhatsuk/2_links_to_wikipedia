import asyncio
import logging
import re

import aiohttp
from bs4 import BeautifulSoup


async def search_links(session, current_url, target_url, target_title, path, depth=3, visited=None):
    if visited is None:
        visited = set()
    visited.add(current_url)
    if depth == 0:
        return None
    async with session.get(current_url) as response:
        text = await response.text()
        soup = BeautifulSoup(text, 'html.parser')
        body_content = soup.find('div', id='bodyContent', class_='vector-body')
        print(body_content)
        if not body_content:
            return None
        match = body_content.find('h1', id='firstHeading', class_='firstHeading')
        print(match)
        if match and match.get_text().strip() == target_title:
            return path + [(match.get_text(), current_url)]
        links = body_content.find_all('a', href=re.compile(r'^/wiki/[^:]+$'))
        for link in links:
            next_url = f"https://en.wikipedia.org{link['href']}"
            if next_url not in visited:
                next_path = await search_links(session, next_url, target_url, target_title,
                                               path + [(link.get_text(), next_url)], depth - 1, visited)
                if next_path is not None:
                    return next_path
        return None


async def find_path(start_url, target_url, target_title, depth=3):
    async with aiohttp.ClientSession() as session:
        path = await search_links(session, start_url, target_url, target_title, [], depth=depth)
        return path


async def main():
    start_url = 'https://en.wikipedia.org/wiki/Xbox_360_S'
    target_url = 'https://ru.wikipedia.org/wiki/Nintendo_3DS'
    target_title = str(re.search(r'/([^/]+)$', target_url)).replace('_', ' ')
    path = await find_path(start_url, target_url, target_title, depth=3)
    if path:
        print("Path:")
        for i, (url, text) in enumerate(path):
            print(f"{i + 1}------------------------")
            match = re.search(f'<a href="({target_url})"[^>]*>', text)
            if match:
                link_text = match.group(0)
                start_index = text.rindex(">", 0, match.start()) + 1
                end_index = text.index("</a>", match.end())
                link_text += text[start_index:end_index]
                print(link_text)
            else:
                print(url)
    else:
        print("No path found")


if __name__ == '__main__':
    logging.basicConfig(filename='search.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info('Starting search')
    asyncio.run(main())
