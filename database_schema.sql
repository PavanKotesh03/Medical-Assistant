-- ============================================
-- Medical Symptom Assistant Database Schema
-- ============================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS recommendations CASCADE;
DROP TABLE IF EXISTS disease_symptoms CASCADE;
DROP TABLE IF EXISTS symptoms CASCADE;
DROP TABLE IF EXISTS diseases CASCADE;

-- ============================================
-- TABLE 1: symptoms
-- ============================================
CREATE TABLE symptoms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    severity_weight INTEGER DEFAULT 1
);

-- ============================================
-- TABLE 2: diseases
-- ============================================
CREATE TABLE diseases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT
);

-- ============================================
-- TABLE 3: disease_symptoms (relationship table)
-- ============================================
CREATE TABLE disease_symptoms (
    id SERIAL PRIMARY KEY,
    disease_id INTEGER NOT NULL,
    symptom_id INTEGER NOT NULL,
    weight NUMERIC DEFAULT 1.0,
    FOREIGN KEY (disease_id) REFERENCES diseases(id) ON DELETE CASCADE,
    FOREIGN KEY (symptom_id) REFERENCES symptoms(id) ON DELETE CASCADE,
    UNIQUE(disease_id, symptom_id)
);

-- ============================================
-- TABLE 4: recommendations
-- ============================================
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    disease_id INTEGER NOT NULL,
    recommendation_text TEXT NOT NULL,
    precaution_order INTEGER DEFAULT 1,
    FOREIGN KEY (disease_id) REFERENCES diseases(id) ON DELETE CASCADE
);

-- ============================================
-- INDEXES for better performance
-- ============================================
CREATE INDEX idx_disease_symptoms_disease ON disease_symptoms(disease_id);
CREATE INDEX idx_disease_symptoms_symptom ON disease_symptoms(symptom_id);
CREATE INDEX idx_recommendations_disease ON recommendations(disease_id);
CREATE INDEX idx_symptoms_name ON symptoms(name);

-- ============================================
-- STORED FUNCTION 1: Compute Disease Score
-- ============================================
CREATE OR REPLACE FUNCTION compute_disease_score(user_symptom_ids INT[])
RETURNS TABLE (
    disease_id INT,
    disease_name TEXT,
    match_count BIGINT,
    total_symptoms BIGINT,
    score NUMERIC
)
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id AS disease_id,
        d.name AS disease_name,
        COUNT(ds.symptom_id) AS match_count,
        (SELECT COUNT(*) FROM disease_symptoms WHERE disease_id = d.id) AS total_symptoms,
        ROUND(
            (COUNT(ds.symptom_id)::NUMERIC / 
             NULLIF((SELECT COUNT(*) FROM disease_symptoms WHERE disease_id = d.id), 0)) * 100, 
            2
        ) AS score
    FROM diseases d
    JOIN disease_symptoms ds ON ds.disease_id = d.id
    WHERE ds.symptom_id = ANY(user_symptom_ids)
    GROUP BY d.id, d.name
    HAVING COUNT(ds.symptom_id) > 0
    ORDER BY score DESC, match_count DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STORED FUNCTION 2: Get Recommendations
-- ============================================
CREATE OR REPLACE FUNCTION get_recommendations_for_disease(d_id INT)
RETURNS TABLE (
    recommendation_text TEXT,
    precaution_order INT
)
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.recommendation_text,
        r.precaution_order
    FROM recommendations r
    WHERE r.disease_id = d_id
    ORDER BY r.precaution_order;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STORED FUNCTION 3: Main Diagnosis Function
-- ============================================
CREATE OR REPLACE FUNCTION diagnose(user_symptom_ids INT[])
RETURNS TABLE (
    disease_id INT,
    disease_name TEXT,
    description TEXT,
    match_count BIGINT,
    total_symptoms BIGINT,
    confidence_score NUMERIC,
    recommendations TEXT[]
)
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.disease_id,
        s.disease_name,
        d.description,
        s.match_count,
        s.total_symptoms,
        s.score AS confidence_score,
        ARRAY(
            SELECT recommendation_text 
            FROM get_recommendations_for_disease(s.disease_id)
        ) AS recommendations
    FROM compute_disease_score(user_symptom_ids) s
    JOIN diseases d ON d.id = s.disease_id
    ORDER BY s.score DESC;
END;
$$ LANGUAGE plpgsql;