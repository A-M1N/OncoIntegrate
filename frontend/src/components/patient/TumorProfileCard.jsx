import styles from "./TumorProfileCard.module.css";

export default function TumorProfileCard({ tumor }) {
  if (!tumor) return null;

  return (
    <div className={styles.card}>
      <h2>🔬 Cancer Diagnosis</h2>

      <div className={styles.grid}>
        <div className={styles.item}>
          <p className={styles.label}>Cancer Type</p>
          <p className={styles.value}>{tumor.primary_diagnosis}</p>
        </div>

        <div className={styles.item}>
          <p className={styles.label}>Stage</p>
          <p className={`${styles.value} ${styles.stage}`}>{tumor.stage}</p>
        </div>

        <div className={styles.item}>
          <p className={styles.label}>Histology</p>
          <p className={styles.value}>{tumor.histology || "N/A"}</p>
        </div>

        <div className={styles.item}>
          <p className={styles.label}>Mutation</p>
          <p className={styles.value}>{tumor.mutation_status || "N/A"}</p>
        </div>
      </div>

      <div className={styles.dateSection}>
        <p>
          <strong>Diagnosis Date:</strong> {tumor.diagnosis_date || "N/A"}
        </p>
      </div>
    </div>
  );
}
