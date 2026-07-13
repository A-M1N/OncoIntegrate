from datetime import date

from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404

from .models import (
    Person,
    TumorProfile,
    TreatmentRegimen,
    AdverseEvent,
    Measurement,
    ConditionOccurrence,
    DrugExposure,
)

class PatientService:
    
    @staticmethod
    def get_all_patients(page = 1, page_size=50):
        start = (page - 1) * page_size
        end = start + page_size

        persons = (
            Person.objects
            .select_related(
                "gender_concept"  
            )
            .prefetch_related(
                Prefetch(
                    "tumor_profiles",
                    queryset=TumorProfile.objects.select_related(
                        "primary_diagnosis__condition_concept"
                    )
                ),
                "treatment_regimens"
            )
            .order_by("person_id")[start:end]
        )

        total = Person.objects.count()

        return {
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": [
                PatientService._serialize_patient_list_item(person)
                for person in persons
            ]
        }


    @staticmethod
    def _serialize_patient_list_item(person):
        """
        Serialize patient for list view.
        Uses prefetched relations.
        """

        # Uses prefetched tumor profiles
        tumor = person.tumor_profiles.first()

        # Uses prefetched treatment regimens
        treatments = person.treatment_regimens.all()

        age = None
        if person.year_of_birth:
            age = date.today().year - person.year_of_birth

        return {
            "person_id": person.person_id,
            "source_value": person.person_source_value,
            "age": age,
            "gender": (
                person.gender_concept.concept_name
                if person.gender_concept
                else None
            ),

            "tumor_profile": (
                [PatientService._serialize_tumor(tumor)]
                if tumor
                else []
            ),

            "treatments": [
                PatientService._serialize_regimen(t)
                for t in treatments
            ],
        }


    @staticmethod
    def get_patient(person_id):
        """
        GET /api/patients/{id}
        Returns basic patient information
        """

        person = get_object_or_404(
            Person.objects
            .select_related(
                "gender_concept"
            )
            .prefetch_related(
                Prefetch(
                    "tumor_profiles",
                    queryset=TumorProfile.objects.select_related(
                        "primary_diagnosis__condition_concept"
                    )
                ),
                "treatment_regimens"
            ),
            person_id=person_id
        )

        tumor = person.tumor_profiles.first()

        treatments = person.treatment_regimens.all()

        age = None
        if person.year_of_birth:
            age = date.today().year - person.year_of_birth

        return {
            "person_id": person.person_id,
            "source_value": person.person_source_value,
            "age": age,
            "gender": (
                person.gender_concept.concept_name
                if person.gender_concept
                else None
            ),

            "tumor_profile": (
                [PatientService._serialize_tumor(tumor)]
                if tumor
                else []
            ),

            "treatments": [
                PatientService._serialize_regimen(t)
                for t in treatments
            ],
        }

    
    
    
    # To render single patient's cancer profile
    @staticmethod
    def get_cancer_profile(person_id):
        # select_related() pulls the gender concept in the same query
        # avoids a second round trip just to read person.gender_concept.name
        person = Person.objects.select_related(
            'gender_concept'
        ).prefetch_related(
            Prefetch(
                'tumor_profiles',
                TumorProfile.objects.select_related(
                    'primary_diagnosis__condition_concept'
                )
            ),
            Prefetch(
                'treatment_regimens',
                TreatmentRegimen.objects.prefetch_related(
                    'adverse_events'  # Nested prefetch
                )
            ),
            Prefetch(
                'adverse_events',
                AdverseEvent.objects.select_related('treatment_regimen')
            ),
            Prefetch(
                'measurements',
                Measurement.objects.select_related('measurement_concept')
            ),
            Prefetch(
                'conditions',
                ConditionOccurrence.objects.select_related('condition_concept')
            )
        ).get(person_id= person_id)
        
        tumor = person.tumor_profiles.first()
        regimens  = person.treatment_regimens.all()
        
        adverse_events = person.adverse_events.all()
        recent_labs = person.measurements.all().order_by('-measurement_date')[:20]
        
        diagnosis = person.conditions.first()
        
        age = None
        if person.year_of_birth:
            age = date.today().year - person.year_of_birth
            
        return {
            'person_id' : person.person_id,
            'source_value' :person.person_source_value,
            'age' : age,
            'gender' : person.gender_concept.concept_name if person.gender_concept else None,
            'tumor' : PatientService._serialize_tumor(tumor),
            'diagnosis_omop': PatientService._serialize_omop_diagnosis(diagnosis),
            'treatments' : [
                PatientService._serialize_regimen(r) for r in regimens 
            ],
            'adverse_events' : [
                PatientService._serialize_adverse_event(ae) for ae in adverse_events 
            ],
            'recent_labs' : [
                PatientService._serialize_lab(m) for m in recent_labs
            ],
        }
    
    @staticmethod
    def get_adverse_events(person_id):
        #Called by: GET /api/patients/{id}/adverse-events
        #Returns: Adverse events with regimen context
        
        person = get_object_or_404(Person, person_id = person_id)
        
        adverse_events = (
            AdverseEvent.objects
            .select_related('treatment_regimen')
            .filter(person=person)
            .order_by('event_date')
        ) 
        return {
            'person_id': person.person_id,
            'total_events': adverse_events.count(),
            'adverse_events': [
                PatientService._serialize_adverse_event(ae)
                for ae in adverse_events
            ]
        }
    
    @staticmethod
    def get_patients_by_stage(stage):
        # Called by: GET /api/patients/by-stage/?stage=III
        # Returns: All patients with specific cancer stage
        
        tumors = TumorProfile.objects.filter(
            stage=stage
        ).select_related('person__gender_concept')    
    
        return {
            'stage': stage,
            'total_patients': tumors.count(),
            'patients': [
                {
                    'person_id': tumor.person.person_id,
                    'source_value': tumor.person.person_source_value,
                    'age': (date.today().year - tumor.person.year_of_birth) if tumor.person.year_of_birth else None,
                    'histology': tumor.histology,
                    'mutation_status': tumor.mutation_status,
                    'treatment_count': TreatmentRegimen.objects.filter(person=tumor.person).count(),
                }
                for tumor in tumors
            ]
        }
    
    
    @staticmethod
    def _serialize_omop_diagnosis(diagnosis):
        if not diagnosis:
            return None

        return {
            'condition_concept_id': diagnosis.condition_concept.concept_id if diagnosis.condition_concept else None,
            'condition_concept_name': diagnosis.condition_concept.concept_name if diagnosis.condition_concept else None,
            'condition_source_value': diagnosis.condition_source_value,
            'condition_start_date': diagnosis.condition_start_date.isoformat() if diagnosis.condition_start_date else None,
        }
    
        
    @staticmethod
    def _serialize_tumor(tumor):
        if not tumor:
            return None
        primary_diagnosis_name = None
        if tumor.primary_diagnosis and tumor.primary_diagnosis.condition_concept:
            primary_diagnosis_name = tumor.primary_diagnosis.condition_concept.concept_name
        
        return {
            'tumor_id' : tumor.tumor_id,
            'stage' : tumor.stage,
            'histology' : tumor.histology,
            'mutation_status': tumor.mutation_status or "Unknown",
            'diagnosis_date': tumor.diagnosis_date,
            'primary_diagnosis': primary_diagnosis_name,
        }
    
    @staticmethod
    def _serialize_regimen(regimen):
        adverse_events = (
            AdverseEvent.objects
            .filter(treatment_regimen=regimen)
            .order_by('event_date')
        )
        return {
            'regimen_id': regimen.regimen_id,
            'regimen_name': regimen.regimen_name,
            'start_date': regimen.start_date.isoformat() if regimen.start_date else None,
            'end_date': regimen.end_date.isoformat() if regimen.end_date else None,
            'best_response': regimen.best_response or "Unknown",
            'cycles_completed': regimen.completed_cycles or 0,
            'adverse_events': [
                PatientService._serialize_adverse_event(ae)
                for ae in adverse_events
            ]
        }
        
    @staticmethod
    def _serialize_adverse_event(ae):
        return {
            'event_name': ae.event_name or "Unknown",
            'event_description': ae.event_description,
            'event_date': ae.event_date,
            'grade': ae.grade or 0,
            'resolution_status': ae.resolution_status,
            'regimen': ae.treatment_regimen.regimen_name if ae.treatment_regimen else None,
        }
    
    @staticmethod
    def _serialize_lab(measurement):
        name = measurement.measurement_source_value
        if measurement.measurement_concept:
            name = measurement.measurement_concept.concept_name
        return {
            'name': name,
            'value': measurement.value_as_number,
            'unit': measurement.unit_source_value,
            'date': measurement.measurement_date,
        }
    
