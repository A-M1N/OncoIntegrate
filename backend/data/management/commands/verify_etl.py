"""
Management command to sanity-check ETL output.

This does NOT replace real automated tests — see the note at the bottom
of the chat response for a suggested pytest-based approach. This is a
fast, no-setup-required smoke test you can run after every ETL run,
especially useful right before a demo.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from data.models import (
    Person, ConditionOccurrence, DrugExposure, Measurement, VisitOccurrence,
    TumorProfile, TreatmentRegimen, AdverseEvent, UnmappedConcept
)


class Command(BaseCommand):
    help = "Verify ETL output: FK linkage, duplicates, and basic counts"

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("ETL VERIFICATION REPORT")
        self.stdout.write("=" * 80 + "\n")

        self._counts()
        self._fk_integrity()
        self._duplicates()
        self._unmapped()

        self.stdout.write("\n" + "=" * 80 + "\n")

    # ------------------------------------------------------------------
    def _counts(self):
        self.stdout.write("-- Row counts --")
        for model in [Person, ConditionOccurrence, DrugExposure, Measurement,
                      VisitOccurrence, TumorProfile, TreatmentRegimen, AdverseEvent]:
            self.stdout.write(f"  {model.__name__:<20} {model.objects.count()}")
        self.stdout.write("")

    # ------------------------------------------------------------------
    def _fk_integrity(self):
        """
        Checks the exact thing that was broken before the date-parsing fix:
        TumorProfile.primary_diagnosis and AdverseEvent.treatment_regimen
        should actually be populated, not silently null.
        """
        self.stdout.write("-- FK linkage integrity --")

        total_tumors = TumorProfile.objects.count()
        linked_tumors = TumorProfile.objects.filter(primary_diagnosis__isnull=False).count()
        if total_tumors:
            pct = linked_tumors / total_tumors * 100
            flag = "OK" if pct > 90 else "CHECK THIS"
            self.stdout.write(
                f"  [{flag}] TumorProfile.primary_diagnosis linked: "
                f"{linked_tumors}/{total_tumors} ({pct:.1f}%)"
            )
        else:
            self.stdout.write("  No TumorProfile rows to check")

        total_ae = AdverseEvent.objects.count()
        linked_ae = AdverseEvent.objects.filter(treatment_regimen__isnull=False).count()
        if total_ae:
            pct = linked_ae / total_ae * 100
            flag = "OK" if pct > 90 else "CHECK THIS"
            self.stdout.write(
                f"  [{flag}] AdverseEvent.treatment_regimen linked: "
                f"{linked_ae}/{total_ae} ({pct:.1f}%)"
            )
        else:
            self.stdout.write("  No AdverseEvent rows to check")

        # Every TreatmentRegimen should ideally have a tumor_profile too
        total_regimens = TreatmentRegimen.objects.count()
        linked_regimens = TreatmentRegimen.objects.filter(tumor_profile__isnull=False).count()
        if total_regimens:
            pct = linked_regimens / total_regimens * 100
            self.stdout.write(
                f"  [info] TreatmentRegimen.tumor_profile linked: "
                f"{linked_regimens}/{total_regimens} ({pct:.1f}%)"
            )
        self.stdout.write("")

    # ------------------------------------------------------------------
    def _duplicates(self):
        """
        Only Person and TumorProfile currently check for existing rows
        before inserting. Everything else (conditions, medications,
        measurements, visits, treatment regimens, adverse events) will
        be duplicated if the ETL is run twice against the same DB.
        This flags it so it's visible instead of silent.
        """
        self.stdout.write("-- Duplicate detection (re-run safety) --")

        dup_conditions = (
            ConditionOccurrence.objects.values('person_id', 'condition_concept_id', 'condition_start_date')
            .annotate(n=Count('pk')).filter(n__gt=1)
        )
        dup_meds = (
            DrugExposure.objects.values('person_id', 'drug_concept_id', 'drug_exposure_start_date')
            .annotate(n=Count('pk')).filter(n__gt=1)
        )
        # NOTE: keyed on (person, concept, date) only, matching the dedup fix in
        # _load_measurements -- deliberately excludes value_as_number, since
        # comparing a DB Decimal to a Python float for equality is unreliable
        # (e.g. Decimal('1.2') == 1.2 is False due to binary float precision).
        dup_measurements = (
            Measurement.objects.values('person_id', 'measurement_concept_id', 'measurement_date')
            .annotate(n=Count('pk')).filter(n__gt=1)
        )
        dup_visits = (
            VisitOccurrence.objects.values('person_id', 'visit_concept_id', 'visit_start_date')
            .annotate(n=Count('pk')).filter(n__gt=1)
        )
        dup_regimens = (
            TreatmentRegimen.objects.values('person_id', 'regimen_name', 'start_date')
            .annotate(n=Count('pk')).filter(n__gt=1)
        )
        dup_ae = (
            AdverseEvent.objects.values('person_id', 'event_name', 'event_date')
            .annotate(n=Count('pk')).filter(n__gt=1)
        )

        checks = [
            ("ConditionOccurrence", dup_conditions),
            ("DrugExposure", dup_meds),
            ("Measurement", dup_measurements),
            ("VisitOccurrence", dup_visits),
            ("TreatmentRegimen", dup_regimens),
            ("AdverseEvent", dup_ae),
        ]

        any_dups = False
        for name, qs in checks:
            count = qs.count()
            if count > 0:
                any_dups = True
                self.stdout.write(f"  [DUPLICATES FOUND] {name}: {count} duplicate key groups")
            else:
                self.stdout.write(f"  [OK] {name}: no duplicates")

        if any_dups:
            self.stdout.write(
                "\n  NOTE: this usually means the ETL was run more than once against\n"
                "  the same database without a flush in between. Only Person and\n"
                "  TumorProfile currently guard against duplicate inserts."
            )
        self.stdout.write("")

    # ------------------------------------------------------------------
    def _unmapped(self):
        self.stdout.write("-- Unmapped concepts --")
        unresolved = UnmappedConcept.objects.filter(status='UNRESOLVED').count()
        if unresolved:
            self.stdout.write(f"  [CHECK THIS] {unresolved} unresolved unmapped concepts")
            for u in UnmappedConcept.objects.filter(status='UNRESOLVED').order_by('-occurrence_count')[:5]:
                self.stdout.write(f"    - {u.source_value} ({u.domain_id}) x{u.occurrence_count}")
        else:
            self.stdout.write("  [OK] No unresolved unmapped concepts")
        self.stdout.write("")