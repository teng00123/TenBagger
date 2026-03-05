# main.py
from fastapi import FastAPI
from api.Trade.routers import router as trade_router
from utils.db import init_db
from api.core.i18n_scanner import main as i18n_scanner

app = FastAPI()
app.include_router(trade_router)
init_db()
i18n_scanner()
@app.get("/")
async def root():
    return {"message": "TenBagger Trading API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)