class CohortService:
    """Aggregate / cohort-level queries across the cancer-specific layer."""
 
    @staticmethod
    def get_statistics(stage=None, histology=None):
        #   Called by: GET /api/cohorts/statistics/?stage=III&histology=Adenocarcinoma
        #   Returns: Aggregate statistics for research cohorts
        
        tumors = TumorProfile.objects.all()
        if stage:
            tumors = tumors.filter(stage=stage)
        if histology:
            tumors = tumors.filter(histology__icontains=histology)
 
        total_patients = tumors.count()
        person_ids = list(tumors.values_list('person_id', flat=True))
 
        by_stage = list(
            tumors.values('stage')
            .annotate(count=Count('pk'))
            .order_by('-count')
        )
        by_histology = list(
            tumors.values('histology')
            .annotate(count=Count('pk'))
            .order_by('-count')
        )
 
        top_regimens = list(
            TreatmentRegimen.objects
            .filter(person_id__in=person_ids)
            .values('regimen_name')
            .annotate(count=Count('pk'))
            .order_by('-count')[:5]
        )
 
        ae_grade_distribution = list(
            AdverseEvent.objects
            .filter(person_id__in=person_ids)
            .values('grade')
            .annotate(count=Count('pk'))
            .order_by('grade')
        )
        response_distribution = {}
        for response in ['CR', 'PR', 'SD', 'PD']:
            count = TreatmentRegimen.objects.filter(
                person_id__in=person_ids,
                best_response=response
            ).count()
            response_distribution[response] = count
 
        return {
            'filters': {'stage': stage, 'histology': histology},
            'total_patients': total_patients,
            'by_stage': by_stage,
            'by_histology': by_histology,
            'stages_represented': [item['stage'] for item in by_stage if item['stage']], 
            'histologies_represented': [item['histology'] for item in by_histology if item['histology']],  
            'top_regimens': top_regimens,
            'adverse_event_grade_distribution': ae_grade_distribution,
            'treatment_response_distribution': response_distribution,
        } 
        
    @staticmethod
    def get_treatment_responses():
        """
        Called by: GET /api/cohorts/treatment-responses/
        Returns: Treatment response distribution across all patients
        """
        response_distribution = {}
        responses = ['CR', 'PR', 'SD', 'PD']
        
        total_treatments = TreatmentRegimen.objects.count()
        
        for response in responses:
            count = TreatmentRegimen.objects.filter(
                best_response=response
            ).count()
            response_distribution[response] = count
        
        return {
            'total_treatments': total_treatments,
            'response_distribution': response_distribution,
        }
