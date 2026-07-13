from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Prefetch
from django.views.decorators.http import require_http_methods
from .services import PatientService, CohortService, DataQualityService
from .models import Person,ETLLog, TumorProfile

# Create your views here.

@require_http_methods(['GET'])
def patient_list(request):
    #    GET /api/patients/?page=1&page_size=50
    #    List all patients with pagination
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size',25))
    
    # Get paginated data
    persons = Person.objects.select_related('gender_concept').prefetch_related(
        Prefetch(
            'tumor_profiles',
            TumorProfile.objects.select_related('primary_diagnosis__condition_concept')
        ),
        'treatment_regimens'
    )
    
    paginator = Paginator(persons, page_size)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'page': page,
        'page_size': page_size,
        'results': [
            PatientService._serialize_patient_list_item(p) 
            for p in page_obj
        ]
    })


@require_http_methods(["GET"])
def patient_detail(request, person_id):
    """
    GET /api/patients/{person_id}/
    Get single patient basic information
    """
    try:
        patient = PatientService.get_patient(person_id)
        return JsonResponse(patient)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


@require_http_methods(["GET"])
def patient_cancer_profile(request, person_id):
    try:
        profile = PatientService.get_cancer_profile(person_id)
        return JsonResponse(profile)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)
 
 
@require_http_methods(["GET"])
def patient_adverse_events(request, person_id):
    """
    GET /api/patients/{person_id}/adverse-events/
    Get adverse events for specific patient
    """
    try:
        events = PatientService.get_adverse_events(person_id)
        return JsonResponse(events)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)
 
@require_http_methods(["GET"])
def patients_by_stage(request):
    """
    GET /api/patients/by-stage/?stage=III
    Get all patients with specific cancer stage
    """
    stage = request.GET.get('stage')
    if not stage:
        return JsonResponse({'error': 'stage parameter required'}, status=400)
    
    result = PatientService.get_patients_by_stage(stage)
    return JsonResponse(result)
 

@require_http_methods(["GET"])
def cohort_statistics(request):
    """GET /api/cohorts/statistics?stage=III&histology=adeno"""
    stage = request.GET.get('stage')
    histology = request.GET.get('histology')
    
    stats = CohortService.get_statistics(stage=stage, histology=histology)
    return JsonResponse(stats)
 

@require_http_methods(["GET"])
def treatment_responses(request):
    """
    GET /api/cohorts/treatment-responses/
    Get distribution of treatment responses across all patients
    """
    result = CohortService.get_treatment_responses()
    return JsonResponse(result)


@require_http_methods(["GET"])
def data_quality_summary(request):
    """
    GET /api/data-quality/summary/
    Get comprehensive data quality metrics and ETL run information
    """
    summary = DataQualityService.get_summary()
    return JsonResponse(summary)


def data_quality_metrics(request):
    """
    GET /api/data-quality/metrics
 
    NOTE: ordering by -pk as a stand-in for "most recent run" since I
    haven't confirmed ETLLog's timestamp field name. If ETLLog has a
    field like `created_at` or `run_at` (likely, given it's probably
    auto_now_add=True), swap the .order_by('-pk') below for that field --
    it's a more semantically correct way to find the latest run than
    relying on primary key ordering.
    """
    latest_run = ETLLog.objects.order_by('-pk').first()
 
    if not latest_run:
        return JsonResponse({'error': 'No ETL runs found'}, status=404)
 
    return JsonResponse({
        'source_name': latest_run.source_name,
        'status': latest_run.status,
        'records_processed': latest_run.records_processed,
        'records_loaded': latest_run.records_loaded,
        'records_failed': latest_run.records_failed,
        'records_skipped': latest_run.records_skipped,
        'duration_seconds': latest_run.duration_seconds,
    })