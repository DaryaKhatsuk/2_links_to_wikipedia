import asyncio
import logging
import re
import time
from urllib.parse import urljoin

from aiohttp import ClientSession
from fake_useragent import UserAgent

logging.basicConfig(filename='search.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_DEPTH = 3
final_title = ''


async def get_url_from_title(session, title):
    url = f'https://ru.wikipedia.org/w/index.php?title=Special:Search&limit=1&offset=0&ns0=1&search={title}'
    html = await fetch(session, url)
    links = re.findall(r'<a href="(/wiki/[^"]+)"', html)
    if links:
        return 'https://ru.wikipedia.org' + links[0]
    else:
        return None


async def fetch(session, url):
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    async with session.get(url, headers=headers) as response:
        return await response.text()


async def get_links(session, url):
    html = await fetch(session, url)
    links = re.findall(r'<a href="([^"]+)"[^>]*>(.*?)</a>', html)
    links = [(urljoin(url, link), title) for link, title in links if 'wikipedia.org' in link]
    return links


async def search_links(session, current_url, target_title, path, depth=3, visited=None):
    if visited is None:
        visited = set()

    if depth < 0:
        return None

    if current_url in visited:
        return None

    visited.add(current_url)

    html = await fetch(session, current_url)
    title = re.search(r'<firstHeading>(.*?) - Wikipedia</firstHeading>', html).group(1)
    print(html, title)
    if title == target_title:
        return path + [(f'"{title}"', current_url)]

    links = await get_links(session, current_url)
    for link, link_title in links:
        logging.info(f'Visiting {link}')
        subpath = await search_links(session, link, target_title, path + [(f'"{link_title}"', link)], depth=depth - 1,
                                     visited=visited)
        if subpath is not None:
            return subpath

    return None


# async def search_links(session, current_url, target_url, path, visited_urls, depth=3):
#     target_title = re.search(r'/([^/]+)$', link)
#     if depth < 0:
#         return None
#     if current_url == target_url:
#         return path
#
#     if current_url in visited_urls:
#         return None
#
#     visited_urls.add(current_url)
#
#     links = await get_links(session, current_url)
#
#     for link in links:
#         if 'wikipedia.org' not in link:
#             continue
#
#         if link in visited_urls:
#             continue
#
#         logging.info(f'Visiting {link}')
#         new_path = path + [(link, '')]
#
#         html = await fetch(session, link)
#         soup = BeautifulSoup(html, 'html.parser')
#         title_tag = soup.find('h1', {'class': 'firstHeading'})
#         if title_tag is None:
#             continue
#         title = title_tag.text.replace(' ', '_')
#         print(title_tag)
#         title_compar = re.search(r'/([^/]+)$', link)
#         print(title_compar)
#         if link == target_url and (title_compar == title):
#             return new_path
#
#         if title.lower() in {'error', 'not found', 'page not found', '404 not found', 'page does not exist'}:
#             continue
#
#         subpath = await search_links(session, link, target_url, new_path, visited_urls, depth=depth-1)
#         if subpath is not None:
#             sentence, next_link = subpath[0]
#             subpath[0] = (sentence, link)
#             return new_path + subpath[1:]
#
#     return None


async def main():
    start_url = input('Enter start URL: ')
    target_url = input('Enter target URL: ')
    async with ClientSession() as session:
        target_url = await get_url_from_title(session, target_url)
        if target_url is None:
            print(f"Couldn't find a page with title '{target_url}'.")
        else:
            path = await search_links(session, start_url, target_url, depth=3)
            if path is not None:
                for i, (sentence, link) in enumerate(path):
                    print(f'{i + 1}. {sentence} ({link})')
            else:
                print('No path found')


if __name__ == '__main__':
    x = time.time()
    asyncio.run(main())
    y = time.time()
    print(y - x)