class DataQualityService:
    """Service layer for ETL and data quality metrics"""
    
    @staticmethod
    def get_summary():
        """
        Called by: GET /api/data-quality/summary/
        Returns: Comprehensive ETL run info + data quality metrics
        Matches what frontend expects from useDataQualitySummary()
        """
        from .models import ETLLog, DataQualityLog
        
        # Get latest ETL run (ordered by creation time)
        latest_etl = (
            ETLLog.objects
            .order_by('-run_time')  
            .first()
        )
        
        if not latest_etl:
            return {
                'latest_etl_run': None,
                'total_persons_loaded': 0,
                'total_conditions_loaded': 0,
                'total_medications_loaded': 0,
                'total_measurements_loaded': 0,
                'total_cancer_profiles': 0,
                'total_treatments': 0,
                'total_adverse_events': 0,
                'quality_issues': 0,
            }
        
        return {
            'latest_etl_run': {
                'source': latest_etl.source_name,
                'status': latest_etl.status,
                'records_processed': latest_etl.records_processed,
                'records_loaded': latest_etl.records_loaded,
                'records_failed': latest_etl.records_failed,
                'success_rate': DataQualityService._calculate_success_rate(latest_etl),
                'duration_seconds': latest_etl.duration_seconds,
            },
            'total_persons_loaded': Person.objects.count(),
            'total_conditions_loaded': ConditionOccurrence.objects.count(),
            'total_medications_loaded': DrugExposure.objects.count(),
            'total_measurements_loaded': Measurement.objects.count(),
            'total_cancer_profiles': TumorProfile.objects.count(),
            'total_treatments': TreatmentRegimen.objects.count(),
            'total_adverse_events': AdverseEvent.objects.count(),
            'quality_issues': DataQualityLog.objects.count(),
        }
    
    @staticmethod
    def _calculate_success_rate(etl_log):
        """Calculate success rate from ETL log"""
        if etl_log.records_processed == 0:
            return 0
        return (etl_log.records_loaded / etl_log.records_processed) * 100