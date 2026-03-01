"""Router de branches — skeleton, pendiente de implementación."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/", summary="Listar branches")
async def list_items(db: AsyncSession = Depends(get_db)):
    return {"status": "not implemented", "resource": "branches"}

@router.post("/", summary="Crear branches")
async def create_item(db: AsyncSession = Depends(get_db)):
    return {"status": "not implemented", "resource": "branches"}
