import { useDataQualitySummary } from "../hooks/useCohortStats";
import LoadingSpinner from "../components/common/LoadingSpinner";
import styles from "./ETLStatusPage.module.css";

export default function ETLStatusPage() {
  const { data: status, isLoading, error } = useDataQualitySummary();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div className="error">Error: {error.message}</div>;
  if (!status) return <div>No ETL data available</div>;

  const etl = status.latest_etl_run || {};

  return (
    <div className={styles.container}>
      <h1>ETL Status Dashboard</h1>

      {/* ETL Results Card */}
      <div className={styles.card}>
        <h2>Latest ETL Run</h2>

        <div className={styles.statsGrid}>
          <div className={styles.stat}>
            <p className={styles.label}>Source</p>
            <p className={styles.value}>{etl.source || "N/A"}</p>
          </div>

          <div
            className={`${styles.stat} ${etl.status === "SUCCESS" ? styles.success : styles.warning}`}
          >
            <p className={styles.label}>Status</p>
            <p className={styles.value}>{etl.status || "N/A"}</p>
          </div>

          <div className={styles.stat}>
            <p className={styles.label}>Records Processed</p>
            <p className={styles.value}>{etl.records_processed || 0}</p>
          </div>

          <div className={styles.stat}>
            <p className={styles.label}>Records Loaded</p>
            <p className={styles.value}>{etl.records_loaded || 0}</p>
          </div>

          <div className={styles.stat}>
            <p className={styles.label}>Success Rate</p>
            <p className={styles.value}>
              {etl.success_rate ? etl.success_rate.toFixed(1) : 0}%
            </p>
          </div>

          <div className={styles.stat}>
            <p className={styles.label}>Duration</p>
            <p className={styles.value}>
              {etl.duration_seconds ? etl.duration_seconds.toFixed(1) : 0}s
            </p>
          </div>
        </div>
      </div>

      {/* Data Loaded Card */}
      <div className={styles.card}>
        <h2>📊 Data Loaded</h2>

        <div className={styles.dataGrid}>
          {/* OMOP Layer */}
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>OMOP Layer (Standardized)</h3>
            <ul className={styles.list}>
              <li>
                👤 Persons: <strong>{status.total_persons_loaded}</strong>
              </li>
              <li>
                🩺 Conditions: <strong>{status.total_conditions_loaded}</strong>
              </li>
              <li>
                💊 Medications:{" "}
                <strong>{status.total_medications_loaded}</strong>
              </li>
              <li>
                🧪 Measurements:{" "}
                <strong>{status.total_measurements_loaded}</strong>
              </li>
            </ul>
          </div>

          {/* Cancer-Specific Layer */}
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>
              Cancer-Specific Layer (Research)
            </h3>
            <ul className={styles.list}>
              <li>
                🔬 Tumor Profiles:{" "}
                <strong>{status.total_cancer_profiles}</strong>
              </li>
              <li>
                💉 Treatments: <strong>{status.total_treatments}</strong>
              </li>
              <li>
                ⚠️ Adverse Events:{" "}
                <strong>{status.total_adverse_events}</strong>
              </li>
              <li>
                ⚙️ Quality Issues:{" "}
                <strong className={styles.error}>
                  {status.quality_issues}
                </strong>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className={styles.summary}>
        <p>
          ✅ ETL successfully loaded{" "}
          <strong>{status.total_persons_loaded} patients</strong> with
          comprehensive OMOP standardization and cancer-specific research data
          enrichment.
        </p>
      </div>
    </div>
  );
}
