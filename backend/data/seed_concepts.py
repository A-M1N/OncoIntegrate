# backend/data/seed_concepts.py

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from data.models import Concept, DataSource, ConceptMapping

def seed_concepts():
    """
    Seed OMOP Concepts with STANDARD OMOP concept_ids and codes
    
    Key difference from before:
    - concept_code now stores OMOP's OWN standard codes (SNOMED, LOINC, RxNorm IDs)
    - NOT the source system codes (ICD-10, drug names, etc.)
    - Source codes are mapped via ConceptMapping table
    """
    
    print("\n" + "="*80)
    print("SEEDING OMOP CONCEPT TABLE")
    print("="*80 + "\n")
    
    # ============================================================
    # GENDER CONCEPTS
    # ============================================================
    gender_concepts = [
        {
            'concept_id': 8507,
            'concept_name': 'Female',
            'vocabulary_id': 'GENDER',
            'concept_code': 'F',
            'domain_id': 'Gender'
        },
        {
            'concept_id': 8508,
            'concept_name': 'Male',
            'vocabulary_id': 'GENDER',
            'concept_code': 'M',
            'domain_id': 'Gender'
        },
    ]
    
    # ============================================================
    # CONDITION CONCEPTS (SNOMED - OMOP standard for conditions)
    # ============================================================
    condition_concepts = [
        {
            'concept_id': 201826,
            'concept_name': 'Malignant neoplasm of lung',
            'vocabulary_id': 'SNOMED',
            'concept_code': '162573006',  # SNOMED code (OMOP standard)
            'domain_id': 'Condition'
        },
        {
            'concept_id': 201827,
            'concept_name': 'Malignant neoplasm of breast',
            'vocabulary_id': 'SNOMED',
            'concept_code': '126618006',
            'domain_id': 'Condition'
        },
        {
            'concept_id': 440379,
            'concept_name': 'Anemia',
            'vocabulary_id': 'SNOMED',
            'concept_code': '271737000',
            'domain_id': 'Condition'
        },
        {
            'concept_id': 201254,
            'concept_name': 'Type 2 Diabetes Mellitus',
            'vocabulary_id': 'SNOMED',
            'concept_code': '44054006',
            'domain_id': 'Condition'
        },
    ]
    
    # ============================================================
    # DRUG CONCEPTS (RxNorm - OMOP standard for drugs)
    # ============================================================
    drug_concepts = [
        {
            'concept_id': 1708147,
            'concept_name': 'Pemetrexed',
            'vocabulary_id': 'RxNorm',
            'concept_code': '1708147',  # RxNorm ID (OMOP standard)
            'domain_id': 'Drug'
        },
        {
            'concept_id': 945638,
            'concept_name': 'Carboplatin',
            'vocabulary_id': 'RxNorm',
            'concept_code': '945638',
            'domain_id': 'Drug'
        },
        {
            'concept_id': 1585838,
            'concept_name': 'Nivolumab',
            'vocabulary_id': 'RxNorm',
            'concept_code': '1585838',
            'domain_id': 'Drug'
        },
        {
            'concept_id': 35894,
            'concept_name': 'Pembrolizumab',
            'vocabulary_id': 'RxNorm',
            'concept_code': '35894',
            'domain_id': 'Drug'
        },
        {
            'concept_id': 904542,
            'concept_name': 'Metformin',
            'vocabulary_id': 'RxNorm',
            'concept_code': '904542',
            'domain_id': 'Drug'
        },
    ]
    
    # ============================================================
    # VISIT CONCEPTS
    # ============================================================
    visit_concepts = [
        {
            'concept_id': 9200,
            'concept_name': 'Inpatient Visit',
            'vocabulary_id': 'Visit',
            'concept_code': '9200',
            'domain_id': 'Visit'
        },
        {
            'concept_id': 9201,
            'concept_name': 'Outpatient Visit',
            'vocabulary_id': 'Visit',
            'concept_code': '9201',
            'domain_id': 'Visit'
        },
        {
            'concept_id': 9202,
            'concept_name': 'Baseline Visit',
            'vocabulary_id': 'Visit',
            'concept_code': '9202',
            'domain_id': 'Visit'
        },
        {
            'concept_id': 9203,
            'concept_name': 'Cycle Treatment Visit',
            'vocabulary_id': 'Visit',
            'concept_code': '9203',
            'domain_id': 'Visit'
        },
    ]
    
    # ============================================================
    # MEASUREMENT CONCEPTS (LOINC - OMOP standard for labs)
    # ============================================================
    measurement_concepts = [
        {
            'concept_id': 3000963,
            'concept_name': 'Creatinine',
            'vocabulary_id': 'LOINC',
            'concept_code': '2160-0',  # LOINC code (OMOP standard)
            'domain_id': 'Measurement'
        },
        {
            'concept_id': 3006924,
            'concept_name': 'Hemoglobin',
            'vocabulary_id': 'LOINC',
            'concept_code': '718-7',
            'domain_id': 'Measurement'
        },
        {
            'concept_id': 3007070,
            'concept_name': 'Platelet count',
            'vocabulary_id': 'LOINC',
            'concept_code': '777-3',
            'domain_id': 'Measurement'
        },
        {
            'concept_id': 3012888,
            'concept_name': 'White blood cell count',
            'vocabulary_id': 'LOINC',
            'concept_code': '6690-2',
            'domain_id': 'Measurement'
        },
        {
            'concept_id': 3025315,
            'concept_name': 'Bilirubin',
            'vocabulary_id': 'LOINC',
            'concept_code': '1975-2',
            'domain_id': 'Measurement'
        },
    ]
    
    # Combine all
    all_concepts = (
        gender_concepts + condition_concepts + 
        drug_concepts + visit_concepts + measurement_concepts
    )
    
    created_count = 0
    updated_count = 0
    
    for concept_data in all_concepts:
        concept, was_created = Concept.objects.update_or_create(
            concept_id=concept_data['concept_id'],
            defaults={
                'concept_name': concept_data['concept_name'],
                'vocabulary_id': concept_data['vocabulary_id'],
                'domain_id': concept_data['domain_id'],
                'concept_code': concept_data['concept_code'],
            }
        )
        
        if was_created:
            created_count += 1
            print(f"✅ Created: {concept.concept_name} ({concept.vocabulary_id})")
        else:
            updated_count += 1
    
    print(f"\n✅ CONCEPTS SEEDED")
    print(f"   Created: {created_count}")
    print(f"   Updated: {updated_count}")
    print(f"   Total: {created_count + updated_count}\n")


