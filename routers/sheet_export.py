from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db.database import get_session
from models.spare_parts import SparePart
from routers.stock_out import StockOut
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

router = APIRouter()

SHEET_ID = "1FQwLZynh9_3ps6pTvCo__i795dB5SwlFMcfxSYt9U7I"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

CREDENTIALS = {}


def get_sheets_service():
    raise HTTPException(
        status_code=503,
        detail="Google Sheets integration is temporarily disabled."
    )


def ensure_sheet(service, sheet_name: str):
    """Create sheet tab if it doesn't exist, then clear it."""
    spreadsheet = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    existing = [s["properties"]["title"] for s in spreadsheet["sheets"]]

    if sheet_name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
        ).execute()
    else:
        # Clear existing content
        service.spreadsheets().values().clear(
            spreadsheetId=SHEET_ID, range=f"{sheet_name}!A:Z"
        ).execute()


def write_rows(service, sheet_name: str, rows: list):
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()


@router.post("/inventory")
def export_inventory(session: Session = Depends(get_session)):
    parts = session.exec(select(SparePart)).all()
    if not parts:
        raise HTTPException(status_code=400, detail="No inventory data to export")

    try:
        service = get_sheets_service()
        sheet_name = "Inventory"
        ensure_sheet(service, sheet_name)

        headers = ["ID", "Product Name", "Product ID", "Category", "Available Stock", "Minimum Stock", "Rack", "Status", "Last Updated"]
        rows = [headers]
        for p in parts:
            status = "Critical" if p.available_stock == 0 else "Low" if p.available_stock <= p.minimum_stock else "OK"
            rows.append([
                p.id, p.product_name, p.product_id, p.category,
                p.available_stock, p.minimum_stock, p.rack, status,
                p.updated_at.strftime("%Y-%m-%d %H:%M"),
            ])

        write_rows(service, sheet_name, rows)
        return {"message": f"Exported {len(parts)} parts to Google Sheets", "sheet": sheet_name, "count": len(parts)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/stock-out")
def export_stock_out(session: Session = Depends(get_session)):
    records = session.exec(select(StockOut)).all()
    if not records:
        raise HTTPException(status_code=400, detail="No stock out records to export")

    try:
        service = get_sheets_service()
        sheet_name = "Stock Out"
        ensure_sheet(service, sheet_name)

        headers = ["ID", "Timestamp", "Product Name", "Product ID", "Quantity", "Usage / Purpose", "User"]
        rows = [headers]
        for r in sorted(records, key=lambda x: x.timestamp, reverse=True):
            rows.append([
                r.id,
                r.timestamp.strftime("%Y-%m-%d %H:%M"),
                r.product_name, r.product_id,
                r.quantity, r.usage, r.user,
            ])

        write_rows(service, sheet_name, rows)
        return {"message": f"Exported {len(records)} records to Google Sheets", "sheet": sheet_name, "count": len(records)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


def read_sheet(service, sheet_name: str):
    """Read all rows from a sheet tab, returns list of dicts using header row as keys."""
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"{sheet_name}!A:Z"
    ).execute()
    rows = result.get("values", [])
    if len(rows) < 2:
        return []
    headers = rows[0]
    return [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in rows[1:]]


def _parse_int(val, default=0):
    """Safely parse a value that might be empty, float string, or int string."""
    try:
        return int(float(str(val).strip())) if str(val).strip() else default
    except (ValueError, TypeError):
        return default


@router.get("/debug/inventory")
def debug_inventory(session: Session = Depends(get_session)):
    """See exactly what the sheet returns before importing."""
    try:
        service = get_sheets_service()
        rows = read_sheet(service, "Inventory")
        return {"row_count": len(rows), "first_5_rows": rows[:5]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/inventory")
def import_inventory(session: Session = Depends(get_session)):
    try:
        service = get_sheets_service()
        rows = read_sheet(service, "Inventory")
        if not rows:
            raise HTTPException(status_code=400, detail="No data found in Inventory sheet")

        updated = 0
        created = 0

        for row in rows:
            try:
                sheet_id = _parse_int(row.get("ID", 0))
                product_name = row.get("Product Name", "").strip()
                product_id_str = row.get("Product ID", "").strip()
                if not product_name or not product_id_str:
                    continue

                available = _parse_int(row.get("Available Stocks", row.get("Available Stock", 0)))
                minimum = _parse_int(row.get("Minimum Stock", 1), default=1)
                category = row.get("Category", "").strip()
                rack = row.get("Rack", "").strip()

                # Match by DB id first, then fall back to product_id string
                part = session.get(SparePart, sheet_id) if sheet_id else None
                if not part:
                    part = session.exec(select(SparePart).where(SparePart.product_id == product_id_str)).first()

                if part:
                    part.product_name = product_name
                    part.product_id = product_id_str
                    part.available_stock = available
                    part.minimum_stock = minimum
                    part.category = category
                    part.rack = rack
                    part.updated_at = datetime.utcnow()
                    session.add(part)
                    updated += 1
                else:
                    new_part = SparePart(
                        product_name=product_name,
                        product_id=product_id_str,
                        available_stock=available,
                        minimum_stock=minimum,
                        category=category,
                        rack=rack,
                    )
                    session.add(new_part)
                    created += 1
            except Exception:
                continue

        session.commit()
        return {"message": f"Inventory synced — {updated} updated, {created} created", "updated": updated, "created": created}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/import/stock-out")
def import_stock_out(session: Session = Depends(get_session)):
    try:
        service = get_sheets_service()
        rows = read_sheet(service, "Stock Out")
        if not rows:
            raise HTTPException(status_code=400, detail="No data found in Stock Out sheet")

        existing_ids = set(r.id for r in session.exec(select(StockOut)).all())
        created = 0

        for row in rows:
            try:
                sheet_id = int(row.get("ID", 0))
                if sheet_id in existing_ids:
                    continue  # skip already imported records

                part_name = row.get("Product Name", "").strip()
                part_pid = row.get("Product ID", "").strip()
                quantity = int(row.get("Quantity", 0))
                usage = row.get("Usage / Purpose", "").strip()
                user = row.get("User", "").strip()
                timestamp_str = row.get("Timestamp", "")

                if not part_name or quantity <= 0:
                    continue

                # Find part in db
                part = session.exec(select(SparePart).where(SparePart.product_id == part_pid)).first()
                if not part:
                    continue

                try:
                    ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    ts = datetime.utcnow()

                record = StockOut(
                    part_id=part.id,
                    product_name=part_name,
                    product_id=part_pid,
                    quantity=quantity,
                    usage=usage,
                    user=user,
                    timestamp=ts,
                )
                session.add(record)
                created += 1
            except (ValueError, TypeError):
                continue

        session.commit()
        return {"message": f"Stock Out synced — {created} new records imported", "created": created}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.post("/sync")
def full_sync(session: Session = Depends(get_session)):
    """Push current DB state to Sheets — inventory + stock out."""
    try:
        service = get_sheets_service()

        # Export inventory
        parts = session.exec(select(SparePart)).all()
        if parts:
            ensure_sheet(service, "Inventory")
            headers = ["ID", "Product Name", "Product ID", "Category", "Available Stock", "Minimum Stock", "Rack", "Status", "Last Updated"]
            rows = [headers]
            for p in parts:
                status = "Critical" if p.available_stock == 0 else "Low" if p.available_stock <= p.minimum_stock else "OK"
                rows.append([p.id, p.product_name, p.product_id, p.category, p.available_stock, p.minimum_stock, p.rack, status, p.updated_at.strftime("%Y-%m-%d %H:%M")])
            write_rows(service, "Inventory", rows)

        # Export stock out
        stock_records = session.exec(select(StockOut)).all()
        if stock_records:
            ensure_sheet(service, "Stock Out")
            headers = ["ID", "Timestamp", "Product Name", "Product ID", "Quantity", "Usage / Purpose", "User"]
            rows = [headers]
            for r in sorted(stock_records, key=lambda x: x.timestamp, reverse=True):
                rows.append([r.id, r.timestamp.strftime("%Y-%m-%d %H:%M"), r.product_name, r.product_id, r.quantity, r.usage, r.user])
            write_rows(service, "Stock Out", rows)

        return {
            "message": f"Synced {len(parts)} inventory items and {len(stock_records)} stock out records to Google Sheets",
            "inventory_count": len(parts),
            "stock_out_count": len(stock_records),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")