import { useQuery } from "@tanstack/react-query";
import { cohortService, cohortKeys } from "../services/cohortService";

export const useCohortStatistics = (stage = null, histology = null) => {
  return useQuery({
    queryKey: cohortKeys.statistics(stage, histology),
    queryFn: () => cohortService.getStatistics(stage, histology),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  });
};

export const useTreatmentResponses = () => {
  return useQuery({
    queryKey: cohortKeys.responses(),
    queryFn: () => cohortService.getTreatmentResponses(),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  });
};

export const useDataQualitySummary = () => {
  return useQuery({
    queryKey: cohortKeys.dataQuality(),
    queryFn: () => cohortService.getDataQualitySummary(),
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  });
};
