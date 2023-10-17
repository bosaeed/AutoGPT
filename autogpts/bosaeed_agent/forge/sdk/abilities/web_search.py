import requests
import asyncio
import pprint


from bs4 import BeautifulSoup
# from playwright.async_api import async_playwright
import urllib.request

from ..forge_log import ForgeLogger
from .registry import ability

logger = ForgeLogger(__name__)

# @ability(
#     name="search_web",
#     description="Use this to search web about any topic",
#     parameters=[
#         {
#             "name": "query",
#             "description": "a query to search",
#             "type": "string",
#             "required": True,
#         }
#     ],
#     output_type="str",
# )
# async def search_web(agent, task_id: str, query:str):
    # headers = {
    #     # 'User-agent':
    #     # 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        
    # }

    # params = {
    # 'q': query,
    # 'format': 'json',
    # }

    # html = requests.get('http://localhost:8899/search', headers=headers, params=params)
    # result = html.json()['results']
    # # logger.info(pprint.pformat(result))
    # # logger.info(type(result))
    # result = result[0:4]
    # output = ""
    # # count = 0
    # # max_count = 4
    # for r in result:
    #     output += "title: "+ r["title"] +"\n"
    #     output += "url: "+ r["url"] +"\n"
    #     output += "content: "+ r["content"] +"\n"
    #     output += ",\n"
    #     # count +=1
    #     # if count>max_count:
    #     #     break

    # logger.info(output)
    # return output