import { useQuery } from "@tanstack/react-query";
import { patientService, patientKeys } from "../services/patientService";

export const usePatients = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: patientKeys.list(page, pageSize),
    queryFn: () => patientService.getPatients(page, pageSize),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes (cacheTime)
  });
};
