"""
API endpoints for diseases
"""

from fastapi import APIRouter, HTTPException, Path
from app.schemas.diagnose import DiseasesResponse, DiseaseItem
from app.services.diagnose_service import get_all_diseases, get_disease_details

router = APIRouter(prefix="/diseases", tags=["Diseases"])


@router.get(
    "",
    response_model=DiseasesResponse,
    summary="Get all diseases",
    description="Returns a list of all diseases in the database with symptom counts"
)
async def list_diseases():
    """
    Get all diseases
    """
    try:
        diseases_data = get_all_diseases()
        
        # Convert to Pydantic models
        diseases = [
            DiseaseItem(
                id=d['id'],
                name=d['name'],
                description=d.get('description'),
                symptom_count=d['symptom_count']
            )
            for d in diseases_data
        ]
        
        return DiseasesResponse(
            status="success",
            total_count=len(diseases),
            diseases=diseases
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching diseases: {str(e)}"
        )


@router.get(
    "/{disease_id}",
    summary="Get disease details",
    description="Get detailed information about a specific disease including symptoms and recommendations"
)
async def get_disease(
    disease_id: int = Path(..., description="Disease ID", ge=1)
):
    """
    Get detailed information about a specific disease
    """
    try:
        disease_data = get_disease_details(disease_id)
        
        if not disease_data:
            raise HTTPException(
                status_code=404,
                detail=f"Disease with ID {disease_id} not found"
            )
        
        return {
            "status": "success",
            "disease": disease_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching disease details: {str(e)}"
        )