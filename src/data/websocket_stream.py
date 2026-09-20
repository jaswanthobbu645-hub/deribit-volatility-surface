"""
Real-time Deribit options streaming via WebSocket.
Usage: python src/data/websocket_stream.py BTC 30
"""
import asyncio
import json
import websockets
import pandas as pd
from datetime import datetime
import os
import sys

STREAM_URL = "wss://www.deribit.com/ws/api/v2"
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw')


async def stream_options(asset='BTC', duration=30):
    async with websockets.connect(STREAM_URL) as ws:
        sub_msg = {
            "jsonrpc": "2.0", "id": 1,
            "method": "public/subscribe",
            "params": {"channels": [f"ticker.{asset}-*.100ms"]}
        }
        await ws.send(json.dumps(sub_msg))
        print(f"Subscribed to {asset} ticker stream for {duration}s")

        start = datetime.now()
        messages = []

        while (datetime.now() - start).total_seconds() < duration:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(msg)
                if 'params' in data and 'data' in data['params']:
                    messages.append(data['params']['data'])
                    if len(messages) % 100 == 0:
                        print(f"  Received {len(messages)} updates")
            except asyncio.TimeoutError:
                continue

        if messages:
            os.makedirs(DATA_DIR, exist_ok=True)
            df = pd.DataFrame(messages)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = os.path.join(DATA_DIR, f'{asset}_live_{ts}.csv')
            df.to_csv(out, index=False)
            print(f"Saved {len(df)} rows to {out}")
        return messages


if __name__ == '__main__':
    asset = sys.argv[1] if len(sys.argv) > 1 else 'BTC'
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    asyncio.run(stream_options(asset, duration))