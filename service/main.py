import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from service.routers import kitas

app = FastAPI(title="Tobey GIS - Kita Bedarfsplanung § 80 SGB VIII")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print("CRASH TRACEBACK:\n", tb)
    return PlainTextResponse(tb, status_code=500)

app.include_router(kitas.router)