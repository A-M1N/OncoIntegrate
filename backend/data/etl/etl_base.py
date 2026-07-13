from abc import ABC, abstractmethod
from datetime import datetime
from collections import defaultdict
from django.db import transaction
from django.utils import timezone
from data.models import Person,Concept,VisitOccurrence,ConditionOccurrence, DrugExposure, Measurement, ETLLog , DataSource, ConceptMapping, UnmappedConcept
from data.models import TumorProfile, TreatmentRegimen , AdverseEvent
import logging

logger = logging.getLogger(__name__)

class BaseETL(ABC):
    # Abstract Base Class for all ETL Pipelines
    # Subclasses (RedCap,Synthea)  implement their own extract() method 
    
    def __init__(self , data_source_name):
        try:
            self.data_source = DataSource.objects.get(
                name=data_source_name,
                is_active=True
            )
        except DataSource.DoesNotExist:
            available = ', '.join(
                DataSource.objects.filter(is_active=True)
                .values_list('name', flat=True)
            )
            raise ValueError(
                f"Unknown data source: {data_source_name}. "
                f"Available: {available}"
            )
        self.data_source_name = self.data_source.name
                
        self.start_time = None
        self.end_time = None
        
        # Statistics
        self.records_processed = 0 
        self.records_loaded = 0 
        self.records_failed = 0
        self.records_skipped = 0
        self.unmapped_count = 0
        
        # Data Containers
        self.persons_data = []
        self.conditions_data = []
        self.medications_data = []
        self.measurements_data = [] 
        self.visits_data = []
        self.concept_map = {}
        
        self.tumor_profiles_data = []
        self.treatment_regimens_data = []
        self.adverse_events_data = []
        
        # OPTIMIZATION: Build caches for THIS batch only
        self._person_source_values_cache = None
        self._tumor_profiles_cache = None
        self._treatment_regimens_cache = None
        
        # to prevent n+1 queries problem
        self.load_concept_caches()
        
    def load_concept_caches(self):
        #Load all concepts and mappings in memory 
        print(f"Loading concept caches for {self.data_source.display_name}...")
        
        #Cache 1 All concepts by ID
        self.concept_by_id = {
            c.concept_id : c
            for c in Concept.objects.all()
        }

        #Cache 2 All concepts by code 
        self.concept_by_code = {
            c.concept_code : c
            for c in Concept.objects.all()
        }
        
        #Cache 3 All concepts by nomralized name
        self.concept_by_name = {
            self.normalize(c.concept_name) : c
            for c in Concept.objects.all()
        }   
        
        #Cache 4 ConceptMappings for this data source (high confidence first )
        self.mapping_cache = {}
        
        mappings = ConceptMapping.objects.filter(
            data_source = self.data_source,
            confidence_score__gte=self.data_source.min_mapping_confidence
        ).select_related('target_concept').order_by('-confidence_score') 
        
        for mapping in mappings:
            key = self.normalize(mapping.source_code)
            self.mapping_cache[key] = {
                'concept_id' : mapping.target_concept.concept_id,
                'confidence' : mapping.confidence_score,
                'type' : mapping.mapping_type 
            }      
        
        logger.info(
            f"Loaded {len(self.concept_by_id)} concepts, "
            f"{len(self.mapping_cache)} high-confidence mappings "
            f"(threshold: {self.data_source.min_mapping_confidence})"
        )

    def normalize(self, text):
        if text is None:
            return None
        return text.lower().strip() 
    
       
    def resolve_concept(self, source_code, source_value = None, domain_id = None, source_field = None):
        #Multi strategy concept resolution with ConceptMapping Support
        """
        Strategies (in order):
        1. ConceptMapping (source → OMOP, high confidence)
        2. Direct code lookup
        3. Normalized name lookup
        4. Track as unmapped
        
        Args:
            source_code: Code from source system (e.g., "pembrolizumab")
            source_value: Human-readable value (e.g., "Pembrolizumab")
            domain_id: OMOP domain (Condition, Drug, Measurement, etc.)
            source_field: Which field this came from (e.g., "drug_1_name")
        
        Returns:
            concept_id (int) or None
        """
        if not source_code:
            return None
        # Strategy 1 Concept Mapping 
        mapping_key = self.normalize(source_code)
        if mapping_key in self.mapping_cache:
            mapping_info = self.mapping_cache[mapping_key]
            concept_id = mapping_info['concept_id']
            
            logger.debug(
                f"✓ ConceptMapping: {source_code} → {concept_id} "
                f"({mapping_info['type']}, confidence: {mapping_info['confidence']})"
            )
            
            return concept_id 
            
        #  Strategy 2 Try with source_value
        if source_value:
            mapping_key = self.normalize(source_value)
            if mapping_key in self.mapping_cache:
                return self.mapping_cache[mapping_key]['concept_id']
        
        # Strategy 3 Direct Code lookup concept.concept_code
        if source_code in self.concept_by_code:
            concept_id = self.concept_by_code[source_code].concept_id
            logger.debug(f"✓ Direct code: {source_code} → {concept_id}")
            
            return concept_id

        # Strategy 4 Normalized name lookup
        normalized = self.normalize(source_value or source_code)
        if normalized in self.concept_by_name:
            concept_id = self.concept_by_name[normalized].concept_id
            logger.debug(f"✓ Name match: {source_value} → {concept_id}")
            return concept_id

        # No Match
        logger.warning(
            f"❌ Unmapped: {source_code} ({source_value}) - domain={domain_id}, field={source_field}"
        )
        self._record_unmapped_concept(source_code, source_value, domain_id, source_field)
        self.unmapped_count += 1
        
        return None
    
    def _record_unmapped_concept(self, source_code, source_value,domain_id, source_field = None):
        # Track unmapped concept 
        unmapped , created = UnmappedConcept.objects.get_or_create(
            data_source = self.data_source,
            source_code = source_code,
            domain_id = domain_id or 'Other',
            source_value = source_value or "",
            source_field = source_field or "",
            status = 'UNRESOLVED'
        )
        if not created:
            unmapped.occurrence_count += 1
            unmapped.last_seen = timezone.now()
            unmapped.save()
        


    @abstractmethod
    def extract(self):
            # Read Data from sources , subclasses will implement this and populate self.persons_data , self.conditions_data and so on 
            pass
        
    def validate_input(self):
            """Check Data exists before processing"""
            print("\n[VALIDATE] Checking input data...")
            
            if not self.persons_data:
                raise ValueError("No person data to process")

            validation_issues = []
            critical_issues = []
            
            # Person data Validation
            logger.info('Validating persons...')
            
            # Validate person data format
            for person in self.persons_data:
                try:
                    # Required Fields 
                    source_id = person.get('source_id')
                    gender = person.get('gender')
                    year = person.get('year_of_birth')
                    
                    if not source_id:
                        critical_issues.append("Person missing source_id")
                        continue
                    
                    if not gender:
                        critical_issues.append(f"Person {source_id} missing gender")
                        continue
    
                    # Validate date format YYYY-MM-DD
                    if year:
                        if not (1900 <= year <= 2026):
                            validation_issues.append(f"Person {source_id} has invalid year: {year}")

                except Exception as e:
                    critical_issues.append(f"Person validation error : {str(e)}")
            
            # Condition Data Validation
            logger.info("Validation Conditions....")
            for condition in self.conditions_data:
                person_id = condition.get('person_source_id')
                condition_code = condition.get('condition_code')
                condition_date = condition.get('condition_date')
                
                if not condition_code:
                    #soft: resolve concept() will track this as unmapped concept
                    validation_issues.append(f"Condition for {person_id} missing code")
                
                if not condition_date:
                    #hard: a condition with no date can never be linked to TumorProfile diagnosis or any timeline  
                    critical_issues.append(f"Condition for {person_id} missing date")
                
            #Medications Data validation
            logger.info("Validating medications...")
            for med in self.medications_data:
                person_id = med.get('person_source_id')
                drug_code = med.get('drug_code')
                start_date = med.get('drug_start_date')
                
                if not drug_code:
                    validation_issues.append(f"Drug for {person_id} missing code")
                
                if not start_date:
                    critical_issues.append(f"Drug for {person_id} missing start date")
            
            #Measurement Data Validation
            logger.info("Validating measurements...")
            missing_values = 0
            for measurement in self.measurements_data:
                value = measurement.get('value')
                if value is None:
                    missing_values +=1 
            
            if missing_values > 0:
                logger.warning(f" {missing_values} measurements have null values")
            
            #Visit Data validation
            logger.info("Validating visits...")
            for visit in self.visits_data:
                visit_date = visit.get('visit_date')
                if not visit_date:
                    critical_issues.append(f"Visit missing date")
            
            #Tumor profile validation
            logger.info("Validating tumor profiles...")
            for tumor in self.tumor_profiles_data:
                diagnosis_date = tumor.get("diagnosis_date")
                if not diagnosis_date:
                    critical_issues.append(f"Tumor profile missing diagnosis_date")
            
            #Treatment Validation
            logger.info("Validating treatments...")
            for treatment in self.treatment_regimens_data:
                regimen_name = treatment.get("regimen_name")
                start_date = treatment.get("start_date")
                
                if not regimen_name:
                    critical_issues.append("Treatment missing regimen_name")
                
                if not start_date:
                    critical_issues.append("Treatment missing start_date")
            
            #Adverse events validation 
            logger.info('Validating adverse events...')
            for ae in self.adverse_events_data:
                event_name = ae.get("event_name")
                event_date = ae.get("event_date")
                grade = ae.get("grade")
                
                if not event_name:
                    critical_issues.append("AE missing event_name")
                
                if not event_date:
                    critical_issues.append("AE missing event_date")
                    
                if not grade:
                    critical_issues.append("AE missing grade")
                 
                    
                
            # Report validation results
            self.records_processed = (
            len(self.persons_data) +
            len(self.conditions_data) +  
            len(self.medications_data) + 
            len(self.measurements_data) +
            len(self.visits_data) 
            )
            print(f"\n[VALIDATE] Data Quality Report:")
            print(f"  Total OMOP records: {self.records_processed}")
            print(f"  Persons: {len(self.persons_data)}")
            print(f"  Conditions: {len(self.conditions_data)}")
            print(f"  Medications: {len(self.medications_data)}")
            print(f"  Measurements: {len(self.measurements_data)}")
            print(f"  Visits: {len(self.visits_data)}")
            print(f"  Total: {self.records_processed}")
            print(f"  Total Cancer-Specific: {len(self.tumor_profiles_data) + len(self.treatment_regimens_data) + len(self.adverse_events_data)}")
            
            if validation_issues:
                logger.warning(f"\n ⚠️ Found {len(validation_issues)} validation issues:")
                for issue in validation_issues[:10]:  # i will print the first 10
                    logger.warning(f" - {issue}")
                
                if len(validation_issues) > 10:
                    logger.warning(f" ... and {len(validation_issues) - 10 } more issues")
            
            print(f" Validation Issues: {len(validation_issues)}")

            if critical_issues:
                print(f"Validation Issues (CRITICAL): {len(critical_issues)}")
                logger.error(f"\n Found {len(critical_issues)} CRITICAL validation issues:")
                for issue in critical_issues[:10]:
                    logger.error(f" - {issue}")
                if (len(critical_issues) > 10):
                    logger.error(f" ... and {len(critical_issues) - 10} more critical issues")
                
                raise ValueError(
                    f"{len(critical_issues)} critical validation issue(s) found "
                    f"(e.g. missing required dates or identifying fields) -- aborting "
                    f"before load. See logs above for the full list."
                )

        
    @transaction.atomic
    def transform_and_load(self):
            """Transform to OMOP and load to database with optimizations"""
            print("\n[TRANSFORM & LOAD] Converting to OMOP format...") 
            
            try: 
                logger.info("Loading OMOP layer...")
                self._load_persons()
                self._load_conditions()
                self._load_medications()
                self._load_measurements()
                self._load_visits()
                
                logger.info("Loading cancer-specific layer...")
                self._load_tumor_profiles()
                self._load_treatment_regimens()
                self._load_adverse_events()
                
                
                print(f"\n ✅ Successfully loaded {self.records_loaded} records")
                 # FIX: quality gate moved here, still inside @transaction.atomic
                logger.info("PHASE 4: Quality Check")
                if not self.validate_mapping_quality():
                    logger.error("Mapping quality check FAILED - rolling back this ETL run")
                    raise ValueError("Too many unmapped concepts")

            
            except Exception as e:
                logger.exception("ETL failure during transform/load")
                self.records_failed += 1
                raise 
    
    def _load_persons(self):
            """Load Person Data to database""" 
            print("\n [PERSON] Loading Patients...")
            
            
            #Pre fetch: getting all existing person_source_values in one query 
            existing_source_values = set(
                Person.objects.values_list('person_source_value', flat=True)
            ) 
            logger.debug(f"Found {len(existing_source_values)} existing persons in DB")
            
            persons_to_create = []
            created = 0
            
            for person_dict in self.persons_data:
                try:
                    source_id = person_dict.get('source_id')
                    
                    # check for duplicates. this is faster than making a query 
                    if source_id in existing_source_values:
                        logger.warning(f"Person {source_id} already exists, skipping..."  )
                        self.records_skipped +=1
                        continue
                
                    # Get Gender Concept 
                    gender = person_dict.get('gender')
                    gender_concept_id = self.resolve_concept(
                        gender,
                        source_value = gender,
                        domain_id = 'Gender',
                        source_field = 'gender',
                        )
                    
                    if not gender_concept_id:
                        self.records_failed +=1 
                        continue
                    
                    gender_concept = self.concept_by_id.get(gender_concept_id)
                    if not gender_concept:
                        self.records_failed +=1
                        continue
                    
                    # Create person
                    person = Person(
                        person_source_value = source_id,
                        gender_concept = gender_concept,
                        year_of_birth = person_dict.get('year_of_birth'),
                        month_of_birth = person_dict.get('month_of_birth',1),
                        day_of_birth = person_dict.get('day_of_birth',1), 
                    )
                    persons_to_create.append(person)
                    
                except Exception as e:
                    logger.error(f"⚠️ Error processing person {source_id}: {str(e)}")
                    self.records_failed += 1
            if persons_to_create:
                Person.objects.bulk_create(persons_to_create, batch_size=1000)
                created = len(persons_to_create)
                self.records_loaded += created

            print(f" ✅ Loaded {created} persons")
        
    def _load_visits(self):
            print("\n [VISIT] Loading Vists Data ...")
            
            batch_persons_ids = [v.get("person_source_id") for v in self.visits_data]
            
            #pre fetch : only persons in this batch 
            persons_map = {p.person_source_value: p for p in Person.objects.filter(
                person_source_value__in = batch_persons_ids
            )}
            
            existing_visit_keys = set(
                VisitOccurrence.objects.filter(
                    person__person_source_value__in = batch_persons_ids
                ).values_list('person_id','visit_concept_id','visit_start_date')
            ) 
            
            visits_to_create = []
            created = 0
            
            for visit_dict in self.visits_data:
                try:
                    person_id = visit_dict.get('person_source_id')
                    person = persons_map.get(person_id)
                    
                    if not person:
                        print(f"Person {person_id} not found")
                        self.records_failed +=1
                        continue
                  
                    # Get visit concept 
                    visit_type = visit_dict.get('visit_type', 'Outpatient')
                    visit_concept_id = self.resolve_concept(
                        visit_type,
                        source_value = visit_type,
                        domain_id = 'Visit',
                        source_field = 'visit_type'
                    )
                    if not visit_concept_id:
                        print(f" visit concept id not found")
                        self.records_failed += 1
                        continue
                    
                    visit_concept = self.concept_by_id.get(visit_concept_id)
                    if not visit_concept:
                        print(f" visit concept not found")
                        self.records_failed += 1
                        continue
                    
                    visit_date = visit_dict.get('visit_date')
                    
                    natural_key = (person.person_id,visit_concept.concept_id, visit_date)
                    if natural_key in existing_visit_keys:
                        logger.debug(f'Visit for {person_id} on {visit_date} already exists, skipping...')
                        self.records_skipped +=1
                        continue
                    
                    visit = VisitOccurrence(
                        person = person,
                        visit_concept = visit_concept,
                        visit_start_date = visit_date,
                        visit_source_value = visit_type,
                    )
                    visits_to_create.append(visit)
                    existing_visit_keys.add(natural_key)
                    
                except Exception as e:
                    logger.error(f"Error processing visit: {str(e)}")
                    self.records_failed += 1
            
            if visits_to_create:
                VisitOccurrence.objects.bulk_create(visits_to_create,batch_size=3000)
                created = len(visits_to_create)
                self.records_loaded += created
                
                
                    
            print(f" ✅ Loaded {created} visits (batch={len(visits_to_create)} ")   
        
    def _load_conditions(self):
            print("\n [CONDITION] loading conditions ...")
            
            batch_person_ids = [c.get('person_source_id') for c in self.conditions_data] 
            
            #pre-fetch : Only persons in this batch 
            
            persons_map = {p.person_source_value: p for p in Person.objects.filter(
                person_source_value__in = batch_person_ids
            )}
            
            existing_condition_keys = set(
                ConditionOccurrence.objects.filter(
                    person__person_source_value__in = batch_person_ids 
                ).values_list('person_id', 'condition_concept_id','condition_start_date')
            )
            
            conditions_to_create = []
            created = 0 
            
            for condition_dict in self.conditions_data:
                try:
                    # Get Person
                    person_id = condition_dict.get('person_source_id')
                    person = persons_map.get(person_id)

                    if not person:
                        logger.warning(f"Person {person_id} not found")
                        self.records_failed += 1
                        continue
                    
                    # Resolve condition concept
                    condition_code = condition_dict.get('condition_code')
                    condition_name = condition_dict.get('condition_name')
                    
                    condition_concept_id = self.resolve_concept(
                        condition_code,
                        source_value = condition_name,
                        domain_id = 'Condition',
                        source_field = 'cancer_type_code'
                    )
                    if not condition_concept_id:
                        self.records_failed +=1
                        continue
                    
                    condition_concept = self.concept_by_id.get(condition_concept_id)
                    if not condition_concept:
                        self.records_failed +=1 
                        continue
                    
                    condition_date = condition_dict.get('condition_date')
                    natural_key = (person.person_id,condition_concept.concept_id,condition_date)
                    
                    if natural_key in existing_condition_keys:
                        logger.debug(f'Condition for {person_id} on {condition_date} already exists, skipping...')
                        self.records_skipped +=1
                        continue
                                        
                    condition = ConditionOccurrence(
                        person = person,
                        condition_concept = condition_concept,
                        condition_start_date =condition_date,
                        condition_source_value = condition_name,
                    )
                    conditions_to_create.append(condition)
                    existing_condition_keys.add(natural_key)
                
                except Exception as e: 
                    logger.error(f" ⚠️ Error processing condition: {str(e)}")
                    self.records_failed += 1
            
            if conditions_to_create:
                ConditionOccurrence.objects.bulk_create(conditions_to_create, batch_size=1000)
                created = len(conditions_to_create)
                self.records_loaded += created
        
                
            print(f" ✅ Loaded {created} conditions")
        
    def _load_medications(self):
        print("\n [MEDICATION] Loading medications ...")
        
        
        batch_person_ids = [d.get('person_source_id') for d in self.medications_data]
        
        #Pre fetch: only persons in this batch 
        
        persons_map = {p.person_source_value: p for p in Person.objects.filter(
            person_source_value__in =  batch_person_ids
        )}
        
        existing_drug_keys = set(
            DrugExposure.objects.filter(
                person__person_source_value__in = batch_person_ids
            ).values_list('person_id', 'drug_concept_id','drug_exposure_start_date')
        )
        
        drugs_to_create = []
        created = 0
        
        for drug_dict in self.medications_data:
            try:
                person_id = drug_dict.get('person_source_id')
                person = persons_map.get(person_id)
                
                if not person:
                    logger.warning(f"Person {person_id} not found")
                    self.records_failed += 1
                    continue
                
                # get drug concept
                drug_code = drug_dict.get('drug_code')
                drug_name = drug_dict.get('drug_name')
                
                drug_concept_id = self.resolve_concept(
                    drug_code,
                    source_value= drug_name,
                    domain_id='Drug',
                    source_field = 'drug_name'
                )
                    
                if not drug_concept_id :
                    print(f"⚠️ Drug {drug_name} ({drug_code}) not mapped, skipping...")
                    self.records_failed +=1 
                    continue
                
                drug_concept = self.concept_by_id.get(drug_concept_id)
                if not drug_concept:
                    print(f"⚠️ Drug {drug_name} ({drug_code}) not mapped, skipping...")
                    self.records_failed +=1 
                    continue
                
                drug_start_date = drug_dict.get('drug_start_date')
                natural_key = (person.person_id,drug_concept.concept_id,drug_start_date)
                
                if natural_key in existing_drug_keys:
                    logger.debug(f"Drug {drug_name} for {person_id} on {drug_start_date} already exists, skipping...")
                    self.records_skipped +=1
                    continue 
                                
                # Create Drug Exposure
                drug = DrugExposure(
                    person = person,
                    drug_concept = drug_concept,
                    drug_exposure_start_date = drug_start_date,
                    drug_exposure_end_date = drug_dict.get('drug_end_date'),
                    quantity = drug_dict.get('quantity'),
                    drug_source_value = drug_name,
                ) 
                drugs_to_create.append(drug)
                existing_drug_keys.add(natural_key)
                
            except Exception as e:
                logger.error(f"Error processing drug: {str(e)}")
                self.records_failed += 1
        
        if drugs_to_create:
            DrugExposure.objects.bulk_create(drugs_to_create,batch_size=1000)
            created = len(drugs_to_create)
            self.records_loaded += created 
    
        print(f" ✅ Loaded {created} medications")
        
    def _load_measurements(self):
        print("\n [MEASUREMENTS] Loading Measurements...")
        
        batch_person_ids = [m.get('person_source_id') for m in self.measurements_data]
        
         
        #pre fetch: only persons in this batch  
        persons_map = {p.person_source_value: p for p in Person.objects.filter(
            person_source_value__in = batch_person_ids
        )} 
        
        existing_measurement_keys = set(
            Measurement.objects.filter(
                person__person_source_value__in = batch_person_ids
            ).values_list('person_id', 'measurement_concept_id','measurement_date')
        )
        
        measurements_to_create = []    
        created = 0
        
        for measurement_dict in self.measurements_data:
            try:
                person_id = measurement_dict.get('person_source_id')
                person = persons_map.get(person_id)
                
                if not person:
                    logger.warning(f"Person {person_id} not found")
                    self.records_failed += 1
                    continue
                
                # get measurement concept
                measurement_code = measurement_dict.get('measurement_code')
                measurement_name = measurement_dict.get('measurement_name')
                
                measurement_concept_id = self.resolve_concept(
                    measurement_code,
                    source_value = measurement_name,
                    domain_id = 'Measurement',
                    source_field = 'lab_code'
                )
                
                if not measurement_concept_id:
                    print(f" ⚠️ Measurement {measurement_name} not mapped, skipping")
                    self.records_failed +=1 
                    continue
                
                measurement_concept = self.concept_by_id.get(measurement_concept_id)
                
                if not measurement_concept:
                    print(f" ⚠️ Measurement {measurement_name} not mapped, skipping")
                    self.records_failed += 1
                    continue 
               
                measurement_date = measurement_dict.get('measurement_date')
                value = measurement_dict.get('value')
                
                natural_key = (person.person_id, measurement_concept.concept_id, measurement_date)
                
                if natural_key in existing_measurement_keys:
                    logger.debug(f"Measurement {measurement_name} for {person_id} on {measurement_date} already exists skipping...")
                    self.records_skipped +=1
                    continue
               
                # Create Measuretment 
                measurement = Measurement(
                    person = person,
                    measurement_concept = measurement_concept,
                    measurement_date =  measurement_date ,
                    value_as_number = value,
                    unit_source_value = measurement_dict.get('unit', 'Unknown'),
                    measurement_source_value = measurement_name
                )
                measurements_to_create.append(measurement)
                existing_measurement_keys.add(natural_key)
        
            except Exception as e:
                logger.error(f"Error processing measurement: {str(e)}")
                self.records_failed +=1
        
        if measurements_to_create:
            Measurement.objects.bulk_create(measurements_to_create,batch_size=1000)
            created = len(measurements_to_create)
            self.records_loaded += created
            
        print(f" ✅ Loaded {created} measurements ")
     
     
    def _load_tumor_profiles(self):
        # Load tumor profiles from diagnosis data 
        # Links OMOP ConditionOccurrence to cancer-specific staging
        print("[TUMOR] Loading Tumor Profiles ... (Cancer-Specific)")
        
        # pre fetch: only person IDs in this batch
        batch_person_ids = set(
            t.get('person_source_id') for t in self.tumor_profiles_data
        )
        
        persons_map = {p.person_source_value: p for p in Person.objects.filter(
            person_source_value__in = batch_person_ids
        )}
        
        # pre fetch: getting all existing tumor profiles only for this batch
        existing_tumor_person_ids = set(
            TumorProfile.objects.filter(
                person__person_source_value__in = batch_person_ids
            ).values_list('person_id', flat = True)
        )
        logger.debug(f"Found {len(existing_tumor_person_ids)} existing tumor profiles")
        
        
        conditions_map = {
            (c.person_id, c.condition_start_date) : c
            for c in ConditionOccurrence.objects.filter(
                person__person_source_value__in = batch_person_ids
            )
        }        
        
        tumor_profiles_to_create = []
        created = 0;
        
        for tumor_dict in self.tumor_profiles_data:
            try:
                person_id = tumor_dict.get('person_source_id')
                person = persons_map.get(person_id)
                
                if not person:
                    self.records_failed +=1
                    continue
                
                # check for duplicates in the pre fetched set 
                if person.person_id in existing_tumor_person_ids:
                    logger.debug(f"Tumor profile for {person_id} already exists")
                    self.records_skipped += 1
                    continue
                
                
                
                #link to OMOP ConditionOccurrence if available
                diagnosis_date = tumor_dict.get('diagnosis_date')
                
                if not diagnosis_date:
                    logger.warning(f"No diagnosis_date for {person_id}, skipping tumor profile")
                    self.records_failed += 1
                    continue
                
                primary_diagnosis = conditions_map.get((person.person_id, diagnosis_date))
                
                tumor_profile = TumorProfile(
                    person=person,
                    primary_diagnosis = primary_diagnosis,
                    diagnosis_date=diagnosis_date,
                    stage = tumor_dict.get('stage'),
                    histology = tumor_dict.get('histology'),
                    mutation_status = tumor_dict.get('mutation_status'),
                )
                tumor_profiles_to_create.append(tumor_profile)
                
                
            except Exception as e:
                logger.error(f"Error processing tumor profile: {str(e)}")
                self.records_failed += 1
            
        if tumor_profiles_to_create:
            TumorProfile.objects.bulk_create(tumor_profiles_to_create,batch_size=1000)
            created = len(tumor_profiles_to_create)
            self.records_loaded += created
        
        logger.info(f"✅ Loaded {created} tumor profiles")
    
    def _load_treatment_regimens(self):
        # Links to Tumor Profile and track outcomes
        logger.info('Loading treatment regimens (Cancer-Specific Models)')
        
        #pre fetch: only persons in this batch
        
        batch_person_ids = set(
            r.get('person_source_id') for r in self.treatment_regimens_data
        )
        
        persons_map = {p.person_source_value : p for p in Person.objects.filter(
            person_source_value__in = batch_person_ids 
        )}
        
        #pre fetch tumor profiles only for this batch
        
        tumor_map = {tp.person_id : tp for tp in TumorProfile.objects.filter(
            person__person_source_value__in  = batch_person_ids
        )}
        
        existing_regimen_keys = set(
            TreatmentRegimen.objects.filter(
                person__person_source_value__in = batch_person_ids
            ).values_list('person_id', 'regimen_name','start_date')
        )
        
        regimens_to_create = []
        created = 0
        
        for regimen_dict in self.treatment_regimens_data:
            try:
                person_id = regimen_dict.get('person_source_id')
                person = persons_map.get(person_id)
                
                if not person:
                    self.records_failed += 1
                    continue
                
                tumor_profile = tumor_map.get(person.person_id)
                
                if not tumor_profile:
                    logger.warning(f"No tumor profile for {person_id}, creating regimen anyway")
                
                
                regimen_name = regimen_dict.get('regimen_name')
                start_date = regimen_dict.get('start_date')
                
                if not regimen_name or not start_date:
                    logger.warning(f"Missing regimen_name or start_date for {person_id}")
                    self.records_failed += 1
                    continue
                
                natural_key = (person.person_id,regimen_name,start_date)
                if natural_key in existing_regimen_keys:
                    logger.debug(f"Regimen '{regimen_name} for {person_id} already exists, skipping...")
                    self.records_skipped +=1
                    continue
                
                regimen = TreatmentRegimen(
                    person = person,
                    tumor_profile= tumor_profile,
                    regimen_name = regimen_name,
                    start_date = start_date,
                    end_date = regimen_dict.get('end_date'),
                    best_response = regimen_dict.get('best_response'),
                    completed_cycles = regimen_dict.get('completed_cycles',0),
                )
                regimens_to_create.append(regimen)
                existing_regimen_keys.add(natural_key)
            
            except Exception as e:
                logger.error(f"Error processing treatment regimen: {str(e)}")
                self.records_failed += 1
        
        if regimens_to_create:
            TreatmentRegimen.objects.bulk_create(regimens_to_create,batch_size=1000)
            created = len(regimens_to_create)
            self.records_loaded += created 
        logger.info(f"✅ Loaded {created} treatment regimens")
    
    
    def _load_adverse_events(self):
        # Load Side effects and Link it to Treatment Regimen for tracking 

        logger.info(f" ✅ Loading adverse events (cancer-specific)...")
        
        #pre fetch : only persons in this batch 
        batch_person_ids = set(
            e.get("person_source_id") for e in self.adverse_events_data
        )
        

        persons_map = {p.person_source_value: p for p in Person.objects.filter(
            person_source_value__in = batch_person_ids
        )}
        
        #pre fetch : treatment regimens only for this batch
        all_regimens = list(TreatmentRegimen.objects.filter(
            person__person_source_value__in = batch_person_ids
        ))
        regimen_by_person_and_start = {
            (r.person_id,r.start_date): r for r in all_regimens
        }
        regimens_by_person = defaultdict(list)
        for r in all_regimens:
            regimens_by_person[r.person_id].append(r)
        for regs in regimens_by_person.values():
            regs.sort(key=lambda r: r.start_date)  # ascending, oldest first
        
        
        existing_ae_keys = set(
            AdverseEvent.objects.filter(
                person__person_source_value__in = batch_person_ids
            ).values_list('person_id','event_name','event_date')
        )

        adverse_events_to_create = []
        created = 0
        
        for event_dict in self.adverse_events_data:
            try:
                person_id = event_dict.get('person_source_id')
                person = persons_map.get(person_id)
                
                if not person:
                    self.records_failed += 1
                    continue
                
                
                event_name = event_dict.get('event_name')
                event_date = event_dict.get('event_date')
                grade = event_dict.get('grade')
            
                if not event_name or not event_date or not grade:
                    logger.warning(f"Missing event data for {person_id}")
                    self.records_failed += 1
                    continue
                
                natural_key = (person.person_id, event_name,event_date)
                if natural_key in existing_ae_keys:
                    logger.debug(f"AE {event_name} for {person_id} on {event_date} already exists, skipping...")
                    self.records_skipped +=1
                    continue
                                
                regimen = None
                
                # Strategy 1: Try exact match with treatment_start_date
                treatment_start_date = event_dict.get('treatment_start_date')
                regimen = regimen_by_person_and_start.get((person.person_id, treatment_start_date))
                
                #Strategy 2: AE occurred during the regimen's date range (in-memory,
                # most recent candidate first since the list is sorted ascending)
                if not regimen:
                    candidates = regimens_by_person.get(person.person_id, [])
                    for candidate in reversed(candidates):
                        started_before_ae = candidate.start_date <= event_date
                        still_ongoing_or_ended_after = (
                            candidate.end_date is None or candidate.end_date >= event_date
                        )
                        if started_before_ae and still_ongoing_or_ended_after:
                            regimen = candidate
                            logger.debug(
                                f"AE matched to regimen by date range: "
                                f"{candidate.start_date} to {candidate.end_date or 'ongoing'}"
                            )
                            break
                        
            
                # Strategy 3: fall back to the person's most recent regimen (in-memory)
                if not regimen:
                    candidates = regimens_by_person.get(person.person_id, [])
                    if candidates:
                        regimen = candidates[-1]  # sorted ascending, so last = most recent
                        logger.warning(
                            f"AE {event_name} matched to most recent regimen "
                            f"(no exact date match). Date: {event_date} vs Treatment: {regimen.start_date}"
                        )
                    else:
                        logger.warning(
                        f"❌ No treatment regimen found for {person_id}, skipping AE"
                        )
                        self.records_failed += 1
                        continue

                event = AdverseEvent(
                    person=person,
                    treatment_regimen= regimen,
                    event_name = event_name,
                    event_date = event_date,
                    grade = grade,
                    )
                adverse_events_to_create.append(event)
                existing_ae_keys.add(natural_key)
                
            except Exception as e:
                logger.error(f"Error processing adverse event: {str(e)}")
                self.records_failed += 1
        if adverse_events_to_create:
            AdverseEvent.objects.bulk_create(adverse_events_to_create,batch_size=1000)
            created = len(adverse_events_to_create)
            self.records_loaded +=  created
            
        logger.info(f"✅ Loaded {created} adverse events")
        
    
    def log_etl_run(self):
            
            duration = (self.end_time - self.start_time).total_seconds()
            
            status = 'SUCCESS' if self.records_failed == 0 else 'PARTIAL'
            
            etl_log = ETLLog(
                source_name = self.data_source_name,
                records_processed = self.records_processed,
                records_loaded = self.records_loaded,
                records_failed = self.records_failed,
                records_skipped = self.records_skipped,
                duration_seconds = int(duration),
                status = status
            )
            etl_log.save()
            
            print(f"\n ETLLoged {status}")
    
    def get_unmapped_summary(self):
        # Get summary of unmapped concepts
        unmapped = UnmappedConcept.objects.filter(
            data_source = self.data_source,
            status = 'UNRESOLVED'
        ).order_by('-occurrence_count')
        
        critical = unmapped.filter(occurrence_count__gte=5)
        
        return {
            'total_unmapped' : unmapped.count(),
            'critical_unmapped' : critical.count(),
            'unmapped_concepts' : [
                {
                    'source_value': u.source_value,
                    'source_field': u.source_field,
                    'domain' : u.domain_id,
                    'occurrences' : u.occurrence_count,
                    'is_critical' : u.occurrence_count >= 5 
                }
                for u in unmapped[:10]
            ]
        }
    
    def validate_mapping_quality(self):
        # Validate that unmapping % is acceptable
        
        if self.records_processed == 0:
            return True
        
        unmapped_percent = (self.unmapped_count / self.records_processed) * 100
        max_allowed = self.data_source.max_unmapped_percent
        
        if unmapped_percent > max_allowed :
            logger.error(
                f"⚠️  Data quality FAILED: {unmapped_percent:.1f}% unmapped "
                f"(max allowed: {max_allowed}%)"
            )
            return False
        logger.info(
            f"✅ Data quality OK: {unmapped_percent:.1f}% unmapped "
            f"(max allowed: {max_allowed}%)"
        )
        return True
        
    def get_quality_report(self):
            """Generate comprehensive quality report"""
            
            unmapped_summary = self.get_unmapped_summary()
            
            return{
                'source' : self.data_source.display_name,
                'records_processed' : self.records_processed,
                'records_loaded' : self.records_loaded,
                'records_failed' : self.records_failed,
                'records_skipped' : self.records_skipped,
                'success_rate' : (
                    (self.records_loaded / self.records_processed * 100)
                    if self.records_processed > 0 else 0
                ),
                'unmapped_concepts' : unmapped_summary['total_unmapped'],
                'critical_unmapped' : unmapped_summary['critical_unmapped'],
                'top_unmapped' : unmapped_summary['unmapped_concepts'],
                'mapping_quality_percent' : (
                    100 - ((self.unmapped_count / self.records_processed * 100)
                    if self.records_processed > 0 else 0)  
                ),
                'status' : 'SUCCESS' if  self.records_failed == 0 else 'PARTIAL'
            }
        
          
    def run(self):
            # Execute complete ETL Pipeline 
            print("\n" + "="*100)
            print(f" {self.data_source.display_name.upper()} => OMOP ETL PIPELINE" )
            print("="*100)
            
            self.start_time = timezone.now()
            
            try:
                # step 1 Extract
                print(f"\n [EXTRACT] Reading {self.data_source.display_name} data ...") 
                self.extract()
                print(f"  ✅ Extracted {len(self.persons_data)} persons")
                print(f"  ✅ Extracted {len(self.conditions_data)} conditions")
                print(f"  ✅ Extracted {len(self.medications_data)} medications")
                print(f"  ✅ Extracted {len(self.measurements_data)} measurements")
                print(f"  ✅ Extracted {len(self.visits_data)} visits")
                print(f"  ✅ Extracted {len(self.treatment_regimens_data)} treatment regimens")
                print(f"  ✅ Extracted {len(self.adverse_events_data)} adverse events")
                
                # step 2 validate
                logger.info("PHASE 2: Validate")
                print(f"[VALIDATE] Checking input data...")
                self.validate_input()
                print(f"  ✅ Data validation passed")
                
                #step 3 transform & load
                logger.info("PHASE 3: Transform & Load")
                print(f"[TRANSFORM] Converting to OMOP + Cancer-specific format...")
                self.transform_and_load()

                self.end_time = timezone.now()
                self.log_etl_run()
                
                report = self.get_quality_report()
                
                # Print summary
                print("\n" + "="*80)
                print(f"✅ ETL COMPLETED: {report['status']}")
                print("="*80)
            
                print(f"\nSTATISTICS:")
                print(f"\nRecords Loaded:       {report['records_loaded']}/{report['records_processed']}")
                print(f"\nSuccess Rate:         {report['success_rate']:.1f}%")
                print(f"\nMapping Quality:      {report['mapping_quality_percent']:.1f}%")
                print(f"\nFailed Records:       {report['records_failed']}")
                print(f"\nSkipped (duplicates): {report['records_skipped']}")
                print(f"\nUnmapped Concepts:    {report['unmapped_concepts']}")
            
                if report['critical_unmapped'] > 0:
                    print(f"\n  🔴 CRITICAL: {report['critical_unmapped']} unmapped with high occurrence")
                    print(f"     Run: python manage.py show_unmapped_concepts --data-source {self.data_source_name}")
            
                if report['top_unmapped']:
                    print(f"\n  TOP UNMAPPED VALUES:")
                    for unmapped in report['top_unmapped']:
                        marker = "🔴" if unmapped['is_critical'] else "🟡"
                        print(
                            f"    {marker} {unmapped['source_value']:<30} "
                            f"[{unmapped['domain']:<15}] {unmapped['occurrences']}x"
                        )
            
                duration = (self.end_time - self.start_time).total_seconds()
                print(f"\n  Duration: {duration:.1f}s")
                print("="*80 + "\n")
            
                return report
        
            except Exception as e:
                self.end_time = timezone.now()
                logger.exception("ETL FAILED")
            
                print("\n" + "="*80)
                print(f"❌ ETL FAILED")
                print(f"Error: {str(e)}")
                print(f"Records Loaded: {self.records_loaded}")
                print(f"Records Failed: {self.records_failed}")
                print("="*80 + "\n")
            
                raise
            
                                                    
                    
                