import { useQuery } from "@tanstack/react-query";
import { patientService, patientKeys } from "../services/patientService";

export const usePatientDetail = (patientId) => {
  return useQuery({
    queryKey: patientKeys.detail(patientId),
    queryFn: () => patientService.getPatient(patientId),
    enabled: !!patientId, // Only run if patientId exists
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  });
};

export const usePatientCancerProfile = (patientId) => {
  return useQuery({
    queryKey: patientKeys.cancerProfile(patientId),
    queryFn: () => patientService.getPatientCancerProfile(patientId),
    enabled: !!patientId,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  });
};

export const useAdverseEvents = (patientId) => {
  return useQuery({
    queryKey: patientKeys.adverseEvents(patientId),
    queryFn: () => patientService.getAdverseEvents(patientId),
    enabled: !!patientId,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  });
};
