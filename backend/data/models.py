from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Concept(models.Model):
    """
    For Medical Codes and their meaning such as concept_id:8507 , concept_name: Female
    """
    
    concept_id = models.IntegerField(primary_key=True)
    concept_name = models.CharField(max_length=255)
    
    concept_code = models.CharField(max_length=50)
    
    domain_id = models.CharField(
        max_length=20,
        choices=[('Gender','Gender'),
                 ('Race','Race'),
                 ('Condition','Condition'),
                 ('Drug','Drug'),
                 ('Measurement','Measurement'),
                 ('Visit','Visit'),
                 ('Procedure','Procedure'),
                 ('Metadata','Metadata'),
                 ]
    )
    vocabulary_id = models.CharField(
        max_length=20,
        choices=[
            ('SNOMED','SNOMED-CT'),
            ('ICD10','ICD-10'),
            ('RxNorm','RxNorm'),
            ('LOINC','LOINC'),
            ('GENDER','Gender'),
            ('RACE','Race'),
        ]
    )
    
    valid_start_date = models.DateField(default='1900-01-01')
    valid_end_date = models.DateField(default = '2099-12-31')
    
    class Meta:
        db_table = 'omop_concept'
        verbose_name = 'Concept'
        verbose_name_plural = 'Concepts'
        
    def __str__(self):
        return f"{self.concept_id}: {self.concept_name}"

