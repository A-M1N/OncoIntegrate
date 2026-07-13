import styles from "./StageChart.module.css";

export default function StageChart({ data }) {
  const maxCount = Math.max(...data.map((d) => d.count));

  return (
    <div className={styles.card}>
      <h2>📊 Cancer Stages Distribution</h2>

      <div className={styles.chartContainer}>
        {data.map((item, idx) => {
          const percentage = (item.count / maxCount) * 100;
          return (
            <div key={idx} className={styles.barItem}>
              <div className={styles.label}>
                <span className={styles.stage}>Stage {item.stage}</span>
                <span className={styles.count}>{item.count}</span>
              </div>
              <div className={styles.barContainer}>
                <div
                  className={styles.bar}
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: "#3498db",
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
