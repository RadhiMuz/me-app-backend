from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./appsheet.db"
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    from models.db_models import App, Record  # noqa
    from models.spare_parts import SparePart  # noqa
    from routers.stock_out import StockOut  # noqa
    from routers.auth import User, seed_admin  # noqa
    from routers.update_report import UpdateReport  # noqa
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_admin(session)

def get_session():
    with Session(engine) as session:
        yield session