class DataSource(models.Model):
    
    SOURCE_TYPE_CHOICES = [
        ('JSON','JSON Files'),
        ('CSV','CSV Files'),
        ('HL7','HL7 Messages'),
        ('FHIR','FHIR API'),
        ('ODBC','ODBC Database'),
        ('KAFKA','Kafka Stream'),
        ('FILE','Custom Format'),
    ]
    source_type = models.CharField(
    max_length=20,
    choices=SOURCE_TYPE_CHOICES,
    default='JSON'
    )
    
    # Identification
    name = models.CharField(
        max_length=50,
        help_text='System Identifier (REDCap, HL7, Kafka etc)'
    )
    display_name = models.CharField(max_length=100, help_text= 'Human-readable name')
    
    description = models.TextField( blank = True, help_text= 'Details about the data source')
    
    connection_config = models.JSONField(default = dict, blank = True, help_text="Configuration for connecting to this source")

    parser_class = models.CharField(max_length = 255, blank=True,help_text= 'Full path to ETL class etl.redcap_etl.REDCapETL')
    
    batch_schedule = models.CharField(max_length=100, blank = True, help_text= "Cron expression for batch ETL")

    is_active = models.BooleanField(default=True, help_text = "Enable/Disable this source")
    
    is_real_time = models.BooleanField(default = False, help_text = "True if streaming (Kafka or HL7), False if batch CSV/JSON")
    
    min_mapping_confidence = models.FloatField(
        default = 0.9,
        validators=[MinValueValidator(0.0),MaxValueValidator(1.0)],
        help_text = "Minimum confidence score for concept mappings to be used"
        )
    max_unmapped_percent = models.FloatField(
        default = 10.0,
        validators = [MinValueValidator(0.0),MaxValueValidator(100.0)],
        help_text = "Fail ETL if more than X% of records unmapped"
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    last_etl_run = models.DateTimeField(null = True, blank = True) 
    
    class Meta:
        db_table = "data_source"
        verbose_name = 'Data Source'
        verbose_name_plural = 'Data Sources'
        indexes = [
            models.Index(fields = ['name','is_active']),
        ]
    def __str__(self):
        status = "✅" if self.is_active else "❌"
        return f"{status} {self.name}: {self.display_name}"
    
    def get_connection_string(self):
        """Return connection configuration"""
        return self.connection_config or {}
    
    def get_parser_class(self):
        """Dynamically import and return ETL parser class"""
        from django.utils.module_loading import import_string
        
        if not self.parser_class:
            raise ValueError(f"No parser class configured for {self.name}")
        
        try: 
            return import_string(self.parser_class)
        except ImportError as e:
            raise ValueError(
                f"Could not import parser class '{self.parser_class} : {str(e)}"
            )
            
class ConceptMapping(models.Model):
    # Maps Source system Codes (RedCap, Synthea,etc) to OMOP concepts and handles mismatch between source and standard codes
    
    MAPPING_TYPE_CHOICES = [
        ("EXACT","Exact match - Definitely correct"),
        ("PARENT","Parent Concept - Hierarchical match"),
        ("FUZZY","Fuzzy Match - Similar names"),
        ("MANUAL","Manual Review - Human-curated"),
    ]
    
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='concept_mappings',
        help_text = 'Which data source this mapping applies to'
    )
    
    source_code = models.CharField(
        max_length=100,
        help_text="Code from source system (e.g., 'pembrolizumab', 'C34.1', 'PEMBRO')"
        ) # C34.1 From Redcap 
    source_value = models.CharField(
        max_length=255,
        help_text="Human-readable value (e.g., 'Pembrolizumab')"
        ) 
    
    source_field = models.CharField(
        max_length=100,
        blank=True,
        help_text = "Which field this comes from ex: drug_1_name"
    )
    source_vocabulary = models.CharField(
    max_length=50,
    blank=True,
    help_text="ICD10, RxNorm, LOINC, Local..."
    )
    
    # Target OMOP concept 
    target_concept = models.ForeignKey(
        Concept,
        on_delete = models.PROTECT,
        related_name= 'source_mappings',
        help_text = 'Standard OMOP concept this maps to '
    )
    # Mapping meta-data 
    mapping_type = models.CharField(
        max_length = 20,
        choices = MAPPING_TYPE_CHOICES,
        default='EXACT'
    )
    confidence_score = models.FloatField(
        default = 1.0,
        validators=[MinValueValidator(0.0),MaxValueValidator(1.0)],
        help_text = "Confidence in this mapping: 1.0=>certain , 0.5=guess, 0.0=wrong"
    )
    notes = models.TextField(
        blank=True,
        help_text = "Why this mapping exists, any caveats,etc."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'omop_concept_mapping'
        unique_together = ('data_source','source_code','source_value','source_field')
        indexes = [
            models.Index(fields=['data_source','source_code']),
            models.Index(fields=['data_source','confidence_score']),
        ]
    
    def __str__(self):
        confidence_emoji = {
            1.0: "✅",
            0.9: "✓",
            0.7: "⚠️",
            0.5: "❓"
        }
        emoji = confidence_emoji.get(
            round(self.confidence_score * 10) / 10,
            "❌"
        )
        return (
            f"{emoji} {self.data_source.name}: "
            f"{self.source_value} → {self.target_concept.concept_name} "
            f"({self.confidence_score})"
        )

class UnmappedConcept(models.Model):
    # Tracks Concepts that couldn't be mapped during ETL
    STATUS_CHOICES = [
        ('UNRESOLVED','Unresolved - Needs attention'),
        ('MAPPED','Mapped - Now has ConceptMapping'),
        ('IGNORED','Ignored - Not a valid concept')
    ]
    
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='unmapped_concepts'
    )
    
    source_code = models.CharField(max_length=100)
    source_value = models.CharField(max_length=255, blank = True)
    source_field = models.CharField(
        max_length=100,
        blank=True,
        help_text = "Which field this unmapped value came from"
    )
    domain_id = models.CharField(
        max_length=20,
        choices=[
            ('Condition', 'Condition/Diagnosis'),
            ('Drug', 'Drug/Medication'),
            ('Measurement', 'Lab/Measurement'),
            ('Visit', 'Visit Type'),
            ('Procedure', 'Procedure'),
            ('Gender', 'Gender'),
            ('Race', 'Race/Ethnicity'),
            ('Other', 'Other'),
        ]
    )
    # Tracking occurrence
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    occurrence_count = models.IntegerField(
        default = 1,
        help_text="How many times we've seen this unmapped value"
    )
    # Resolution
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="UNRESOLVED"
    )
    resolved_to = models.ForeignKey(
        Concept,
        on_delete=models.SET_NULL,
        null = True,
        blank=True,
        help_text = 'Which concept this was eventually mapped to'
    )
    notes = models.TextField(
        blank=True,
        help_text="Why unmapped or how it was resolved"
    )
    class Meta:
        db_table = 'omop_unmapped_concept'
        unique_together = ('data_source','source_code','domain_id')
        indexes = [
            models.Index(fields = ['data_source', 'status']),
            models.Index(fields = ['status','occurrence_count']),
        ]
        
    def __str__(self):
        return (
            f"[{self.data_source.name}] {self.source_value} "
            f"({self.domain_id}) - x{self.occurrence_count}"
        )
    @property
    def is_critical(self):
        """Is this unmapped concept problematic?"""
        return self.occurrence_count >= 5  # If occurs 5+ times, it's critical
    
