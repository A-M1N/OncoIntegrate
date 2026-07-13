import styles from "./LabResultsTable.module.css";

export default function LabResultsTable({ labs }) {
  return (
    <div className={styles.card}>
      <h2>🧪 Lab Results</h2>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Test</th>
              <th>Value</th>
              <th>Unit</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {labs.map((lab, idx) => (
              <tr key={idx} className={styles.row}>
                <td>{lab.name}</td>
                <td className={styles.bold}>{lab.value}</td>
                <td>{lab.unit || "N/A"}</td>
                <td>{lab.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className={styles.note}>
        ℹ️ Your ETL loaded {labs.length} measurements for this patient
      </p>
    </div>
  );
}
