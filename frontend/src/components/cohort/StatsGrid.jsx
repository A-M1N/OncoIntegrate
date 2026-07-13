import styles from "./StatsGrid.module.css";

export default function StatsGrid({ stats }) {
  return (
    <div className={styles.card}>
      <h2>📊 Summary Statistics</h2>

      <div className={styles.statsGrid}>
        <div className={styles.stat}>
          <p className={styles.label}>Total Patients</p>
          <p className={styles.value}>{stats.total_patients}</p>
        </div>

        <div className={styles.stat}>
          <p className={styles.label}>Cancer Stages</p>
          <p className={styles.value}>{stats.by_stage?.length || 0}</p>
        </div>

        <div className={styles.stat}>
          <p className={styles.label}>Histology Types</p>
          <p className={styles.value}>{stats.by_histology?.length || 0}</p>
        </div>

        <div className={styles.stat}>
          <p className={styles.label}>Top Regimens</p>
          <p className={styles.value}>{stats.top_regimens?.length || 0}</p>
        </div>
      </div>
    </div>
  );
}