class Person(models.Model):
        """
        One row per patient Example:
        - person_id: 1, gender_concept_id: 8507 (Female), year_of_birth: 1965
        """
        person_id = models.AutoField(primary_key = True)
        
        gender_concept = models.ForeignKey(
            Concept,
            on_delete = models.PROTECT,
            related_name = 'persons_gender',
            limit_choices_to = {'vocabulary_id' : 'GENDER'} 
        )
        
        year_of_birth = models.IntegerField()
        month_of_birth = models.IntegerField(null = True, blank = True)
        day_of_birth = models.IntegerField( null = True, blank = True)
        
        race_concept = models.ForeignKey(
            Concept,
            on_delete = models.SET_NULL,
            null = True,
            blank = True,
            related_name = 'persons_race',
            limit_choices_to = {'vocabulary_id' : 'RACE'} 
        )
        # Original Data before Standardization -> Source Value
        person_source_value = models.CharField(max_length = 255,db_index=True)
        
        created_at = models.DateTimeField(auto_now_add = True)
        updated_at = models.DateTimeField(auto_now = True)
        
        class Meta:
            db_table = 'omop_person'
            verbose_name = 'Person'
            verbose_name_plural = 'Persons'
            indexes = [
                models.Index(fields=['person_source_value']),  # ✅
                models.Index(fields=['year_of_birth']),  # ✅
            ]
            
        def __str__(self):
            return f"Patient {self.person_id} (Born {self.year_of_birth})"
        
        def get_age(self):
            from datetime import datetime
            return datetime.now().year - self.year_of_birth
        
class VisitOccurrence(models.Model):
    
    # When Patient Came To Hospital EX: - patient1 visited on 2026-01-01 for outpatient care 
    visit_occurrence_id = models.AutoField(primary_key = True)
    
    # Which Patient 
    person = models.ForeignKey(
        Person,
        on_delete = models.CASCADE,
        related_name = 'visits' # i can apply person.visits.all() here
    )
    
    visit_concept = models.ForeignKey(
        Concept,
        on_delete = models.PROTECT,
        related_name = 'visits',
        limit_choices_to = {'domain_id' : "Visit"}
    )
    
    visit_start_date = models.DateField(db_index=True)
    visit_end_date = models.DateField(null = True, blank=True)
    
    visit_source_value = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'omop_visit_occurrence'
    
    def __str__(self):
        return f"Visit {self.visit_occurrence_id} ({self.visit_start_date})"
    
class ConditionOccurrence(models.Model):
    
    condition_occurrence_id = models.AutoField(primary_key=True)
    
    person = models.ForeignKey(
        Person,
        on_delete = models.CASCADE,
        related_name= 'conditions'
    )
    condition_concept = models.ForeignKey(
        Concept,
        on_delete=models.PROTECT,
        related_name= 'conditions',
        limit_choices_to = {'domain_id' : 'Condition'}
    )
    
    condition_start_date = models.DateField(db_index=True)
    condition_end_date = models.DateField(null = True, blank=True)
    
    # Which Visit
    visit_occurrence = models.ForeignKey(
        VisitOccurrence,
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name= 'conditions'
    )
    
    condition_source_value = models.CharField(max_length=255,null = True, blank=True)
    
    class Meta:
        db_table = 'omop_condition_occurrence'
        verbose_name = 'Condition Occurrence'
        verbose_name_plural = 'Condition Occurrences'
        indexes = [
            models.Index(fields = ['person','condition_start_date']),
        ]
    def __str__(self):
        return f"{self.person} - {self.condition_concept} ({self.condition_start_date})"
    
