import asyncio
import csv
from bs4 import BeautifulSoup
import aiohttp

CATEGORY_URL = "https://www.gorgany.com/odiah/shtany"


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def parse_product(product):
    product_link = product.select_one(".product-item-link")
    if product_link:
        name = product_link.getText()
        price = product.select_one(".price").getText()
        link = product_link.get("href")
        sku = product.select_one("form").get("data-product-sku")
        return [sku, name, price, link]


async def parse_page(session, page_url):
    response = await fetch(session, page_url)
    page_doc = BeautifulSoup(response, features="html.parser")
    products = page_doc.select(".item.product.product-item")
    results = []
    for product in products:
        result = await parse_product(product)
        if result:
            results.append(result)
    return results


async def main():
    async with aiohttp.ClientSession() as session:
        response = await fetch(session, CATEGORY_URL)
        soup = BeautifulSoup(response, features="html.parser")
        items = soup.select(".items.pages-items")
        count = len(items[0].select("a.page"))

        filename = CATEGORY_URL.split("/")[-1]
        with open(filename + ".csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(["sku", "name", "price", "link"])

            tasks = []
            for i in range(count):
                page_url = CATEGORY_URL + "?p=" + str(i)
                task = asyncio.ensure_future(parse_page(session, page_url))
                tasks.append(task)

            pages_data = await asyncio.gather(*tasks)
            for page_data in pages_data:
                for product_data in page_data:
                    writer.writerow(product_data)

asyncio.run(main())
