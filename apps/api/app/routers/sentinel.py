"""
Router de Sentinel — endpoints para el módulo de predicción ML.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.post("/ingest", summary="Recibe evento del POS")
async def ingest_pos_event(db: AsyncSession = Depends(get_db)):
    """
    Endpoint que el POS llama cada vez que se prepara un lote.
    Sentinel procesa el evento y calcula Pis.
    Si Pis >= umbral: crea misión automáticamente.
    """
    return {"status": "not implemented"}

@router.get("/predictions/{branch_id}", summary="Predicciones recientes de una sucursal")
async def get_predictions(branch_id: str, db: AsyncSession = Depends(get_db)):
    return {"status": "not implemented", "branch_id": branch_id}
