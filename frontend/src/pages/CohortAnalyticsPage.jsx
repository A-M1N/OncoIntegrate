import { useState } from "react";
import { useCohortStatistics } from "../hooks/useCohortStats";
import LoadingSpinner from "../components/common/LoadingSpinner";
import styles from "./CohortAnalyticsPage.module.css";
import StatsGrid from "../components/cohort/StatsGrid";
import StageChart from "../components/cohort/StageChart";
import HistologyChart from "../components/cohort/HistologyChart";
import TreatmentResponseChart from "../components/cohort/TreatmentResponseChart";
import AdverseEventChart from "../components/cohort/AdverseEventChart";

export default function CohortAnalyticsPage() {
  const [selectedStage, setSelectedStage] = useState(null);
  const { data: stats, isLoading, error } = useCohortStatistics(selectedStage);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div className="error">Error: {error.message}</div>;

  return (
    <div className={styles.container}>
      <h1>Cohort Analytics</h1>

      {/* Filters */}
      <div className={styles.card}>
        <label className={styles.filterLabel}>
          <span>Filter by Stage:</span>
          <select
            value={selectedStage || ""}
            onChange={(e) => setSelectedStage(e.target.value || null)}
            className={styles.select}
          >
            <option value="">All Stages</option>
            <option value="I">Stage I</option>
            <option value="II">Stage II</option>
            <option value="III">Stage III</option>
            <option value="IV">Stage IV</option>
          </select>
        </label>
      </div>

      {stats && (
        <>
          {/* Stats Overview */}
          <StatsGrid stats={stats} />

          {/* Stage Distribution Chart */}
          {stats.by_stage && stats.by_stage.length > 0 && (
            <StageChart data={stats.by_stage} />
          )}

          {/* Histology Distribution Chart */}
          {stats.by_histology && stats.by_histology.length > 0 && (
            <HistologyChart data={stats.by_histology} />
          )}

          {/* Treatment Response Distribution */}
          {stats.treatment_response_distribution && (
            <TreatmentResponseChart
              distribution={stats.treatment_response_distribution}
            />
          )}

          {/* Adverse Event Grade Distribution */}
          {stats.adverse_event_grade_distribution &&
            stats.adverse_event_grade_distribution.length > 0 && (
              <AdverseEventChart
                data={stats.adverse_event_grade_distribution}
              />
            )}

          {/* Top Regimens */}
          {stats.top_regimens && stats.top_regimens.length > 0 && (
            <div className={styles.card}>
              <h2>💊 Top Treatment Regimens</h2>
              <div className={styles.regimenList}>
                {stats.top_regimens.map((regimen, idx) => (
                  <div key={idx} className={styles.regimenItem}>
                    <span className={styles.rank}>#{idx + 1}</span>
                    <span className={styles.name}>{regimen.regimen_name}</span>
                    <span className={styles.count}>
                      {regimen.count} patients
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