class DrugExposure(models.Model):
    drug_exposure_id = models.AutoField(primary_key=True)
    
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='medications'
    )
    # What Medication 
    drug_concept = models.ForeignKey(
        Concept,
        on_delete= models.PROTECT,
        related_name= 'medications',
        limit_choices_to = {'domain_id': 'Drug'}
    )
    # When
    drug_exposure_start_date = models.DateField(db_index=True)
    drug_exposure_end_date = models.DateField(null=True, blank=True)
    
    # How much ?
    quantity = models.DecimalField(max_digits=10, decimal_places= 2, null = True, blank = True )
    days_supply = models.IntegerField(null= True, blank= True)
    
    # Which Visit 
    visit_occurrence = models.ForeignKey(
        VisitOccurrence,
        on_delete=models.SET_NULL,
        null = True,
        blank = True,
        related_name='medications'
    )
    
    drug_source_value = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'omop_drug_exposure'
        verbose_name = 'Drug Exposure'
        verbose_name_plural = 'Drug Exposures'
        indexes = [
            models.Index(fields=['person','drug_exposure_start_date']),
        ]
    def __str__(self):
        return f"{self.person} - {self.drug_concept} ({self.drug_exposure_start_date})"

class ObservationPeriod(models.Model):
    observation_period_id = models.AutoField(primary_key=True)
    
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='observation_periods'
    )
    
    observation_period_start_date = models.DateField()
    observation_period_end_date = models.DateField()
    
    class Meta:
        db_table = 'omop_observation_period'
        verbose_name = 'Observation Period'
        verbose_name_plural = 'Observation Periods'
    
    def __str__ (self):
        return f"{self.person} ({self.observation_period_start_date} to {self.observation_period_end_date})" 

class ProcedureOccurrence(models.Model):
    """
    Patient procedure/surgery Example:
    - Patient 1 had CT scan on 2026-01-20 - Patient 2 had surgery on 2026-02-15
    """
    procedure_occurrence_id = models.AutoField(primary_key=True)
    
    person = models.ForeignKey(
        Person,
        on_delete= models.CASCADE,
        related_name= 'procedures'
    )
    
    procedure_concept = models.ForeignKey(
        Concept,
        on_delete=models.PROTECT,
        related_name='procedures',
        limit_choices_to={'domain_id': 'Procedure'}
    )
    
    procedure_date = models.DateField(db_index=True)
    
    visit_occurrence = models.ForeignKey(
        VisitOccurrence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='procedures'
    )
    procedure_source_value = models.CharField(max_length=255,null=True,blank=True)
    
    class Meta:
        db_table = 'omop_procedure_occurrence'
        verbose_name = 'Procedure Occurrence'
        verbose_name_plural = 'Procedure Occurrences'
        indexes = [
            models.Index(fields = ['person','procedure_date']),
        ]
    def __str__(self):
        return f"{self.person} - {self.procedure_concept} ({self.procedure_date})"

class Measurement(models.Model):
    """
    Patient lab result or clinical measurement Example:
    - Patient 1 had Creatinine test on 2026-06-01 with value 1.5 mg/dL
    """
    measurement_id = models.AutoField(primary_key=True)
    
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name= 'measurements'
    )
    
    measurement_concept = models.ForeignKey(
        Concept,
        on_delete=models.PROTECT,
        related_name='measurements',
        limit_choices_to= {'domain_id' : 'Measurement'}
    )
    measurement_date = models.DateField(db_index=True)
    
    # Result 
    value_as_number = models.DecimalField(max_digits=15, decimal_places=3 , null=True, blank=True)
    
    # Unit
    unit_source_value = models.CharField(max_length=50, null=True, blank=True)
    
    #Whats Normal 
    range_low = models.DecimalField(max_digits=15, decimal_places=3, null = True, blank = True)
    range_high = models.DecimalField(max_digits=15, decimal_places=3, null = True, blank = True)
    
    visit_occurrence = models.ForeignKey(
        VisitOccurrence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='measurements'
    )
    
    measurement_source_value = models.CharField(max_length=255,null=True,blank=True)
    class Meta:
        db_table= 'omop_measurement'
        verbose_name = 'Measurement'
        verbose_name_plural = 'Measurements'
        indexes = [
            models.Index(fields = ['person','-measurement_date']),
        ]
    def __str__(self):
        return f"{self.person} - {self.measurement_concept} ({self.measurement_date})"
    
    def is_abnormal(self):
        if self.value_as_number is None or self.range_low is None or self.range_high is None: 
            return None
        return not (self.range_low <= self.value_as_number <= self.range_high)

