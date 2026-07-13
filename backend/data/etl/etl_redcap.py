import json
from datetime import datetime
from data.etl.etl_base import BaseETL
import logging

logger = logging.getLogger(__name__)

class RedcapETL(BaseETL):
    # ETL Pipeline for mock REDCAP Json Data 
    
    def __init__(self,  redcap_folder=None):
        super().__init__("REDCAP")
        if redcap_folder:
            self.redcap_folder = redcap_folder
        else:
            # Get from database config
            self.redcap_folder = self.data_source.connection_config.get('path')
        
        if not self.redcap_folder:
            raise ValueError(
                "No redcap_folder provided and none in DataSource.connection_config"
            )
    
    @staticmethod
    def _parse_date(value):
        if value is None or value == "":
            return None
        if hasattr(value,"isoformat") and not isinstance(value,str):
            # already a date/datetime 
            return value
        return datetime.strptime(value, "%Y-%m-%d").date()
    
    def extract(self):
        # Read json files 
        print(f" Reading From: {self.redcap_folder}")
        
        try:
            logger.info('Extracting Patients...')
            self._extract_patients()
            
            logger.info('Extracting Diagnoses...')
            self._extract_diagnoses()
            
            # Extract Treatments (and create treatment regimens)
            logger.info("Extracting treatments...")
            self._extract_treatments()
        
            logger.info('Extracting Labs...')
            self._extract_labs()
            
            logger.info('Extracting Visits...')
            self._extract_visits()
            
            logger.info('Extracting Adverse Events...')
            self._extract_adverse_events()        
            
            logger.info("Extraction complete")
                    
        except FileNotFoundError as e:
            print(f"File not found: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"Error during extraction: {str(e)}")
            raise  
            

    def _extract_patients(self):
        # Read Patients
        with open(f'{self.redcap_folder}/patients.json','r') as f:
            patients = json.load(f)
        for patient in patients:
            self.persons_data.append({
                'source_id' : patient['record_id'],
                'gender' : patient['gender'],
                'year_of_birth': int(patient['date_of_birth'].split('-')[0]),
                'month_of_birth' : int(patient['date_of_birth'].split('-')[1]),
                'day_of_birth' : int(patient['date_of_birth'].split('-')[2]),
            })
         
    def _extract_diagnoses(self):
    #Read Diagnosis
        with open(f'{self.redcap_folder}/diagnoses.json','r') as f:
            diagnoses = json.load(f)
                
        for diagnosis in diagnoses:
            condition_date = self._parse_date(diagnosis['diagnosis_date'])
            self.conditions_data.append({
                'person_source_id': diagnosis['record_id'],
                'condition_code' : diagnosis['cancer_type_code'],
                'condition_name' : diagnosis['cancer_type_name'],
                'condition_date' : condition_date,
                })
            self.tumor_profiles_data.append({
                'person_source_id' : diagnosis['record_id'],
                'diagnosis_date' : condition_date,
                'stage' : diagnosis.get('cancer_stage', ""),
                'histology' : diagnosis.get('cancer_histology', ""),
                'mutation_status': diagnosis.get('mutation_status',""),
            })
    
    def _extract_treatments(self):
        with open(f'{self.redcap_folder}/treatments.json','r') as f:
            treatments = json.load(f)
                
        for treatment in treatments:
            
            start_date = self._parse_date(treatment['treatment_start_date'])
            end_date = self._parse_date(treatment.get('treatment_end_date'))
            
            # Extract each drug from treatment
            drug_names = []
            drug_num = 1
            while f'drug_{drug_num}_name' in treatment:
                drug_names.append(treatment[f'drug_{drug_num}_name'])
                
                #OMOP DrugExposure
                self.medications_data.append({
                    'person_source_id': treatment['record_id'],
                    'drug_code' : treatment.get(
                        f'drug_{drug_num}_code',
                        treatment[f'drug_{drug_num}_name'].lower()
                    ),
                        'drug_name' : treatment[f'drug_{drug_num}_name'],
                        'drug_start_date': start_date,
                        'drug_end_date': end_date,
                        'quantity': treatment.get(f'drug_{drug_num}_dose'),
                })
                drug_num +=1
            
            # Cancer-specific: Treatment Regimen
            self.treatment_regimens_data.append({
                'person_source_id' : treatment['record_id'],
                'regimen_name' : ' + '.join(drug_names),
                'start_date' : start_date,
                'end_date' : end_date,
                'best_response' : treatment.get('treatment_response'),
                'completed_cycles' : treatment.get('completed_cycles',0),
            })
    
    def _extract_labs(self):
        # Read Labs
        with open(f'{self.redcap_folder}/labs.json','r') as f:
            labs = json.load(f);
            
        for lab in labs:
            self.measurements_data.append({
                    'person_source_id' : lab['record_id'],
                    'measurement_code' : lab['lab_code'],
                    'measurement_name' : lab['lab_name'],
                    'measurement_date' : self._parse_date(lab['lab_date']),
                    'value' : float(lab['lab_result']),
                    'unit' : lab.get('lab_unit','Unknown'),
                })
    
    def _extract_visits(self):
        #Read Visits
        with open(f'{self.redcap_folder}/visits.json','r') as f:
            visits = json.load(f)
                
        for visit in visits:
            self.visits_data.append({
                    'person_source_id' : visit['record_id'],
                    'visit_type' : visit['visit_type'],
                    'visit_date' : self._parse_date(visit['visit_date']), 
                })
    
    def _extract_adverse_events(self):
        with open(f'{self.redcap_folder}/adverse_events.json','r') as f:
            adverse_events  = json.load(f)
            
        for ae in adverse_events:
            #Cancer Specific
            self.adverse_events_data.append({
                'person_source_id': ae['record_id'],
                'event_name': ae['ae_event_name'],
                'event_date': self._parse_date(ae['ae_date']),
                'grade': ae['ae_grade'],
                'treatment_start_date': self._parse_date(ae.get('treatment_start_date')),
            })
 
    
                        
                        

          
        
                
                    
            
        