"""Router de fiscal — skeleton, pendiente de implementación."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/", summary="Listar fiscal")
async def list_items(db: AsyncSession = Depends(get_db)):
    return {"status": "not implemented", "resource": "fiscal"}

@router.post("/", summary="Crear fiscal")
async def create_item(db: AsyncSession = Depends(get_db)):
    return {"status": "not implemented", "resource": "fiscal"}
