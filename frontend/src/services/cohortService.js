import api from "./api";

export const cohortService = {
  // Get cohort statistics
  getStatistics: async (stage = null, histology = null) => {
    return api.get("/cohorts/statistics/", {
      params: { stage, histology },
    });
  },

  // Get treatment responses
  getTreatmentResponses: async () => {
    return api.get("/cohorts/treatment-responses/");
  },

  // Get data quality summary
  getDataQualitySummary: async () => {
    return api.get("/data-quality/summary/");
  },
};

export const cohortKeys = {
  all: ["cohorts"],
  statistics: (stage, histology) => [
    ...cohortKeys.all,
    "statistics",
    { stage, histology },
  ],
  responses: () => [...cohortKeys.all, "responses"],
  dataQuality: () => [...cohortKeys.all, "data-quality"],
};
