"""
Initialize database schema for Medical Symptom Assistant
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_db_connection

def create_schema():
    """Create all database tables"""
    print("🔧 Creating database schema...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create symptoms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symptoms (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            severity_weight INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created symptoms table")
    
    # Create diseases table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diseases (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created diseases table")
    
    # Create disease_symptoms join table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disease_symptoms (
            id SERIAL PRIMARY KEY,
            disease_id INTEGER NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
            symptom_id INTEGER NOT NULL REFERENCES symptoms(id) ON DELETE CASCADE,
            weight DECIMAL(3, 2) DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(disease_id, symptom_id)
        )
    """)
    print("✓ Created disease_symptoms table")
    
    # Create recommendations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id SERIAL PRIMARY KEY,
            disease_id INTEGER NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
            recommendation_text TEXT NOT NULL,
            precaution_order INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created recommendations table")
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_disease_symptoms_disease ON disease_symptoms(disease_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_disease_symptoms_symptom ON disease_symptoms(symptom_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_disease ON recommendations(disease_id)")
    print("✓ Created indexes")
    
def create_functions():
    """Create PostgreSQL functions for diagnosis"""
    print("\n🔧 Creating database functions...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop the old function first
    try:
        cursor.execute("DROP FUNCTION IF EXISTS diagnose(INTEGER[]);")
        print("✓ Dropped old diagnose() function")
    except Exception as e:
        print(f"⚠️  Warning dropping function: {e}")
    
    # Create the new function
    diagnose_function = """
        CREATE FUNCTION diagnose(symptom_ids INTEGER[])
        RETURNS TABLE (
            disease_id INTEGER,
            disease_name VARCHAR,
            description TEXT,
            match_count BIGINT,
            total_symptoms BIGINT,
            confidence_score INTEGER
        ) 
        LANGUAGE plpgsql
        AS $func$
        BEGIN
            RETURN QUERY
            SELECT 
                d.id,
                d.name,
                d.description,
                COUNT(DISTINCT ds.symptom_id),
                (SELECT COUNT(*) FROM disease_symptoms ds2 WHERE ds2.disease_id = d.id),
                CAST(
                    (COUNT(DISTINCT ds.symptom_id)::FLOAT / 
                    NULLIF((SELECT COUNT(*) FROM disease_symptoms ds3 WHERE ds3.disease_id = d.id), 0)) * 100 
                    AS INTEGER
                )
            FROM diseases d
            INNER JOIN disease_symptoms ds ON d.id = ds.disease_id
            WHERE ds.symptom_id = ANY(symptom_ids)
            GROUP BY d.id, d.name, d.description
            HAVING COUNT(DISTINCT ds.symptom_id) > 0
            ORDER BY 6 DESC, 4 DESC
            LIMIT 10;
        END;
        $func$;
    """
    
    try:
        cursor.execute(diagnose_function)
        print("✓ Created new diagnose() function")
    except Exception as e:
        print(f"❌ Error creating diagnose function: {e}")
        raise
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Database functions created successfully!")

