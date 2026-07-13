import { createBrowserRouter } from "react-router-dom";
import Layout from "../components/layouts/Layout";
import NotFoundPage from "../pages/NotFoundPage";
import ETLStatusPage from "../pages/ETLStatusPage";
import PatientListPage from "../pages/PatientListPage";
import PatientDetailPage from "../pages/PatientDetailPage";
import CohortAnalyticsPage from "../pages/CohortAnalyticsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    errorElement: <NotFoundPage />,
    children: [
      {
        index: true,
        element: <ETLStatusPage />,
      },
      {
        path: "patients",
        element: <PatientListPage />,
      },
      {
        path: "patients/:patientId",
        element: <PatientDetailPage />,
      },
      {
        path: "cohorts",
        element: <CohortAnalyticsPage />,
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
