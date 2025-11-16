"""
Script to load Kaggle dataset into PostgreSQL database
Modified to work with: Disease precaution.csv and DiseaseAndSymptoms.csv
"""

import pandas as pd
import sys
import os

# Add parent directory to path to import from app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.connection import get_db_connection


def extract_symptoms_from_disease_file():
    """Extract unique symptoms from DiseaseAndSymptoms.csv"""
    print("\n📊 Extracting symptoms from DiseaseAndSymptoms.csv...")
    
    df = pd.read_csv('data/DiseaseAndSymptoms.csv')
    
    # Get all symptom columns (assuming columns with symptoms)
    symptom_columns = [col for col in df.columns if col not in ['Disease', 'disease']]
    
    # Extract all unique symptoms
    all_symptoms = set()
    for col in symptom_columns:
        symptoms = df[col].dropna().unique()
        for symptom in symptoms:
            if symptom and str(symptom).strip():
                symptom_clean = str(symptom).strip().lower().replace('_', ' ')
                all_symptoms.add(symptom_clean)
    
    print(f"✓ Found {len(all_symptoms)} unique symptoms")
    return list(all_symptoms)


def load_symptoms():
    """Load symptoms from DiseaseAndSymptoms.csv"""
    print("\n📊 Loading symptoms into database...")
    
    symptoms = extract_symptoms_from_disease_file()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    inserted = 0
    for symptom_name in symptoms:
        try:
            # Default severity weight to 5 (medium) since we don't have severity data
            cursor.execute(
                """
                INSERT INTO symptoms (name, severity_weight)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
                """,
                (symptom_name, 5)
            )
            inserted += cursor.rowcount
        except Exception as e:
            print(f"Error inserting symptom {symptom_name}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✓ Inserted {inserted} symptoms")


def load_diseases_and_relationships():
    """Load diseases and their symptom relationships from DiseaseAndSymptoms.csv"""
    print("\n📊 Loading diseases and symptom relationships...")
    
    df = pd.read_csv('data/DiseaseAndSymptoms.csv')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all symptoms for ID mapping
    cursor.execute("SELECT id, name FROM symptoms")
    symptom_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    diseases_inserted = 0
    relationships_inserted = 0
    
    # Find the disease column name (could be 'Disease' or 'disease')
    disease_col = 'Disease' if 'Disease' in df.columns else 'disease'
    
    for _, row in df.iterrows():
        disease_name = str(row[disease_col]).strip()
        
        # Skip if empty
        if not disease_name or disease_name == 'nan':
            continue
        
        # Insert disease
        try:
            cursor.execute(
                """
                INSERT INTO diseases (name)
                VALUES (%s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
                """,
                (disease_name,)
            )
            disease_id = cursor.fetchone()[0]
            diseases_inserted += 1
        except Exception as e:
            print(f"Error inserting disease {disease_name}: {e}")
            continue
        
        # Insert symptom relationships
        # Get all columns except the disease column
        symptom_columns = [col for col in df.columns if col != disease_col]
        
        for col in symptom_columns:
            symptom_value = row[col]
            
            if pd.notna(symptom_value) and str(symptom_value).strip():
                symptom_name = str(symptom_value).strip().lower().replace('_', ' ')
                
                if symptom_name in symptom_map:
                    symptom_id = symptom_map[symptom_name]
                    
                    try:
                        cursor.execute(
                            """
                            INSERT INTO disease_symptoms (disease_id, symptom_id, weight)
                            VALUES (%s, %s, 1.0)
                            ON CONFLICT (disease_id, symptom_id) DO NOTHING
                            """,
                            (disease_id, symptom_id)
                        )
                        relationships_inserted += cursor.rowcount
                    except Exception as e:
                        print(f"Error linking {disease_name} - {symptom_name}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✓ Inserted {diseases_inserted} diseases")
    print(f"✓ Created {relationships_inserted} disease-symptom relationships")


def load_precautions():
    """Load precautions/recommendations from Disease precaution.csv"""
    print("\n📊 Loading precautions...")
    
    df = pd.read_csv('data/Disease precaution.csv')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get disease IDs
    cursor.execute("SELECT id, name FROM diseases")
    disease_map = {row[1].lower(): row[0] for row in cursor.fetchall()}
    
    inserted = 0
    
    # Find the disease column name
    disease_col = None
    for col in df.columns:
        if 'disease' in col.lower():
            disease_col = col
            break
    
    if not disease_col:
        print("❌ Could not find disease column in Disease precaution.csv")
        return
    
    # Find precaution columns
    precaution_cols = [col for col in df.columns if 'precaution' in col.lower()]
    
    for _, row in df.iterrows():
        disease_name = str(row[disease_col]).strip().lower()
        
        if not disease_name or disease_name == 'nan':
            continue
        
        # Try to find disease ID (case-insensitive match)
        disease_id = disease_map.get(disease_name)
        
        if not disease_id:
            # Try without extra spaces or characters
            disease_name_clean = ' '.join(disease_name.split())
            disease_id = disease_map.get(disease_name_clean)
        
        if not disease_id:
            print(f"⚠️  Disease not found: {disease_name}")
            continue
        
        # Insert each precaution
        for idx, col in enumerate(precaution_cols, 1):
            precaution = row[col]
            
            if pd.notna(precaution) and str(precaution).strip() and str(precaution) != 'nan':
                try:
                    cursor.execute(
                        """
                        INSERT INTO recommendations (disease_id, recommendation_text, precaution_order)
                        VALUES (%s, %s, %s)
                        """,
                        (disease_id, str(precaution).strip(), idx)
                    )
                    inserted += cursor.rowcount
                except Exception as e:
                    print(f"Error inserting precaution for {disease_name}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✓ Inserted {inserted} precautions/recommendations")


def verify_data():
    """Verify that data was loaded correctly"""
    print("\n🔍 Verifying data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM symptoms")
    symptom_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM diseases")
    disease_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM disease_symptoms")
    relationship_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM recommendations")
    recommendation_count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    print(f"\n📈 Database Statistics:")
    print(f"  • Symptoms: {symptom_count}")
    print(f"  • Diseases: {disease_count}")
    print(f"  • Disease-Symptom relationships: {relationship_count}")
    print(f"  • Recommendations: {recommendation_count}")
    
    if symptom_count > 0 and disease_count > 0:
        print("\n✅ Data loaded successfully!")
    else:
        print("\n❌ Data loading may have failed. Check errors above.")


def main():
    """Main execution function"""
    print("=" * 60)
    print("🏥 Medical Symptom Assistant - Data Loader")
    print("=" * 60)
    print("\nExpected files in 'data/' directory:")
    print("  1. DiseaseAndSymptoms.csv")
    print("  2. Disease precaution.csv")
    print()
    
    try:
        # Load data in order
        load_symptoms()
        load_diseases_and_relationships()
        load_precautions()
        verify_data()
        
        print("\n" + "=" * 60)
        print("✅ All data loaded successfully!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        print("\nMake sure the following files exist in the 'data/' directory:")
        print("  • DiseaseAndSymptoms.csv")
        print("  • Disease precaution.csv")
    except Exception as e:
        print(f"\n❌ Error during data loading: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()