"""
Automated tests for the REDCap -> OMOP ETL pipeline.
WHY THESE TESTS EXIST
----------------------
The ETL's own `validate_input()` only checks that fields are *present* —
it can't tell you whether the pipeline produced the *correct* OMOP records,
correctly linked the cancer-specific layer back to OMOP, or is safe to
re-run. These tests use a small, hand-crafted fixture (2 patients) where
every expected output value is known in advance, so failures point at
exactly what broke.
"""
import os
from django.test import TestCase
from data.models import (
    Concept, DataSource, ConceptMapping,
    Person, ConditionOccurrence, DrugExposure, Measurement, VisitOccurrence,
    TumorProfile, TreatmentRegimen, AdverseEvent,
)
from data.etl.etl_redcap import RedcapETL

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures', 'mock_redcap_mini')


class RedcapETLTestCase(TestCase):
    """
    Seeds the minimum Concept/DataSource/ConceptMapping rows the fixture
    needs, then runs the real RedcapETL against the 2-patient fixture.
    Each test method runs inside Django's transactional TestCase, so the
    DB is rolled back to empty between tests automatically.
    """

    @classmethod
    def setUpTestData(cls):
        # ---- Concepts ----
        concepts = [
            (8507, 'Female', 'GENDER', 'F', 'Gender'),
            (8508, 'Male', 'GENDER', 'M', 'Gender'),
            (201826, 'Malignant neoplasm of lung', 'SNOMED', '162573006', 'Condition'),
            (201827, 'Malignant neoplasm of breast', 'SNOMED', '126618006', 'Condition'),
            (1708147, 'Pemetrexed', 'RxNorm', '1708147', 'Drug'),
            (945638, 'Carboplatin', 'RxNorm', '945638', 'Drug'),
            (1585838, 'Nivolumab', 'RxNorm', '1585838', 'Drug'),
            (9201, 'Outpatient Visit', 'Visit', '9201', 'Visit'),
            (9202, 'Baseline Visit', 'Visit', '9202', 'Visit'),
            (3000963, 'Creatinine', 'LOINC', '2160-0', 'Measurement'),
            (3006924, 'Hemoglobin', 'LOINC', '718-7', 'Measurement'),
        ]
        for concept_id, name, vocab, code, domain in concepts:
            Concept.objects.create(
                concept_id=concept_id, concept_name=name,
                vocabulary_id=vocab, concept_code=code, domain_id=domain,
            )

        # ---- DataSource ----
        cls.data_source = DataSource.objects.create(
            name='REDCAP',
            display_name='REDCap eCRF (test)',
            source_type='JSON',
            parser_class='data.etl.etl_redcap.RedcapETL',
            connection_config={'path': FIXTURE_DIR},
            is_active=True,
            min_mapping_confidence=0.9,
            max_unmapped_percent=10.0,
        )

        # ---- ConceptMappings (source code -> OMOP concept) ----
        mappings = [
            ('C34.9', 'Lung Cancer', 'cancer_type_code', 201826),
            ('C50.9', 'Breast Cancer', 'cancer_type_code', 201827),
            ('Pemetrexed', 'Pemetrexed', 'drug_name', 1708147),
            ('Carboplatin', 'Carboplatin', 'drug_name', 945638),
            ('Nivolumab', 'Nivolumab', 'drug_name', 1585838),
            ('Baseline Visit', 'Baseline Visit', 'visit_type', 9202),
            ('Outpatient', 'Outpatient Visit', 'visit_type', 9201),
            ('2160-0', 'Creatinine', 'lab_code', 3000963),
            ('718-7', 'Hemoglobin', 'lab_code', 3006924),
        ]
        for source_code, source_value, source_field, target_id in mappings:
            ConceptMapping.objects.create(
                data_source=cls.data_source,
                source_code=source_code,
                source_value=source_value,
                source_field=source_field,
                target_concept=Concept.objects.get(concept_id=target_id),
                mapping_type='EXACT',
                confidence_score=1.0,
            )

    def _run_etl(self):
        etl = RedcapETL(redcap_folder=FIXTURE_DIR)
        return etl.run()

    # ------------------------------------------------------------------
    # Basic counts
    # ------------------------------------------------------------------
    def test_extracts_and_loads_expected_row_counts(self):
        report = self._run_etl()

        self.assertEqual(report['status'], 'SUCCESS')
        self.assertEqual(Person.objects.count(), 2)
        self.assertEqual(ConditionOccurrence.objects.count(), 2)
        self.assertEqual(DrugExposure.objects.count(), 3)  # 2 drugs for TEST_001, 1 for TEST_002
        self.assertEqual(Measurement.objects.count(), 2)
        self.assertEqual(VisitOccurrence.objects.count(), 2)
        self.assertEqual(TumorProfile.objects.count(), 2)
        self.assertEqual(TreatmentRegimen.objects.count(), 2)
        self.assertEqual(AdverseEvent.objects.count(), 2)
        self.assertEqual(report['unmapped_concepts'], 0)

    # ------------------------------------------------------------------
    # Concept resolution correctness
    # ------------------------------------------------------------------
    def test_person_gender_and_birthdate_resolved_correctly(self):
        self._run_etl()

        p1 = Person.objects.get(person_source_value='TEST_001')
        self.assertEqual(p1.gender_concept.concept_name, 'Female')
        self.assertEqual(p1.year_of_birth, 1965)
        self.assertEqual(p1.month_of_birth, 3)
        self.assertEqual(p1.day_of_birth, 15)

        p2 = Person.objects.get(person_source_value='TEST_002')
        self.assertEqual(p2.gender_concept.concept_name, 'Male')

    def test_condition_mapped_to_correct_snomed_concept(self):
        self._run_etl()

        p1 = Person.objects.get(person_source_value='TEST_001')
        condition = ConditionOccurrence.objects.get(person=p1)
        self.assertEqual(condition.condition_concept.concept_id, 201826)
        self.assertEqual(condition.condition_concept.concept_name, 'Malignant neoplasm of lung')

    # ------------------------------------------------------------------
    # Dual-layer linkage
    # ------------------------------------------------------------------
    def test_tumor_profile_links_back_to_condition_occurrence(self):
        self._run_etl()

        p1 = Person.objects.get(person_source_value='TEST_001')
        tumor = TumorProfile.objects.get(person=p1)

        self.assertIsNotNone(
            tumor.primary_diagnosis,
            "TumorProfile.primary_diagnosis should be linked to the matching "
            "ConditionOccurrence, not None. If this fails, check that dates "
            "flowing through the ETL are consistently datetime.date objects."
        )
        self.assertEqual(tumor.primary_diagnosis.condition_concept.concept_id, 201826)
        self.assertEqual(tumor.stage, 'III')
        self.assertEqual(tumor.histology, 'Adenocarcinoma')
        self.assertEqual(tumor.mutation_status, 'EGFR+')

    def test_all_tumor_profiles_are_linked_not_just_one(self):
        self._run_etl()
        unlinked = TumorProfile.objects.filter(primary_diagnosis__isnull=True).count()
        self.assertEqual(unlinked, 0)

    # ------------------------------------------------------------------
    # Adverse event -> regimen matching, both strategies
    # ------------------------------------------------------------------
    def test_ae_exact_start_date_match_strategy(self):
        """TEST_001's AE has a treatment_start_date that exactly matches its
        regimen's start_date -> should hit Strategy 1 (exact match)."""
        self._run_etl()

        p1 = Person.objects.get(person_source_value='TEST_001')
        ae = AdverseEvent.objects.get(person=p1, event_name='Neuropathy')

        self.assertIsNotNone(ae.treatment_regimen)
        self.assertEqual(ae.treatment_regimen.regimen_name, 'Pemetrexed + Carboplatin')
        self.assertEqual(ae.grade, '2')

    def test_ae_date_range_match_strategy_for_ongoing_regimen(self):
        """TEST_002's AE has no treatment_start_date at all, and its regimen
        has no end_date (still ongoing) -> should hit Strategy 2 (date range),
        matching because the AE date falls after the regimen's start date."""
        self._run_etl()

        p2 = Person.objects.get(person_source_value='TEST_002')
        ae = AdverseEvent.objects.get(person=p2, event_name='Fatigue')

        self.assertIsNotNone(ae.treatment_regimen)
        self.assertEqual(ae.treatment_regimen.regimen_name, 'Nivolumab')

    def test_no_adverse_event_is_left_unlinked(self):
        self._run_etl()
        unlinked = AdverseEvent.objects.filter(treatment_regimen__isnull=True).count()
        self.assertEqual(unlinked, 0)

    # ------------------------------------------------------------------
    # Data quality gate
    # ------------------------------------------------------------------
    def test_unmapped_concept_is_tracked_not_silently_dropped(self):
        """A drug with no seeded concept or mapping should be recorded as
        an UnmappedConcept rather than just vanishing."""
        # Add an extra, deliberately unmapped drug directly to a fresh ETL run
        etl = RedcapETL(redcap_folder=FIXTURE_DIR)
        etl.extract()
        etl.medications_data.append({
            'person_source_id': 'TEST_001',
            'drug_code': 'unobtainium',
            'drug_name': 'Unobtainium',
            'drug_start_date': etl.medications_data[0]['drug_start_date'],
            'drug_end_date': None,
            'quantity': None,
        })
        etl.validate_input()
        etl.transform_and_load()

        from data.models import UnmappedConcept
        self.assertTrue(
            UnmappedConcept.objects.filter(source_code='unobtainium').exists()
        )

    # ------------------------------------------------------------------
    # Hard-fail validation gate
    # ------------------------------------------------------------------
    def test_missing_critical_date_aborts_run_and_writes_nothing(self):
        """A condition with no condition_date is a critical issue -- the
        whole run should abort in validate_input(), before anything is
        written, rather than silently loading a broken record."""
        etl = RedcapETL(redcap_folder=FIXTURE_DIR)
        etl.extract()
        etl.conditions_data[0]['condition_date'] = None

        with self.assertRaises(ValueError):
            etl.validate_input()

        # Nothing should have been written -- validate_input raises before
        # transform_and_load() is ever called.
        self.assertEqual(Person.objects.count(), 0)
        self.assertEqual(ConditionOccurrence.objects.count(), 0)

    def test_missing_adverse_event_grade_aborts_run(self):
        """An adverse event with no grade is clinically meaningless and
        should hard-fail, not load as a record with an empty severity."""
        etl = RedcapETL(redcap_folder=FIXTURE_DIR)
        etl.extract()
        etl.adverse_events_data[0]['grade'] = None

        with self.assertRaises(ValueError):
            etl.validate_input()

    def test_missing_optional_field_does_not_abort_run(self):
        """Missing condition_code is a soft warning, not critical -- it's
        handled gracefully at load time via UnmappedConcept tracking, so
        the run should still succeed."""
        etl = RedcapETL(redcap_folder=FIXTURE_DIR)
        etl.extract()
        etl.conditions_data[0]['condition_code'] = None

        # Should not raise.
        etl.validate_input()
        etl.transform_and_load()

        self.assertEqual(Person.objects.count(), 2)

    def test_full_run_still_succeeds_with_valid_fixture_data(self):
        """Sanity check that the new hard-fail gate doesn't false-positive
        on the normal, valid fixture."""
        report = self._run_etl()
        self.assertEqual(report['status'], 'SUCCESS')

    # ------------------------------------------------------------------
    # Re-run safety (the natural-key existence checks)
    # ------------------------------------------------------------------
    def test_running_etl_twice_does_not_duplicate_records(self):
        first_report = self._run_etl()
        self.assertEqual(first_report['records_skipped'], 0)

        second_report = self._run_etl()

        # Counts must be identical after the second run -- nothing doubled.
        self.assertEqual(Person.objects.count(), 2)
        self.assertEqual(ConditionOccurrence.objects.count(), 2)
        self.assertEqual(DrugExposure.objects.count(), 3)
        self.assertEqual(Measurement.objects.count(), 2)
        self.assertEqual(VisitOccurrence.objects.count(), 2)
        self.assertEqual(TumorProfile.objects.count(), 2)
        self.assertEqual(TreatmentRegimen.objects.count(), 2)
        self.assertEqual(AdverseEvent.objects.count(), 2)

        # And the second run should report everything as skipped, not loaded.
        self.assertGreater(second_report['records_skipped'], 0)
        self.assertEqual(second_report['status'], 'SUCCESS')