class ETLLog(models.Model):
    """ 
    Track each time ETL Pipeline runs EXAMPLE : 
    - ETL run on 24-06-2026 at 10.00 AM 
    - Loaded 2000 records in 30 seconds 
    - Status : SUCCESS 
    """
    STATUS_CHOICES = [
        ('STARTED','Started'),
        ('RUNNING','Running'),
        ('SUCCESS','Success'),
        ('FAILED','Failed'),
        ('PARTIAL','Partial'),
    ]
    
    log_id = models.AutoField(primary_key= True)
    
    run_time = models.DateTimeField(auto_now_add=True,db_index=True)
    
    source_name = models.CharField(max_length=100,default="Unknown")
    
    records_processed = models.IntegerField(default=0)
    records_loaded = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    records_skipped = models.IntegerField(default=0)
    
    duration_seconds = models.IntegerField(null = True,blank=True)
    
    status = models.CharField(max_length=20, choices =STATUS_CHOICES)
    
    
    
    error_message = models.TextField(null=True,blank=True)
    
    class Meta:
        db_table = 'omop_etl_log'
        verbose_name = 'ETL Log'
        verbose_name_plural = 'ETL Logs'
        ordering = ['-run_time']
    
    def __str__(self):
        return f"ETL {self.log_id} - {self.status} ({self.run_time})"

class DataQualityLog(models.Model):
    """
        Track Data Quality metrics over time Ex: - Check on 2026-01-01 at 10:00 AM
        - Total Patients: 5000
        - Quality Score : 95.2%
        - Issues Found : 15 
    """
    quality_id = models.AutoField(primary_key=True)
    
    checked_date = models.DateTimeField(auto_now_add=True, db_index=True)
    
    total_patients = models.IntegerField(default = 0)
    total_visits = models.IntegerField(default = 0)
    total_conditions = models.IntegerField(default = 0)
    total_medications = models.IntegerField(default = 0)
    total_measurements = models.IntegerField(default = 0) 
    
    patients_with_conditions = models.IntegerField(default= 0)
    patients_with_medications = models.IntegerField(default= 0)
    patients_with_measurements = models.IntegerField(default= 0)
    
    conditions_with_null_concept = models.IntegerField(default=0)
    medications_with_null_concept = models.IntegerField(default = 0)
    invalid_date_ranges = models.IntegerField(default=0)
    
    quality_score = models.DecimalField(max_digits=5,decimal_places=2, default = 0)
    
    class Meta:
        db_table = 'omop_data_quality_log'
        verbose_name = 'Data Quality Log'
        verbose_name_plural = 'Data Quality Logs'
        ordering = ['-checked_date']
        
    def __str__(self):
        return f"Quality Check {self.quality_id} - Score {self.quality_score}% "

