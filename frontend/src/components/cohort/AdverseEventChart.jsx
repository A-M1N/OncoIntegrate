import styles from "./AdverseEventChart.module.css";

export default function AdverseEventChart({ data }) {
  const maxCount = Math.max(...data.map((d) => d.count));
  const gradeLabels = {
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Life-threatening",
    5: "Fatal",
  };

  const gradeColors = {
    1: "#27ae60",
    2: "#f39c12",
    3: "#e67e22",
    4: "#e74c3c",
    5: "#c0392b",
  };

  return (
    <div className={styles.card}>
      <h2>⚠️ Adverse Event Grade Distribution</h2>

      <div className={styles.chartContainer}>
        {data.map((item, idx) => {
          const percentage = (item.count / maxCount) * 100;
          const gradeLabel = gradeLabels[item.grade] || "Unknown";
          const color = gradeColors[item.grade] || "#95a5a6";

          return (
            <div key={idx} className={styles.gradeItem}>
              <div className={styles.label}>
                <span className={styles.gradeLabel}>
                  Grade {item.grade} - {gradeLabel}
                </span>
                <span className={styles.count}>{item.count} events</span>
              </div>
              <div className={styles.barContainer}>
                <div
                  className={styles.bar}
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: color,
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
