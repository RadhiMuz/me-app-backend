import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import schema, records, apps, spare_parts, stock_out
from routers import sheet_export as sheets_export
from routers import auth, update_report
from db.database import init_db

app = FastAPI(title="Factory Apps API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()
    os.makedirs("uploads/spare-parts", exist_ok=True)
    os.makedirs("uploads/reports", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(apps.router, prefix="/api/apps", tags=["apps"])
app.include_router(schema.router, prefix="/api/schema", tags=["schema"])
app.include_router(records.router, prefix="/api/apps/{app_id}/records", tags=["records"])
app.include_router(spare_parts.router, prefix="/api/spare-parts", tags=["spare-parts"])
app.include_router(stock_out.router, prefix="/api/stock-out", tags=["stock-out"])
app.include_router(sheets_export.router, prefix="/api/export", tags=["export"])
app.include_router(update_report.router, prefix="/api/reports", tags=["reports"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Factory Apps API running"}