def seed_data_sources():
    """Create DataSource registry"""
    
    print("="*80)
    print("SEEDING DATA SOURCE REGISTRY")
    print("="*80 + "\n")
    
    sources = [
        {
            'name': 'REDCAP',
            'display_name': 'REDCap eCRF',
            'source_type': 'JSON',
            'parser_class': 'data.etl.etl_redcap.RedcapETL',
            "connection_config": {
                "path": "./datasets/mock_redcap_data"
            },
            'is_active': True,
        },
        {
            'name': 'HL7',
            'display_name': 'HL7 v2.5 ADT Feed',
            'source_type': 'HL7',
            'parser_class': 'etl.hl7_etl.HL7ETL',
            'is_active': False,
        },
        {
            'name': 'FHIR_API',
            'display_name': 'FHIR-compliant Hospital API',
            'source_type': 'FHIR',
            'parser_class': 'etl.fhir_etl.FHIRETLAdapter',
            'is_active': False,
        },
    ]
    
    created_count = 0
    for source in sources:
        ds, was_created = DataSource.objects.get_or_create(
            name=source['name'],
            defaults={
                'display_name': source['display_name'],
                'source_type': source['source_type'],
                'parser_class': source['parser_class'],
                'is_active': source['is_active'],
                'min_mapping_confidence': 0.9,
                'max_unmapped_percent': 10.0,
            }
        )
        
        if was_created:
            created_count += 1
            print(f"✅ Created DataSource: {source['name']}")
    
    print(f"\n✅ DATA SOURCES SEEDED: {created_count}\n")


