import json
import uuid

import websockets

# Dir
from dashboard.models import Orders

#
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer



class TradeConsumer(AsyncWebsocketConsumer):
    fastapi_ws = None
    unrealised_order_data = None

    async def connect(self):
        await self.accept()
        print("Got the connection in websocket")

    async def disconnect(self, code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)

        if data.get('new_order', None):
            order = await self.create_order(data['new_order'])
            data['new_order']['order_id'] = order.order_id

            # Receiving data and sending back to the client
            async for d in self.connect_fastapi(data['new_order']):
                self.unrealised_order_data = json.loads(d)
                print(self.unrealised_order_data['equity'])
                await self.send(json.dumps(d))

        if data.get('close_order', None):
            await self.close_order()
            await self.disconnect_fastapi()


    '''Connects to fastapi websocket'''
    async def connect_fastapi(self, data):
        """
        Receives and distributes the live data
        :param data:
        :return:
        """
        url = "ws://localhost:8080/ws/trade_update"
        self.fastapi_ws = await websockets.connect(url, ping_interval=600)

        # Send back for testing
        for k, v in data.items():
            if isinstance(v, uuid.UUID):
                data[k] = str(v)
        await self.fastapi_ws.send(json.dumps(data))

        while True:
            try:
                new_data = await self.fastapi_ws.recv()
                yield json.loads(new_data)
            except Exception as e:
                print("FastAPI Error: ", type(e), str(e))


    '''Stops the stream from FastAPI'''
    async def disconnect_fastapi(self):
        await self.fastapi_ws.close()


    async def create_order(self, data):
        @sync_to_async
        def insert_order(data):
            order = Orders.objects.create(**{k: v for k, v in data.items() if v})
            return order

        return await insert_order(data)

    async def close_order(self):
        order = Orders.objects.get(order_id=self.unrealised_order_data['id'])
        order.realised_pnl = self.unrealised_order_data['unrealised_pnl']
        order.save()
