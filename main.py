from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Item
from slowapi import Limiter
from slowapi.util import get_remote_address

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/items")
@limiter.limit("10/minute")
def create_item(name: str, description: str, price: float = None, db: Session = Depends(get_db)):
    item = Item(name=name, description=description, price=price)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/item/{item_id}")
@limiter.limit("10/minute")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    return item


@app.get("/items")
@limiter.limit("10/minute")
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()