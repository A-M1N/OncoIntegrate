import api from "./api";

export const patientService = {
  // Get all patients
  getPatients: async (page = 1, pageSize = 50) => {
    return api.get("/patients/", {
      params: { page, page_size: pageSize },
    });
  },

  // Get single patient
  getPatient: async (patientId) => {
    return api.get(`/patients/${patientId}/`);
  },

  // Get patient cancer profile (full journey)
  getPatientCancerProfile: async (patientId) => {
    return api.get(`/patients/${patientId}/cancer-profile/`);
  },

  // Get patient adverse events
  getAdverseEvents: async (patientId) => {
    return api.get(`/patients/${patientId}/adverse-events/`);
  },

  // Get patients by stage
  getPatientsByStage: async (stage) => {
    return api.get("/patients/by-stage/", {
      params: { stage },
    });
  },
};

export const patientKeys = {
  all: ["patients"],
  lists: () => [...patientKeys.all, "list"],
  list: (page, pageSize) => [...patientKeys.lists(), { page, pageSize }],
  details: () => [...patientKeys.all, "detail"],
  detail: (patientId) => [...patientKeys.details(), patientId],
  cancerProfile: (patientId) => [
    ...patientKeys.detail(patientId),
    "cancer-profile",
  ],
  adverseEvents: (patientId) => [
    ...patientKeys.detail(patientId),
    "adverse-events",
  ],
  byStage: (stage) => [...patientKeys.all, "by-stage", stage],
};
