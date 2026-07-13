import { useState } from "react";
import { Link } from "react-router-dom";
import { usePatients } from "../hooks/usePatients";
import LoadingSpinner from "../components/common/LoadingSpinner";
import styles from "./PatientListPage.module.css";

export default function PatientListPage() {
  const [page, setPage] = useState(1);
  const pageSize = 25;
  const { data, isLoading, error } = usePatients(page, pageSize);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div className="error">Error: {error.message}</div>;

  const patients = data?.results || [];

  const handleNextPage = () => {
    if (page < data?.total_pages) {
      setPage(page + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handlePrevPage = () => {
    if (page > 1) {
      setPage(page - 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <div className={styles.container}>
      <h1>Patient Registry</h1>

      <div className={styles.card}>
        <p className={styles.totalCount}>
          Total Patients: <span>{patients.length}</span>
        </p>

        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Source ID</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Tumor Profile</th>
                <th>Treatments</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr key={patient.person_id} className={styles.row}>
                  <td>{patient.person_id}</td>
                  <td>{patient.source_value}</td>
                  <td>{patient.age || "N/A"}</td>
                  <td>{patient.gender || "N/A"}</td>
                  <td className={styles.center}>
                    {patient.tumor_profile?.length > 0 ? "✓" : "-"}
                  </td>
                  <td className={styles.center}>
                    {patient.treatments?.length || 0}
                  </td>
                  <td>
                    <Link
                      to={`/patients/${patient.person_id}`}
                      className={styles.link}
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className={styles.pagination}>
        <button onClick={handlePrevPage} disabled={page === 1}>
          ← Previous
        </button>
        <span>
          Page {page} of {data?.total_pages || 1}
        </span>
        <button onClick={handleNextPage} disabled={page >= data?.total_pages}>
          Next →
        </button>
      </div>
    </div>
  );
}
