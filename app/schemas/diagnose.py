"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class DiagnoseRequest(BaseModel):
    """Request model for diagnosis endpoint"""
    symptom_names: List[str] = Field(
        ..., 
        description="List of symptom names",
        min_items=1,
        example=["fever", "headache", "cough"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "symptom_names": ["fever", "headache", "fatigue"]
            }
        }


class DiagnoseResult(BaseModel):
    """Single diagnosis result"""
    disease_id: int
    disease_name: str
    description: Optional[str] = None
    match_count: int = Field(description="Number of symptoms matched")
    total_symptoms: int = Field(description="Total symptoms for this disease")
    confidence_score: float = Field(description="Confidence percentage (0-100)")
    recommendations: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "disease_id": 1,
                "disease_name": "Common Cold",
                "description": "A viral infection of the upper respiratory tract",
                "match_count": 3,
                "total_symptoms": 5,
                "confidence_score": 60.0,
                "recommendations": [
                    "Get plenty of rest",
                    "Stay hydrated",
                    "Use over-the-counter pain relievers"
                ]
            }
        }


class DiagnoseResponse(BaseModel):
    """Response model for diagnosis endpoint"""
    status: str = "success"
    message: str
    input_symptoms: List[str]
    matched_symptoms: List[str]
    results: List[DiagnoseResult]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Diagnosis completed successfully",
                "input_symptoms": ["fever", "headache", "cough"],
                "matched_symptoms": ["fever", "headache", "cough"],
                "results": [
                    {
                        "disease_id": 1,
                        "disease_name": "Common Cold",
                        "description": "A viral infection",
                        "match_count": 3,
                        "total_symptoms": 5,
                        "confidence_score": 60.0,
                        "recommendations": ["Rest", "Hydrate"]
                    }
                ]
            }
        }


class SymptomItem(BaseModel):
    """Individual symptom"""
    id: int
    name: str
    description: Optional[str] = None
    severity_weight: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "fever",
                "description": "Elevated body temperature",
                "severity_weight": 7
            }
        }


class SymptomsResponse(BaseModel):
    """Response for symptoms list endpoint"""
    status: str = "success"
    total_count: int
    symptoms: List[SymptomItem]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "total_count": 132,
                "symptoms": [
                    {"id": 1, "name": "fever", "description": None, "severity_weight": 7}
                ]
            }
        }


class DiseaseItem(BaseModel):
    """Individual disease"""
    id: int
    name: str
    description: Optional[str] = None
    symptom_count: int = Field(description="Number of symptoms associated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Common Cold",
                "description": "A viral infection of the upper respiratory tract",
                "symptom_count": 5
            }
        }


class DiseasesResponse(BaseModel):
    """Response for diseases list endpoint"""
    status: str = "success"
    total_count: int
    diseases: List[DiseaseItem]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "total_count": 41,
                "diseases": [
                    {
                        "id": 1,
                        "name": "Common Cold",
                        "description": "A viral infection",
                        "symptom_count": 5
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = "error"
    message: str
    details: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "No symptoms matched",
                "details": "Please check symptom names"
            }
        }