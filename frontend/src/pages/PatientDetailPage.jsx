import { useParams } from "react-router-dom";
import { usePatientCancerProfile } from "../hooks/usePatientDetail";
import LoadingSpinner from "../components/common/LoadingSpinner";
import TumorProfileCard from "../components/patient/TumorProfileCard";
import TreatmentTimeline from "../components/patient/TreatmentTimeline";
import AdverseEventsList from "../components/patient/AdverseEventsList";
import LabResultsTable from "../components/patient/LabResultsTable";
import styles from "./PatientDetailPage.module.css";

export default function PatientDetailPage() {
  const { patientId } = useParams();
  const {
    data: patient,
    isLoading,
    error,
  } = usePatientCancerProfile(patientId);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div className="error">Error: {error.message}</div>;
  if (!patient) return <div>Patient not found</div>;
  {
    console.log(patient);
  }
  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.card}>
        <h1>Patient Profile</h1>

        <div className={styles.infoGrid}>
          <div>
            <p className={styles.label}>ID</p>
            <p className={styles.value}>{patient.person_id}</p>
          </div>
          <div>
            <p className={styles.label}>Source ID</p>
            <p className={styles.value}>{patient.source_value}</p>
          </div>
          <div>
            <p className={styles.label}>Age</p>
            <p className={styles.value}>{patient.age || "N/A"}</p>
          </div>
          <div>
            <p className={styles.label}>Gender</p>
            <p className={styles.value}>{patient.gender || "N/A"}</p>
          </div>
        </div>
      </div>

      {/* Tumor Profile */}
      {patient.tumor && <TumorProfileCard tumor={patient.tumor} />}

      {/* Treatment Timeline */}
      {patient.treatments && patient.treatments.length > 0 && (
        <TreatmentTimeline treatments={patient.treatments} />
      )}

      {/* Adverse Events */}
      {patient.adverse_events && patient.adverse_events.length > 0 && (
        <AdverseEventsList adverseEvents={patient.adverse_events} />
      )}

      {/* Lab Results */}
      {patient.recent_labs && patient.recent_labs.length > 0 && (
        <LabResultsTable labs={patient.recent_labs} />
      )}
    </div>
  );
}