# CANCER-SPECIFIC MODELS 
class TumorProfile(models.Model):
    #Cancer specific tumor information Ex: Patient1 has Lung Cancer, Stage IV, diagnosed 2026-5-1
    STAGE_CHOICES = [
        ('0','Stage 0'),
        ('I','Stage I'),
        ('II','Stage II'),
        ('III','Stage III'),
        ('IV','Stage IV'),
        ('Unknown','Unknown'),
    ]
    
    HISTOLOGY_CHOICES = [
        ('Adenocarcinoma','Adenocarcinoma'),
        ('Squamous Cell','Squamous Cell'),
        ('Small Cell','Small Cell'),
        ('Large Cell','Large Cell'),
        ('Mesothelioma','Mesothelioma'),
        ('Other','Other'),
    ]
    
    tumor_id = models.AutoField(primary_key=True)
    
    person = models.ForeignKey(
        Person,
        on_delete = models.CASCADE,
        related_name= 'tumor_profiles'
    )
    
    #Which Diagnosis , Ref CONDITION_OCCURRENCE
    primary_diagnosis = models.ForeignKey(
        ConditionOccurrence,
        on_delete=models.PROTECT,
        related_name= 'tumor_profiles',
        null = True,
        blank=True
    )
    
    diagnosis_date = models.DateField()
    
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, blank=True, db_index=True)
    histology = models.CharField(max_length=100, choices = HISTOLOGY_CHOICES, blank=True, db_index=True)
    
    
    
    mutation_status = models.CharField(max_length=100, null = True, blank = True)
    
    #Clinical Notes
    notes = models.TextField(null = True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cancer_tumor_profile'
        verbose_name = 'Tumor Profile'
        verbose_name_plural = 'Tumor Profiles'
        indexes = [
            models.Index(fields=['person', 'stage']),  
            models.Index(fields=['stage', 'histology']), 
        ]
    
    def __str__(self):
        return f"{self.person} - {self.histology} Stage {self.stage}"

class TreatmentRegimen(models.Model):
    # Cancer Treatment Protocol EX: Patient 1 recieves Carboplatin + Pemetrexed 
    
    regimen_id = models.AutoField(primary_key=True)
    
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name= 'treatment_regimens'
    )
    
    tumor_profile = models.ForeignKey(
        TumorProfile,
        on_delete=models.CASCADE,
        related_name='regimens',
        null=True,
        blank=True
    )
    regimen_name = models.CharField(max_length=255)
    
    start_date = models.DateField()
    end_date = models.DateField(null = True, blank=True)
    
    #How Many Cycles 
    planned_cycles = models.IntegerField(null = True, blank=True)
    completed_cycles = models.IntegerField(default = 0 )
    
    RESPONSE_CHOICES = [
        ('CR','Complete Response'),
        ('PR','Partial Response'),
        ('SD','Stable Disease'),
        ('PD','Progressive Disease'),
        ('Unknown','Unknown'),
    ]
    best_response = models.CharField(max_length=20, choices = RESPONSE_CHOICES, default= 'Unknown', null = True, blank=True, db_index=True)
    
    class Meta:
        db_table = 'cancer_treatment_regimen'
        verbose_name = 'Treatment Regimen'
        verbose_name_plural = 'Treatment Regimens'
        indexes = [
            models.Index(fields=['person', 'best_response']),  
        ]
        
    def __str__(self):
        return f"{self.person} - {self.regimen_name} ({self.start_date})"
    
class CancerCohort(models.Model):
    # Define Cohorts of cancer patients for research EX: Lung Cancer Stage IV Patients 2015 
    
    cohort_id = models.AutoField(primary_key=True)
    
    cohort_name = models.CharField(max_length=255)
    description = models.TextField(null = True, blank=True)
    
    #Inclusion criteria 
    cancer_types = models.ManyToManyField(
        Concept,
        related_name= 'cancer_cohorts',
        limit_choices_to={'domain_id' : 'Condition'},
        help_text = 'Select cancer types to include in this cohort'
    )
    #Stage filter
    min_stage = models.CharField(max_length=20, default = '0')
    max_stage = models.CharField(max_length=20, default='IV')
    
    min_age = models.IntegerField(default=18)
    max_age = models.IntegerField(default=120)
    
    #Date range for cohort creation
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True,blank = True)
    
    #Patients in this cohort, Many-to-Many
    patients = models.ManyToManyField(
        Person,
        related_name='cancer_cohorts',
        through= 'CohortMembership'
    ) 
    created_by = models.CharField(max_length=255, null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cancer_cohort'
        verbose_name = 'Cancer Cohort'
        verbose_name_plural = 'Cancer Cohorts'
    def __str__(self):
        return self.cohort_name
    
    def get_patient_count(self):
        return self.patients.count()

class CohortMembership(models.Model):
    # Track which patients belong to which cohorts
    
    membership_id = models.AutoField(primary_key=True)
    
    # links
    cohort = models.ForeignKey(
        CancerCohort,
        on_delete=models.CASCADE
    ) 
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE
    )
    # When Added to Cohort
    added_date = models.DateTimeField(auto_now_add=True)
    
    INCLUSION_REASON = [
        ('Meets criteria','Meets all criteria'),
        ('Manual add','Manually added'),
        ('Override','Criteria override'),
    ]
    inclusion_reason = models.CharField(max_length=100,choices = INCLUSION_REASON)
    
    notes = models.TextField(null = True, blank = True )
    
    class Meta: 
        db_table = 'cancer_cohort_membership'
        unique_together =  [['cohort','person']]
        verbose_name = 'Cohort Membership'
        verbose_name_plural = 'Cohort Memberships'
    
    def __str__(self):
        return f"{self.person} in {self.cohort}"

