import styles from "./HistologyChart.module.css";

export default function HistologyChart({ data }) {
  const maxCount = Math.max(...data.map((d) => d.count));
  const colors = [
    "#e74c3c",
    "#3498db",
    "#2ecc71",
    "#f39c12",
    "#9b59b6",
    "#1abc9c",
    "#e67e22",
    "#34495e",
  ];

  return (
    <div className={styles.card}>
      <h2>🔬 Histology Distribution</h2>

      <div className={styles.chartContainer}>
        {data.map((item, idx) => {
          const percentage = (item.count / maxCount) * 100;
          return (
            <div key={idx} className={styles.barItem}>
              <div className={styles.label}>
                <span className={styles.histology}>{item.histology}</span>
                <span className={styles.count}>{item.count}</span>
              </div>
              <div className={styles.barContainer}>
                <div
                  className={styles.bar}
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: colors[idx % colors.length],
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
