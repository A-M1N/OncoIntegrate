import styles from "./AdverseEventsList.module.css";

export default function AdverseEventsList({ adverseEvents }) {
  const getGradeClass = (grade) => {
    const classes = {
      1: styles.grade1,
      2: styles.grade2,
      3: styles.grade3,
      4: styles.grade4,
      5: styles.grade5,
    };
    return classes[grade] || "";
  };
  // Handle empty state
  if (!adverseEvents || adverseEvents.length === 0) {
    return (
      <div className={styles.card}>
        <h2>⚠️ Adverse Events</h2>
        <p className={styles.noData}>No adverse events recorded</p>
      </div>
    );
  }

  return (
    <div className={styles.card}>
      <h2>⚠️ Adverse Events</h2>

      <div className={styles.eventsList}>
        {adverseEvents.map((ae, idx) => (
          <div key={idx} className={styles.eventItem}>
            <div className={styles.eventContent}>
              <p className={styles.eventName}>{ae.event_name}</p>

              <p className={styles.eventDate}>{ae.event_date}</p>

              <p>{ae.regimen}</p>

              <p>{ae.resolution_status}</p>

              {ae.event_description && <p>{ae.event_description}</p>}
            </div>

            <span
              className={`${styles.grade} ${getGradeClass(Number(ae.grade))}`}
            >
              Grade {ae.grade}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
