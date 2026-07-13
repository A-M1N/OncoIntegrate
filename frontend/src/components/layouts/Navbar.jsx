import { Link } from "react-router-dom";
import styles from "./Navbar.module.css";

export default function Navbar() {
  return (
    <nav className={styles.navbar}>
      <div className="container">
        <div className={styles.navContent}>
          <Link to="/" className={styles.logo}>
            🔬 OncoIntegrate
          </Link>

          <ul className={styles.navLinks}>
            <li>
              <Link to="/" className={styles.link}>
                ETL Status
              </Link>
            </li>
            <li>
              <Link to="/patients" className={styles.link}>
                Patients
              </Link>
            </li>
            <li>
              <Link to="/cohorts" className={styles.link}>
                Cohorts
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}
