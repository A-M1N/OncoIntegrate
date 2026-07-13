"""
OncoIntegrate API Documentation

BASE URL: http://localhost:8000/api

PATIENT ENDPOINTS
================

1. List Patients (Paginated)
   GET /patients/?page=1&page_size=25
   
   Response:
   {
     "count": 50,
     "total_pages": 2,
     "page": 1,
     "page_size": 25,
     "results": [
       {
         "person_id": 51,
         "source_value": "PATIENT_0001",
         "age": 68,
         "gender": "Female",
         "tumor_profile": [...],
         "treatments": [...]
       }
     ]
   }

2. Get Single Patient
   GET /patients/{person_id}/
   
   Returns: Basic patient information

3. Get Cancer Profile (FULL JOURNEY)
   GET /patients/{person_id}/cancer-profile/
   
   Returns:
   {
     "person_id": 51,
     "source_value": "PATIENT_0001",
     "age": 68,
     "gender": "Female",
     "tumor": {...},
     "diagnosis_omop": {...},  // Standardized diagnosis
     "treatments": [...],       // With nested adverse events
     "adverse_events": [...],   // All adverse events
     "recent_labs": [...]       // Last 20 measurements
   }

4. Get Adverse Events
   GET /patients/{person_id}/adverse-events/
   
   Returns:
   {
     "person_id": 51,
     "total_events": 3,
     "adverse_events": [...]
   }

5. Filter by Stage
   GET /patients/by-stage/?stage=III
   
   Returns: All patients with Stage III cancer

COHORT ENDPOINTS
================

1. Cohort Statistics
   GET /cohorts/statistics/?stage=III&histology=Adenocarcinoma
   
   Returns:
   {
     "filters": {...},
     "total_patients": 17,
     "by_stage": [{"stage": "III", "count": 17}],
     "by_histology": [{"histology": "Adenocarcinoma", "count": 12}],
     "stages_represented": ["III", ...],
     "histologies_represented": ["Adenocarcinoma", ...],
     "treatment_response_distribution": {
       "CR": 5,
       "PR": 7,
       "SD": 3,
       "PD": 2
     },
     "top_regimens": [...],
     "adverse_event_grade_distribution": [...]
   }

2. Treatment Response Distribution
   GET /cohorts/treatment-responses/
   
   Returns:
   {
     "total_treatments": 51,
     "response_distribution": {
       "CR": 14,
       "PR": 18,
       "SD": 11,
       "PD": 8
     }
   }

DATA QUALITY ENDPOINTS
======================

1. ETL Summary
   GET /data-quality/summary/
   
   Returns: Latest ETL run info + data loaded counts
"""