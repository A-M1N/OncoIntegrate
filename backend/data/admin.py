from django.contrib import admin
from .models import (
    Concept, Person, VisitOccurrence, ObservationPeriod,
    ConditionOccurrence, DrugExposure, ProcedureOccurrence,
    Measurement, ETLLog, DataQualityLog ,
    # Cancer-specific models
    TumorProfile, TreatmentRegimen, CancerCohort, CohortMembership,
    AdverseEvent, ClinicalTrial, TrialEnrollment
)


# Register your models here.
@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ['concept_id', 'concept_name', 'vocabulary_id', 'domain_id']
    list_filter = ['vocabulary_id', 'domain_id']
    search_fields = ['concept_code', 'concept_name']
    readonly_fields = ['concept_id']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['person_id', 'gender_concept', 'year_of_birth', 'created_at']
    list_filter = ['gender_concept', 'year_of_birth']
    search_fields = ['person_source_value']
    readonly_fields = ['person_id', 'created_at', 'updated_at']


@admin.register(VisitOccurrence)
class VisitOccurrenceAdmin(admin.ModelAdmin):
    list_display = ['visit_occurrence_id', 'person', 'visit_concept', 'visit_start_date']
    list_filter = ['visit_start_date', 'visit_concept']
    search_fields = ['person__person_source_value']
    readonly_fields = ['visit_occurrence_id']


@admin.register(ObservationPeriod)
class ObservationPeriodAdmin(admin.ModelAdmin):
    list_display = ['observation_period_id', 'person', 'observation_period_start_date', 'observation_period_end_date']
    list_filter = ['observation_period_start_date']
    search_fields = ['person__person_source_value']
    readonly_fields = ['observation_period_id']


@admin.register(ConditionOccurrence)
class ConditionOccurrenceAdmin(admin.ModelAdmin):
    list_display = ['condition_occurrence_id', 'person', 'condition_concept', 'condition_start_date']
    list_filter = ['condition_start_date', 'condition_concept']
    search_fields = ['person__person_source_value']
    readonly_fields = ['condition_occurrence_id']


@admin.register(DrugExposure)
class DrugExposureAdmin(admin.ModelAdmin):
    list_display = ['drug_exposure_id', 'person', 'drug_concept', 'drug_exposure_start_date', 'quantity']
    list_filter = ['drug_exposure_start_date', 'drug_concept']
    search_fields = ['person__person_source_value']
    readonly_fields = ['drug_exposure_id']


@admin.register(ProcedureOccurrence)
class ProcedureOccurrenceAdmin(admin.ModelAdmin):
    list_display = ['procedure_occurrence_id', 'person', 'procedure_concept', 'procedure_date']
    list_filter = ['procedure_date', 'procedure_concept']
    search_fields = ['person__person_source_value']
    readonly_fields = ['procedure_occurrence_id']


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['measurement_id', 'person', 'measurement_concept', 'measurement_date', 'value_as_number']
    list_filter = ['measurement_date', 'measurement_concept']
    search_fields = ['person__person_source_value']
    readonly_fields = ['measurement_id']


@admin.register(ETLLog)
class ETLLogAdmin(admin.ModelAdmin):
    list_display = ['log_id', 'run_time', 'source_name', 'status', 'records_processed', 'records_loaded']
    list_filter = ['status', 'run_time', 'source_name']
    readonly_fields = ['log_id', 'run_time']


@admin.register(DataQualityLog)
class DataQualityLogAdmin(admin.ModelAdmin):
    list_display = ['quality_id', 'checked_date', 'quality_score', 'total_patients']
    list_filter = ['checked_date']
    readonly_fields = ['quality_id', 'checked_date']


# CANCER-SPECIFIC MODELS

@admin.register(TumorProfile)
class TumorProfileAdmin(admin.ModelAdmin):
    list_display = ['tumor_id', 'person', 'stage', 'histology', 'diagnosis_date']
    list_filter = ['stage', 'histology', 'diagnosis_date']
    search_fields = ['person__person_source_value']
    readonly_fields = ['tumor_id', 'created_at', 'updated_at']


@admin.register(TreatmentRegimen)
class TreatmentRegimenAdmin(admin.ModelAdmin):
    list_display = ['regimen_id', 'person', 'tumor_profile', 'regimen_name', 'start_date', 'best_response']
    list_filter = ['start_date', 'best_response']
    search_fields = ['person__person_source_value', 'regimen_name']
    readonly_fields = ['regimen_id']


@admin.register(CancerCohort)
class CancerCohortAdmin(admin.ModelAdmin):
    list_display = ['cohort_id', 'cohort_name', 'min_stage', 'max_stage', 'created_at']
    list_filter = ['created_at']
    search_fields = ['cohort_name', 'description']
    readonly_fields = ['cohort_id', 'created_at', 'updated_at']
    filter_horizontal = ['cancer_types']
    
    def get_patient_count(self, obj):
        return obj.get_patient_count()
    get_patient_count.short_description = 'Patient Count'


@admin.register(CohortMembership)
class CohortMembershipAdmin(admin.ModelAdmin):
    list_display = ['membership_id', 'person', 'cohort', 'inclusion_reason', 'added_date']
    list_filter = ['added_date', 'inclusion_reason']
    search_fields = ['person__person_source_value', 'cohort__cohort_name']
    readonly_fields = ['membership_id', 'added_date']


@admin.register(AdverseEvent)
class AdverseEventAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'person', 'event_name', 'grade', 'event_date', 'resolution_status']
    list_filter = ['grade', 'event_date', 'resolution_status']
    search_fields = ['person__person_source_value', 'event_name']
    readonly_fields = ['event_id']


@admin.register(ClinicalTrial)
class ClinicalTrialAdmin(admin.ModelAdmin):
    list_display = ['trial_id', 'trial_name', 'trial_code', 'trial_start_date', 'trial_end_date']
    list_filter = ['trial_start_date']
    search_fields = ['trial_name', 'trial_code']
    readonly_fields = ['trial_id']


@admin.register(TrialEnrollment)
class TrialEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['enrollment_id', 'person', 'trial', 'enrollment_date', 'treatment_arm']
    list_filter = ['enrollment_date', 'treatment_arm']
    search_fields = ['person__person_source_value', 'trial__trial_name']
    readonly_fields = ['enrollment_id']