import asyncio
import json
import time
from typing import Callable, Optional, Dict, Any
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException


class PolymarketWebSocketClient:
    def __init__(self, ws_url: str = "wss://ws-subscriptions.polymarket.com"):
        self.ws_url = ws_url
        self.websocket = None
        self.running = False
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
        self.message_handlers: Dict[str, Callable] = {}
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.running = True
            self.reconnect_delay = 1
            print(f"WebSocket connected to {self.ws_url}")
            return True
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            return False
    
    async def disconnect(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            print("WebSocket disconnected")
    
    async def _reconnect(self):
        print(f"Reconnecting in {self.reconnect_delay} seconds...")
        await asyncio.sleep(self.reconnect_delay)
        
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        
        if await self.connect():
            for channel, params in self.subscriptions.items():
                await self._send_subscription(channel, params)
    
    async def _send_subscription(self, channel: str, params: Dict[str, Any]):
        if not self.websocket:
            return
        
        message = {
            "type": "subscribe",
            "channel": channel,
            **params
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"Subscribed to channel: {channel}")
        except Exception as e:
            print(f"Error sending subscription: {e}")
    
    async def subscribe_user_trades(self, wallet_address: str, 
                                   callback: Callable[[Dict[str, Any]], None]):
        channel = "user"
        params = {"wallet": wallet_address}
        
        self.subscriptions[f"{channel}_{wallet_address}"] = params
        self.message_handlers[f"{channel}_{wallet_address}"] = callback
        
        await self._send_subscription(channel, params)
    
    async def subscribe_market(self, market_id: str, 
                              callback: Callable[[Dict[str, Any]], None]):
        channel = "market"
        params = {"market": market_id}
        
        self.subscriptions[f"{channel}_{market_id}"] = params
        self.message_handlers[f"{channel}_{market_id}"] = callback
        
        await self._send_subscription(channel, params)
    
    async def subscribe_ticker(self, token_id: str,
                              callback: Callable[[Dict[str, Any]], None]):
        channel = "ticker"
        params = {"token_id": token_id}
        
        self.subscriptions[f"{channel}_{token_id}"] = params
        self.message_handlers[f"{channel}_{token_id}"] = callback
        
        await self._send_subscription(channel, params)
    
    async def _handle_message(self, message: str):
        try:
            data = json.loads(message)
            
            msg_type = data.get('type', '')
            channel = data.get('channel', '')
            
            if msg_type == 'trade' or msg_type == 'user_trade':
                wallet = data.get('wallet', '')
                handler_key = f"user_{wallet}"
                if handler_key in self.message_handlers:
                    self.message_handlers[handler_key](data)
            
            elif msg_type == 'market_update':
                market_id = data.get('market', '')
                handler_key = f"market_{market_id}"
                if handler_key in self.message_handlers:
                    self.message_handlers[handler_key](data)
            
            elif msg_type == 'ticker':
                token_id = data.get('token_id', '')
                handler_key = f"ticker_{token_id}"
                if handler_key in self.message_handlers:
                    self.message_handlers[handler_key](data)
            
            elif msg_type == 'pong':
                pass
            
            elif msg_type == 'error':
                print(f"WebSocket error: {data.get('message', 'Unknown error')}")
        
        except json.JSONDecodeError as e:
            print(f"Error decoding WebSocket message: {e}")
        except Exception as e:
            print(f"Error handling WebSocket message: {e}")
    
    async def _send_heartbeat(self):
        while self.running:
            try:
                if self.websocket:
                    await self.websocket.send(json.dumps({"type": "ping"}))
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error sending heartbeat: {e}")
                break
    
    async def listen(self):
        heartbeat_task = asyncio.create_task(self._send_heartbeat())
        
        while True:
            try:
                if not self.websocket:
                    if not await self.connect():
                        await self._reconnect()
                        continue
                
                async for message in self.websocket:
                    await self._handle_message(message)
            
            except ConnectionClosed:
                print("WebSocket connection closed")
                if self.running:
                    await self._reconnect()
                else:
                    break
            
            except WebSocketException as e:
                print(f"WebSocket exception: {e}")
                if self.running:
                    await self._reconnect()
                else:
                    break
            
            except Exception as e:
                print(f"Unexpected error in WebSocket listener: {e}")
                if self.running:
                    await self._reconnect()
                else:
                    break
        
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
    
    async def start(self):
        await self.listen()
    
    async def stop(self):
        await self.disconnect()