class AdverseEvent(models.Model):
    # Track Side Effects from Treatment EX : Patient 1 experienced Grade 3 Neuropathy on 02-02-2026
    GRADE_CHOICES = [
        ('1','Grade 1 (Mild)'),
        ('2','Grade 2 (Moderate)'),
        ('3','Grade 3 (Severe)'),
        ('4','Grade 4 (Life-threatening)'),
        ('5','Grade 5 (Fatal)'),
     ]
    
    event_id = models.AutoField(primary_key=True)
    
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='adverse_events'
    )
    
    treatment_regimen = models.ForeignKey(
        TreatmentRegimen,
        on_delete=models.SET_NULL,
        null = True,
        blank= True,
        related_name='adverse_events'
    )
    
    event_name = models.CharField(max_length=255)
    event_description = models.TextField(null = True, blank = True)
    event_date = models.DateField()
    
    grade = models.CharField(max_length=10, choices = GRADE_CHOICES, db_index=True)
    
    RESOLUTION_CHOICES = [
        ('Ongoing','Ongoing'),
        ('Resolved','Resolved'),
        ('Improving','Improving'),
        ('Worsening','Worsening'),
    ]
    resolution_status = models.CharField(max_length=50, choices= RESOLUTION_CHOICES,default= 'Ongoing')
    
    
    class Meta:
        db_table = 'cancer_adverse_event'
        verbose_name = 'Adverse Event'
        verbose_name_plural = 'Adverse Events'
        indexes = [
            models.Index(fields=['person', 'grade']),  
        ]
    
    def __str__(self):
        return f"{self.person} - {self.event_name} (Grade {self.grade})"

class ClinicalTrial(models.Model):
    # Represents a research study EX :  CCE-DART Study or Lung Cancer Immunotherapy Trial 
    
    trial_id = models.AutoField(primary_key = True)
    
    trial_name = models.CharField(max_length = 255)
    trial_code = models.CharField(max_length = 100, unique=True)
    description = models.TextField(null = True, blank = True)
    
    trial_start_date = models.DateField()
    trial_end_date = models.DateField(null = True, blank = True)
    
    #Patients enrolled in that trial 
    patients = models.ManyToManyField(
        Person,
        related_name='clinical_trials',
        through = 'TrialEnrollment'
    ) 
    class Meta: 
        db_table = 'cancer_clinical_trial'
        verbose_name = 'Clinical Trial'
        verbose_name_plural = 'Clinical Trials'
    
    def __str__(self):
        return self.trial_name

class TrialEnrollment(models.Model):
    # Track patient enrollment in clinical trials ex: John CCE-DART 2026-06-01
    
    enrollment_id = models.AutoField(primary_key=True)
    
    trial = models.ForeignKey(
        ClinicalTrial,
        on_delete=models.CASCADE
    )
    
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE
    )
    
    enrollment_date = models.DateField()
    exit_date = models.DateField(null = True,blank=True)
    
    treatment_arm =  models.CharField(max_length=100, null = True, blank = True)
    
    class Meta: 
        db_table = 'cancer_trial_enrollment'
        unique_together= [['trial','person']]
    
    def __str__(self):
        return f"{self.person} enrolled in {self.trial}"