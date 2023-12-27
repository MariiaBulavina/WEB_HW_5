import asyncio
from datetime import datetime, timedelta
import logging

import aiohttp
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

URL = 'https://api.privatbank.ua/p24api/exchange_rates?date='

logging.basicConfig(level=logging.INFO)

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


async def main_ex(days):

    result = ''

    async with aiohttp.ClientSession() as session:
        
        dates = get_dates(days)    

        for date in dates:
            url = URL + date

            try:
           
                async with session.get(url) as response:
                    
                    if response.status == 200:
                        data = await response.json()    

                        date_dct = {date: parse_data(data)}

                        result += str(date_dct) + '\n'

                    else:
                        logging.error(f"Error status {response.status} for {url}")

            except aiohttp.ClientConnectorError as e:
                logging.error(f"Connection error {url}: {e}")
                
    return result


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def send_to_client(self, message: str, ws:WebSocketServerProtocol):
        await ws.send(message)

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.startswith('exchange'):

                day = int(message.split()[1])

                r = await main_ex(day)
                await self.send_to_client(r, ws)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())