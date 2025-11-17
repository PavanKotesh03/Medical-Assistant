"""
API endpoints for symptoms
"""

from fastapi import APIRouter, HTTPException, Query
from app.schemas.diagnose import SymptomsResponse, SymptomItem
from app.services.diagnose_service import get_all_symptoms, search_symptoms

router = APIRouter(prefix="/symptoms", tags=["Symptoms"])


@router.get(
    "",
    response_model=SymptomsResponse,
    summary="Get all available symptoms",
    description="Returns a list of all symptoms in the database"
)
async def list_symptoms(
    search: str = Query(None, description="Search symptoms by name")
):
    """
    Get all symptoms or search by name
    """
    try:
        if search:
            # Search symptoms
            symptoms_data = search_symptoms(search)
        else:
            # Get all symptoms
            symptoms_data = get_all_symptoms()
        
        # Convert to Pydantic models
        symptoms = [
            SymptomItem(
                id=s['id'],
                name=s['name'],
                description=s.get('description'),
                severity_weight=s['severity_weight']
            )
            for s in symptoms_data
        ]
        
        return SymptomsResponse(
            status="success",
            total_count=len(symptoms),
            symptoms=symptoms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching symptoms: {str(e)}"
        )