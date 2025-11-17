"""
API endpoints for diagnosis
"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.diagnose import (
    DiagnoseRequest, 
    DiagnoseResponse, 
    DiagnoseResult,
    ErrorResponse
)
from app.services.diagnose_service import get_symptom_ids, perform_diagnosis

router = APIRouter(prefix="/diagnose", tags=["Diagnosis"])


@router.post(
    "",
    response_model=DiagnoseResponse,
    summary="Diagnose possible diseases based on symptoms",
    description="Provide a list of symptom names and get back possible diseases with confidence scores"
)
async def diagnose_symptoms(request: DiagnoseRequest):
    """
    Main diagnosis endpoint
    
    Takes a list of symptom names and returns possible diseases
    """
    try:
        # Step 1: Convert symptom names to IDs
        symptom_ids, matched_symptoms = get_symptom_ids(request.symptom_names)
        
        # Check if any symptoms were matched
        if not symptom_ids:
            return DiagnoseResponse(
                status="warning",
                message="No symptoms matched in database",
                input_symptoms=request.symptom_names,
                matched_symptoms=[],
                results=[]
            )
        
        # Step 2: Perform diagnosis using stored procedure
        diagnosis_results = perform_diagnosis(symptom_ids)
        
        # Step 3: Format results
        if not diagnosis_results:
            return DiagnoseResponse(
                status="warning",
                message="No diseases found matching these symptoms",
                input_symptoms=request.symptom_names,
                matched_symptoms=matched_symptoms,
                results=[]
            )
        
        # Convert results to Pydantic models
        formatted_results = []
        for result in diagnosis_results:
            formatted_results.append(
                DiagnoseResult(
                    disease_id=result['disease_id'],
                    disease_name=result['disease_name'],
                    description=result['description'],
                    match_count=result['match_count'],
                    total_symptoms=result['total_symptoms'],
                    confidence_score=float(result['confidence_score']),
                    recommendations=result['recommendations'] or []
                )
            )
        
        return DiagnoseResponse(
            status="success",
            message=f"Found {len(formatted_results)} possible disease(s)",
            input_symptoms=request.symptom_names,
            matched_symptoms=matched_symptoms,
            results=formatted_results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error performing diagnosis: {str(e)}"
        )