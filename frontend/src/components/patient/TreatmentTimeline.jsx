import styles from "./TreatmentTimeline.module.css";

export default function TreatmentTimeline({ treatments }) {
  const getResponseClass = (response) => {
    const classMap = {
      CR: styles.responseCR,
      PR: styles.responsePR,
      SD: styles.responseSD,
      PD: styles.responsePD,
    };
    return classMap[response] || "";
  };

  // Handle empty state
  if (!treatments || treatments.length === 0) {
    return (
      <div className={styles.card}>
        <h2>💊 Treatment Journey</h2>
        <p className={styles.noData}>No treatments recorded</p>
      </div>
    );
  }

  return (
    <div className={styles.card}>
      <h2>💊 Treatment Journey</h2>

      <div className={styles.timeline}>
        {treatments.map((treatment, idx) => (
          <div key={idx} className={styles.timelineItem}>
            <div className={styles.itemHeader}>
              <div>
                <h4>{treatment.regimen_name}</h4>
                <p className={styles.dates}>
                  {treatment.start_date}
                  {treatment.end_date && ` to ${treatment.end_date}`}
                </p>
              </div>
              <span
                className={`${styles.response} ${getResponseClass(treatment.best_response)}`}
              >
                {treatment.best_response}
              </span>
            </div>

            <div className={styles.itemBody}>
              <p>
                Cycles Completed: <strong>{treatment.cycles_completed}</strong>
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
