"""
Servicio real: storage_service
Implementación de subida de evidencias usando la API REST de Supabase Storage mediante httpx.
"""
import uuid
import httpx
import re
from app.config import get_settings

async def upload_evidence_image(
    file_content: bytes, 
    shop_id: uuid.UUID, 
    ticket_id: uuid.UUID, 
    timestamp: str, 
    filename: str, 
    mime_type: str
) -> str:
    """
    Sube un archivo al bucket ticket-evidences en Supabase usando la API REST.
    Retorna la URL pública del archivo.
    """
    settings = get_settings()
    bucket = "ticket-evidences"
    
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    path = f"{shop_id}/{ticket_id}/{timestamp}_{filename}"
    url = f"{settings.supabase_url}/storage/v1/object/{bucket}/{path}"
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            url,
            content=file_content,
            headers={
                "Authorization": f"Bearer {settings.supabase_key}",
                "Content-Type": mime_type,
            }
        )
        response.raise_for_status()
    
    return f"{settings.supabase_url}/storage/v1/object/public/{bucket}/{path}"
