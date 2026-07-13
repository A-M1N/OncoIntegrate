from django.urls import path
from . import views
 
urlpatterns = [
    path('patients/', views.patient_list, name='patient-list'),
    path('patients/<int:person_id>/', views.patient_detail, name='patient-detail'),
    path('patients/<int:person_id>/cancer-profile/', views.patient_cancer_profile, name='patient-cancer-profile'),
    path('patients/<int:person_id>/adverse-events/', views.patient_adverse_events, name='patient-adverse-events'),
    path('patients/by-stage/', views.patients_by_stage, name='patients-by-stage'),
    
    #---------------------------------------------------------------------------
    path('cohorts/statistics/', views.cohort_statistics, name='cohort-statistics'),
    path('cohorts/treatment-responses/', views.treatment_responses, name='treatment-responses'),
    
    #--------------------------------------------------------------------------------------------
    path('data-quality/summary/', views.data_quality_summary, name='data-quality-summary'),
    path('data-quality/metrics/', views.data_quality_metrics, name='data-quality-metrics'),
]
