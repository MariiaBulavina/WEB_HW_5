import asyncio
from datetime import datetime, timedelta
import logging
import sys

import aiohttp


URL = 'https://api.privatbank.ua/p24api/exchange_rates?date='


def get_dates(days):

    today = datetime.today().date()

    dates = []
    for d in range(days):
        date = today - timedelta(d)
        date_str = date.strftime('%d.%m.%Y')
        dates.append(date_str)

    return dates


def parse_data(data):

    ex_dct = {}

    for el in data["exchangeRate"]:

        if el['currency'] in ['EUR', 'USD']:

            ex_dct[el['currency']] = {
                'sale': el.get('saleRate'),
                'purchase': el.get('purchaseRate')}

    return ex_dct


async def main(days):

    result = []

    async with aiohttp.ClientSession() as session:
        
        dates = get_dates(days)    

        for date in dates:
            url = URL + date

            try:
           
                async with session.get(url) as response:
                    
                    if response.status == 200:
                        data = await response.json()    

                        date_dct = {date: parse_data(data)}

                        result.append(date_dct)

                    else:
                        logging.error(f"Error status {response.status} for {url}")

            except aiohttp.ClientConnectorError as e:
                logging.error(f"Connection error {url}: {e}")
                
    return result


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Enter the argument (days)')
    else:
        days = int(sys.argv[1])
        if days > 10:
            print('The number of days cannot be more than 10')
        else:
            result = asyncio.run(main(days))
            print(result)