def seed_concept_mappings():
    """
    Map REDCap source codes to OMOP Concepts
    
    This is where the MAGIC happens:
    - REDCap sends "C34.1" → Maps to concept_id 201826 (Lung Cancer)
    - Different source could send "0344001" → Also maps to 201826
    - Same clinical concept, different source codes!
    """
    
    print("="*80)
    print("SEEDING CONCEPT MAPPINGS (REDCap → OMOP)")
    print("="*80 + "\n")
    
    print("Mapping REDCap diagnosis codes (ICD-10) to OMOP concepts...")
    
    try:
        redcap = DataSource.objects.get(name='REDCAP')
    except DataSource.DoesNotExist:
        print("❌ ERROR: DataSource 'REDCAP' not found. Run seed_data_sources() first!")
        return
    
    mappings = [
        # ============================================================
        # DIAGNOSES: ICD-10 codes → SNOMED concepts
        # ============================================================
        {
            'data_source': 'REDCAP',
            'source_code': 'C34.1',
            'source_value': 'Upper Lobe Lung Cancer',
            'source_field': 'cancer_type_code',
            'target_concept_id': 201826,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'ICD-10 C34.1 → SNOMED Malignant neoplasm of lung'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'C34.9',
            'source_value': 'Lung Cancer',
            'source_field': 'cancer_type_code',
            'target_concept_id': 201826,
            'mapping_type': 'PARENT',
            'confidence_score': 0.95,
            'notes': 'ICD-10 C34.9 (unspecified) → SNOMED Lung Cancer'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'C50.9',
            'source_value': 'Breast Cancer',
            'source_field': 'cancer_type_code',
            'target_concept_id': 201827,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'ICD-10 C50.9 → SNOMED Breast Cancer'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'D64.9',
            'source_value': 'Anemia',
            'source_field': 'cancer_type_code',
            'target_concept_id': 440379,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'ICD-10 D64.9 → SNOMED Anemia'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'E11.9',
            'source_value': 'Type 2 Diabetes',
            'source_field': 'cancer_type_code',
            'target_concept_id': 201254,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'ICD-10 E11.9 → SNOMED Type 2 Diabetes'
        },
        
        # ============================================================
        # DRUGS: Drug names → RxNorm concepts
        # ============================================================
        {
            'data_source': 'REDCAP',
            'source_code': 'pembrolizumab',
            'source_value': 'Pembrolizumab',
            'source_field': 'drug_name',
            'target_concept_id': 35894,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'REDCap drug name → RxNorm Pembrolizumab'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Pembrolizumab',  # Also handle capitalized
            'source_value': 'Pembrolizumab',
            'source_field': 'drug_name',
            'target_concept_id': 35894,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'Alternative capitalization'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'nivolumab',
            'source_value': 'Nivolumab',
            'source_field': 'drug_name',
            'target_concept_id': 1585838,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'REDCap drug name → RxNorm Nivolumab'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Nivolumab',
            'source_value': 'Nivolumab',
            'source_field': 'drug_name',
            'target_concept_id': 1585838,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'Alternative capitalization'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'pemetrexed',
            'source_value': 'Pemetrexed',
            'source_field': 'drug_name',
            'target_concept_id': 1708147,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'REDCap drug name → RxNorm Pemetrexed'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Pemetrexed',
            'source_value': 'Pemetrexed',
            'source_field': 'drug_name',
            'target_concept_id': 1708147,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'Alternative capitalization'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'carboplatin',
            'source_value': 'Carboplatin',
            'source_field': 'drug_name',
            'target_concept_id': 945638,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'REDCap drug name → RxNorm Carboplatin'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Carboplatin',
            'source_value': 'Carboplatin',
            'source_field': 'drug_name',
            'target_concept_id': 945638,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'Alternative capitalization'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'metformin',
            'source_value': 'Metformin',
            'source_field': 'drug_name',
            'target_concept_id': 904542,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'REDCap drug name → RxNorm Metformin'
        },
        
        # ============================================================
        # VISITS: Visit type strings → Visit concepts
        # ============================================================
        {
            'data_source': 'REDCAP',
            'source_code': 'Outpatient',
            'source_value': 'Outpatient Visit',
            'source_field': 'visit_type',
            'target_concept_id': 9201,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'REDCap visit type → OMOP Outpatient'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Outpatient Visit',
            'source_value': 'Outpatient Visit',
            'source_field': 'visit_type',
            'target_concept_id': 9201,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'Alternative format'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Baseline Visit',
            'source_value': 'Baseline Visit',
            'source_field': 'visit_type',
            'target_concept_id': 9202,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'REDCap visit type → OMOP Baseline'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Inpatient',
            'source_value': 'Inpatient Visit',
            'source_field': 'visit_type',
            'target_concept_id': 9200,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'REDCap visit type → OMOP Inpatient'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Inpatient Visit',
            'source_value': 'Inpatient Visit',
            'source_field': 'visit_type',
            'target_concept_id': 9200,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'Alternative format'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Cycle Day 1',
            'source_value': 'Cycle Day 1',
            'source_field': 'visit_type',
            'target_concept_id': 9203,
            'mapping_type': 'EXACT',
            'confidence_score': 0.95,
            'notes': 'Treatment cycle visit'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Cycle Day 8',
            'source_value': 'Cycle Day 8',
            'source_field': 'visit_type',
            'target_concept_id': 9203,
            'mapping_type': 'PARENT',
            'confidence_score': 0.9,
            'notes': 'Treatment cycle visit (Day 8)'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Cycle Day 15',
            'source_value': 'Cycle Day 15',
            'source_field': 'visit_type',
            'target_concept_id': 9203,
            'mapping_type': 'PARENT',
            'confidence_score': 0.9,
            'notes': 'Treatment cycle visit (Day 15)'
        },
        {
            'data_source': 'REDCAP',
            'source_code': 'Follow-up',
            'source_value': 'Follow-up Visit',
            'source_field': 'visit_type',
            'target_concept_id': 9201,
            'mapping_type': 'PARENT',
            'confidence_score': 0.9,
            'notes': 'Follow-up is usually outpatient'
        },
        
        # ============================================================
        # LABS: LOINC codes → Lab concepts
        # ============================================================
        {
            'data_source': 'REDCAP',
            'source_code': '2160-0',
            'source_value': 'Creatinine',
            'source_field': 'lab_code',
            'target_concept_id': 3000963,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'LOINC 2160-0 → Creatinine'
        },
        {
            'data_source': 'REDCAP',
            'source_code': '718-7',
            'source_value': 'Hemoglobin',
            'source_field': 'lab_code',
            'target_concept_id': 3006924,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'LOINC 718-7 → Hemoglobin'
        },
        {
            'data_source': 'REDCAP',
            'source_code': '777-3',
            'source_value': 'Platelet count',
            'source_field': 'lab_code',
            'target_concept_id': 3007070,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'LOINC 777-3 → Platelet Count'
        },
        {
            'data_source': 'REDCAP',
            'source_code': '6690-2',
            'source_value': 'WBC Count',
            'source_field': 'lab_code',
            'target_concept_id': 3012888,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'LOINC 6690-2 → WBC Count'
        },
        {
            'data_source': 'REDCAP',
            'source_code': '1975-2',
            'source_value': 'Total Bilirubin',
            'source_field': 'lab_code',
            'target_concept_id': 3025315,
            'mapping_type': 'EXACT',
            'confidence_score': 1.0,
            'notes': 'LOINC 1975-2 → Bilirubin'
        },
    ]
    
    created_count = 0
    
    for mapping in mappings:
        try:
            redcap = DataSource.objects.get(name=mapping['data_source'])
            target_concept = Concept.objects.get(concept_id=mapping['target_concept_id'])
            
            cm, was_created = ConceptMapping.objects.get_or_create(
                data_source=redcap,
                source_code=mapping['source_code'],
                source_value=mapping['source_value'],
                source_field=mapping['source_field'],
                defaults={
                    'target_concept': target_concept,
                    'mapping_type': mapping['mapping_type'],
                    'confidence_score': mapping['confidence_score'],
                    'notes': mapping['notes'],
                }
            )
            
            if was_created:
                created_count += 1
                
        except (DataSource.DoesNotExist, Concept.DoesNotExist) as e:
            print(f"❌ Error creating mapping: {e}")
            continue
    
    print(f"\n✅ CONCEPT MAPPINGS SEEDED: {created_count}\n")


if __name__ == "__main__":
    print("\n")
    seed_concepts()
    seed_data_sources()
    seed_concept_mappings()
    
    print("="*80)
    print("✅ ALL SEEDS COMPLETE!")
    print("="*80)
    print("\nVerifying...")
    
    # Verify
    from django.db.models import Count
    
    concept_count = Concept.objects.count()
    mapping_count = ConceptMapping.objects.count()
    datasource_count = DataSource.objects.count()
    
    print(f"\nDatabase Summary:")
    print(f"  Concepts: {concept_count}")
    print(f"  DataSources: {datasource_count}")
    print(f"  ConceptMappings: {mapping_count}")
    
    # Show example mapping
    example = ConceptMapping.objects.filter(
        source_code='C34.1'
    ).first()
    
    if example:
        print(f"\nExample Mapping:")
        print(f"  Source: {example.source_code} ({example.source_value})")
        print(f"  Field: {example.source_field}")
        print(f"  Target Concept: {example.target_concept.concept_name} (ID: {example.target_concept.concept_id})")
        print(f"  Confidence: {example.confidence_score * 100}%")
        print(f"  Type: {example.mapping_type}")
    
    print("\n" + "="*80 + "\n")