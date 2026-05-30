from fastapi import FastAPI
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

import asyncio
import json

from app.backtest.statarb_backtest import (
    StatArbBacktester
)

from app.strategies.statistical_arbitrage import (
    StatisticalArbitrage
)

# ---------------------------------------------------
# GLOBAL ENGINE STATE
# ---------------------------------------------------

ENGINE_RUNNING = False

ENGINE_MODE = None

ENGINE_TASK = None

CONNECTED_CLIENTS = []

LIVE_METRICS = {
    "status": "IDLE",
    "strategy": "Statistical Arbitrage",
    "capital": 100000,
    "metrics": {}
}


def update_live_metrics(metrics):

    LIVE_METRICS.update({

        "status": "LIVE",

        "strategy": metrics.get(
            "strategy_name",
            LIVE_METRICS["strategy"]
        ),

        "capital": metrics.get(
            "final_capital",
            LIVE_METRICS["capital"]
        ),

        "metrics": metrics.get(
            "metrics",
            LIVE_METRICS["metrics"]
        )
    })

# ---------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------

app = FastAPI(
    title="US Statistical Arbitrage Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------

class StartLiveRequest(BaseModel):

    mode: str = "LIVE"


class BacktestRequest(BaseModel):

    start_date: str

    end_date: str


# ---------------------------------------------------
# HEALTH
# ---------------------------------------------------

@app.get("/api/health")
async def health():

    return {

        "status": "running",

        "engine_running": ENGINE_RUNNING,

        "engine_mode": ENGINE_MODE
    }


# ---------------------------------------------------
# START LIVE ENGINE
# ---------------------------------------------------

@app.post("/api/live/start")
async def start_live_engine():

    global ENGINE_RUNNING
    global ENGINE_MODE
    global ENGINE_TASK

    if ENGINE_RUNNING:

        return {

            "status": "error",

            "message": "Engine already running"
        }

    ENGINE_RUNNING = True

    ENGINE_MODE = "LIVE"

    strategy = StatisticalArbitrage(
        metrics_callback=update_live_metrics
    )

    ENGINE_TASK = asyncio.create_task(
        strategy.start()
    )

    LIVE_METRICS["status"] = "LIVE"

    return {

        "status": "success",

        "message": "Live Statistical Arbitrage Engine Started"
    }


# ---------------------------------------------------
# STOP LIVE ENGINE
# ---------------------------------------------------

@app.post("/api/live/stop")
async def stop_live_engine():

    global ENGINE_RUNNING
    global ENGINE_MODE
    global ENGINE_TASK

    if not ENGINE_RUNNING:

        return {

            "status": "info",

            "message": "Engine not running"
        }

    ENGINE_RUNNING = False

    ENGINE_MODE = None

    if ENGINE_TASK:

        ENGINE_TASK.cancel()

    LIVE_METRICS["status"] = "STOPPED"

    return {

        "status": "success",

        "message": "Engine Stopped"
    }


# ---------------------------------------------------
# BACKTEST
# ---------------------------------------------------

@app.post("/api/backtest/run")
async def run_backtest(
    request: BacktestRequest
):

    backtester = StatArbBacktester()

    report = backtester.run_portfolio(

        start=request.start_date,

        end=request.end_date
    )

    return {

        "status": "success",

        "report": report
    }


# ---------------------------------------------------
# PERFORMANCE REPORT
# ---------------------------------------------------

@app.get("/api/report")
async def report():

    return {

        "status": "success",

        "metrics": LIVE_METRICS
    }


# ---------------------------------------------------
# STREAM RESULTS
# ---------------------------------------------------

async def broadcast_loop():

    while True:

        if CONNECTED_CLIENTS:

            payload = json.dumps({

                "engine_running":
                    ENGINE_RUNNING,

                "engine_mode":
                    ENGINE_MODE,

                "metrics":
                    LIVE_METRICS
            })

            dead = []

            for ws in CONNECTED_CLIENTS:

                try:

                    await ws.send_text(
                        payload
                    )

                except Exception:

                    dead.append(ws)

            for ws in dead:

                CONNECTED_CLIENTS.remove(
                    ws
                )

        await asyncio.sleep(2)


# ---------------------------------------------------
# WEBSOCKET
# ---------------------------------------------------

@app.websocket("/ws/performance")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()

    CONNECTED_CLIENTS.append(
        websocket
    )

    print(
        "Client Connected"
    )

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        print(
            "Client Disconnected"
        )

    finally:

        if websocket in CONNECTED_CLIENTS:

            CONNECTED_CLIENTS.remove(
                websocket
            )


# ---------------------------------------------------
# STARTUP EVENT
# ---------------------------------------------------

@app.on_event("startup")
async def startup_event():

    asyncio.create_task(
        broadcast_loop()
    )