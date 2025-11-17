"""
Service layer for diagnosis operations
"""

from app.db.connection import get_db_connection
from typing import List, Tuple, Dict, Optional


def get_symptom_ids(symptom_names: List[str]) -> Tuple[List[int], List[str]]:
    """
    Convert symptom names to IDs
    
    Returns:
        Tuple of (symptom_ids, matched_symptom_names)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    symptom_ids = []
    matched_symptoms = []
    
    for symptom_name in symptom_names:
        symptom_clean = symptom_name.strip().lower()
        
        cursor.execute(
            "SELECT id, name FROM symptoms WHERE LOWER(name) = %s",
            (symptom_clean,)
        )
        result = cursor.fetchone()
        
        if result:
            symptom_ids.append(result[0])
            matched_symptoms.append(result[1])
    
    cursor.close()
    conn.close()
    
    return symptom_ids, matched_symptoms


def get_all_symptoms() -> List[Dict]:
    """
    Fetch all symptoms from database
    
    Returns:
        List of symptom dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, name, severity_weight 
        FROM symptoms 
        ORDER BY name
        """
    )
    
    symptoms = []
    for row in cursor.fetchall():
        symptoms.append({
            'id': row[0],
            'name': row[1],
            'severity_weight': row[2],
            'description': None
        })
    
    cursor.close()
    conn.close()
    
    return symptoms


def search_symptoms(query: str) -> List[Dict]:
    """
    Search symptoms by name
    
    Args:
        query: Search query string
        
    Returns:
        List of matching symptom dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    search_pattern = f"%{query.lower()}%"
    
    cursor.execute(
        """
        SELECT id, name, severity_weight 
        FROM symptoms 
        WHERE LOWER(name) LIKE %s
        ORDER BY name
        LIMIT 50
        """,
        (search_pattern,)
    )
    
    symptoms = []
    for row in cursor.fetchall():
        symptoms.append({
            'id': row[0],
            'name': row[1],
            'severity_weight': row[2],
            'description': None
        })
    
    cursor.close()
    conn.close()
    
    return symptoms


def get_all_diseases() -> List[Dict]:
    """
    Fetch all diseases from database with symptom counts
    
    Returns:
        List of disease dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT 
            d.id,
            d.name,
            d.description,
            COUNT(ds.symptom_id) as symptom_count
        FROM diseases d
        LEFT JOIN disease_symptoms ds ON d.id = ds.disease_id
        GROUP BY d.id, d.name, d.description
        ORDER BY d.name
        """
    )
    
    diseases = []
    for row in cursor.fetchall():
        diseases.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'symptom_count': row[3]
        })
    
    cursor.close()
    conn.close()
    
    return diseases


def get_disease_details(disease_id: int) -> Optional[Dict]:
    """
    Get detailed information about a specific disease
    
    Args:
        disease_id: The disease ID
        
    Returns:
        Disease details dictionary or None if not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get disease info
    cursor.execute(
        """
        SELECT id, name, description
        FROM diseases
        WHERE id = %s
        """,
        (disease_id,)
    )
    
    disease_row = cursor.fetchone()
    if not disease_row:
        cursor.close()
        conn.close()
        return None
    
    # Get associated symptoms
    cursor.execute(
        """
        SELECT s.id, s.name, s.severity_weight
        FROM symptoms s
        INNER JOIN disease_symptoms ds ON s.id = ds.symptom_id
        WHERE ds.disease_id = %s
        ORDER BY s.name
        """,
        (disease_id,)
    )
    
    symptoms = []
    for row in cursor.fetchall():
        symptoms.append({
            'id': row[0],
            'name': row[1],
            'severity_weight': row[2]
        })
    
    # Get recommendations
    recommendations = get_recommendations(disease_id)
    
    cursor.close()
    conn.close()
    
    return {
        'id': disease_row[0],
        'name': disease_row[1],
        'description': disease_row[2],
        'symptoms': symptoms,
        'recommendations': recommendations
    }


def get_recommendations(disease_id: int) -> List[str]:
    """
    Fetch recommendations for a specific disease
    
    Args:
        disease_id: The disease ID
        
    Returns:
        List of recommendation texts
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT recommendation_text 
        FROM recommendations 
        WHERE disease_id = %s 
        ORDER BY precaution_order
        """,
        (disease_id,)
    )
    
    recommendations = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return recommendations


def perform_diagnosis(symptom_ids: List[int]) -> List[Dict]:
    """
    Perform diagnosis using PostgreSQL stored procedure
    
    Args:
        symptom_ids: List of symptom IDs
        
    Returns:
        List of diagnosis results with recommendations
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Call the diagnose function
    cursor.execute(
        "SELECT * FROM diagnose(%s)",
        (symptom_ids,)
    )
    
    results = []
    for row in cursor.fetchall():
        disease_id = row[0]
        
        # Fetch recommendations for this disease
        recommendations = get_recommendations(disease_id)
        
        results.append({
            'disease_id': disease_id,
            'disease_name': row[1],
            'description': row[2],
            'match_count': row[3],
            'total_symptoms': row[4],
            'confidence_score': row[5],
            'recommendations': recommendations
        })
    
    cursor.close()
    conn.close()
    
    return results
