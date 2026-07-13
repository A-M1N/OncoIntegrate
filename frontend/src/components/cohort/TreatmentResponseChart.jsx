import styles from "./TreatmentResponseChart.module.css";

export default function TreatmentResponseChart({ distribution }) {
  const responses = [
    { key: "CR", label: "Complete Response", color: "#27ae60" },
    { key: "PR", label: "Partial Response", color: "#3498db" },
    { key: "SD", label: "Stable Disease", color: "#f39c12" },
    { key: "PD", label: "Progressive Disease", color: "#e74c3c" },
  ];

  const total = Object.values(distribution).reduce((a, b) => a + b, 0);

  return (
    <div className={styles.card}>
      <h2>💊 Treatment Response Distribution</h2>

      {total === 0 ? (
        <p className={styles.noData}>No treatment data available</p>
      ) : (
        <div className={styles.chartContainer}>
          {responses.map((response) => {
            const count = distribution[response.key] || 0;
            const percentage = total > 0 ? (count / total) * 100 : 0;

            return (
              <div key={response.key} className={styles.responseItem}>
                <div className={styles.responseHeader}>
                  <span className={styles.responseLabel}>{response.label}</span>
                  <span className={styles.responseCount}>
                    {count} ({percentage.toFixed(1)}%)
                  </span>
                </div>
                <div className={styles.barContainer}>
                  <div
                    className={styles.bar}
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: response.color,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
