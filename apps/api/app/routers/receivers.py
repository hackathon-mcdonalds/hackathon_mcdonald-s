"""Router de receivers — skeleton, pendiente de implementación."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/", summary="Listar receivers")
async def list_items(db: AsyncSession = Depends(get_db)):
    return {"status": "not implemented", "resource": "receivers"}

@router.post("/", summary="Crear receivers")
async def create_item(db: AsyncSession = Depends(get_db)):
    return {"status": "not implemented", "resource": "receivers"}
