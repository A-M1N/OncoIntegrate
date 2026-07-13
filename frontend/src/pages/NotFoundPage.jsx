import { Link } from "react-router-dom";
import styles from "./NotFoundPage.module.css";

export default function NotFoundPage() {
  return (
    <div className={styles.container}>
      <h1>404</h1>
      <p>Page Not Found</p>
      <p className={styles.description}>
        Sorry, the page you're looking for doesn't exist.
      </p>
      <Link to="/" className={styles.link}>
        Go Home
      </Link>
    </div>
  );
}
