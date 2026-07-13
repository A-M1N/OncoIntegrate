# backend/mock_redcap_data/generate_mock_data.py

import json
import os
from datetime import datetime, timedelta
import random

def generate_mock_redcap_data(num_patients=50):
    """
    Generate realistic mock REDCap eCRF data for cancer trials
    Matches structure of what VHIO research teams use
    """
    
    print(f"Generating mock REDCap eCRF data for {num_patients} cancer patients...")
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ============================================
    # FORM 1: PATIENT DEMOGRAPHICS
    # ============================================
    
    patients = []
    patient_ids = [f"PATIENT_{str(i).zfill(4)}" for i in range(1, num_patients + 1)]
    
    for patient_id in patient_ids:
        birth_year = random.randint(1940, 2000)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        patients.append({
            'record_id': patient_id,
            'redcap_event_name': 'baseline_arm_1',
            'patient_initials': ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(2)),
            'date_of_birth': f"{birth_year}-{birth_month:02d}-{birth_day:02d}",
            'gender': random.choice(['Male', 'Female']),
            'race': random.choice(['White', 'Black', 'Asian', 'Other']),
            'ethnicity': random.choice(['Hispanic or Latino', 'Not Hispanic or Latino', 'Unknown']),
            'site': random.choice(['Hospital A', 'Hospital B', 'Hospital C'])
        })
    
    # ============================================
    # FORM 2: CANCER DIAGNOSIS (eCRF Form 1)
    # ============================================
    
    diagnoses = []
    cancer_types = [
        ('C34.9', 'Lung Cancer', ['Adenocarcinoma', 'Squamous Cell', 'Small Cell']),
        ('C50.9', 'Breast Cancer', ['Invasive Ductal', 'Invasive Lobular']),
        ('C34.1', 'Upper Lobe Lung Cancer', ['Adenocarcinoma']),
    ]
    
    for patient in patients:
        cancer_type_code, cancer_type_name, histologies = random.choice(cancer_types)
        diagnosis_date = datetime.now() - timedelta(days=random.randint(180, 730))
        
        diagnoses.append({
            'record_id': patient['record_id'],
            'redcap_event_name': 'baseline_arm_1',
            'diagnosis_date': diagnosis_date.strftime('%Y-%m-%d'),
            'cancer_type_code': cancer_type_code,
            'cancer_type_name': cancer_type_name,
            'cancer_stage': random.choice(['I', 'II', 'III', 'IV']),
            'cancer_stage_detail': random.choice(['A', 'B', 'C']),
            'cancer_histology': random.choice(histologies),
            'ecog_status': random.choice(['0', '1', '2']),
            'mutation_status': random.choice(['EGFR+', 'KRAS+', 'ALK+', 'Wild-type', 'Unknown']),
            'tumor_marker_cea': round(random.uniform(0.5, 10.0), 2),
            'clinical_notes': 'Patient enrolled in clinical trial'
        })
    
    # ============================================
    # FORM 3: TREATMENT (REPEATING FORM)
    # ============================================
    
    treatments = []
    treatment_options = [
        ('Pemetrexed', '500', 'mg'),
        ('Carboplatin', '300', 'mg'),
        ('Nivolumab', '240', 'mg'),
        ('Pembrolizumab', '200', 'mg'),
    ]
    
    # Store treatment info for linking visits/labs later
    treatment_map = {}  # {patient_id: [treatment_dates]}
    
    for i, patient in enumerate(diagnoses):
        patient_id = patient['record_id']
        diagnosis_date = datetime.strptime(patient['diagnosis_date'], '%Y-%m-%d')
        treatment_map[patient_id] = []
        
        # Each patient has 1-2 treatment regimens
        for regimen_num in range(1, random.randint(1, 3)):
            # Treatment starts 2-4 weeks after diagnosis
            days_after_diagnosis = random.randint(14, 28) + (regimen_num - 1) * 150
            treatment_start = diagnosis_date + timedelta(days=days_after_diagnosis)
            treatment_duration = random.randint(60, 180)  # weeks of treatment
            treatment_end = treatment_start + timedelta(days=treatment_duration)
            
            treatment_map[patient_id].append({
                'start': treatment_start,
                'end': treatment_end,
                'instance': regimen_num
            })
            
            # Combine 1-2 drugs per regimen
            num_drugs = random.randint(1, 2)
            selected_drugs = random.sample(treatment_options, num_drugs)
            
            treatment_entry = {
                'record_id': patient_id,
                'redcap_event_name': f'treatment_{regimen_num}_arm_1',
                'redcap_repeat_instrument': 'treatment_log',
                'redcap_repeat_instance': regimen_num,
                'treatment_start_date': treatment_start.strftime('%Y-%m-%d'),
                'treatment_end_date': treatment_end.strftime('%Y-%m-%d'),
                'treatment_intent': random.choice(['Curative', 'Palliative']),
                'planned_cycles': 4,
                'completed_cycles': random.randint(1, 4),
                'treatment_response': random.choice(['CR', 'PR', 'SD', 'PD']),
            }
            
            # Add drugs
            for drug_num, (drug_name, dose, unit) in enumerate(selected_drugs, 1):
                treatment_entry[f'drug_{drug_num}_name'] = drug_name
                treatment_entry[f'drug_{drug_num}_code'] = drug_name.lower().replace(' ', '_')
                treatment_entry[f'drug_{drug_num}_dose'] = dose
                treatment_entry[f'drug_{drug_num}_unit'] = unit
            
            treatments.append(treatment_entry)
    
    # ============================================
    # FORM 4: VISITS (NEW!)
    # ============================================
    
    visits = []
    visit_types = ['Baseline Visit', 'Cycle Day 1', 'Cycle Day 8', 'Cycle Day 15', 'Follow-up']
    
    for patient_id, treatment_list in treatment_map.items():
        patient = next((p for p in patients if p['record_id'] == patient_id), None)
        if not patient:
            continue
        
        # Baseline visit at diagnosis
        diagnosis = next((d for d in diagnoses if d['record_id'] == patient_id), None)
        baseline_date = datetime.strptime(diagnosis['diagnosis_date'], '%Y-%m-%d')
        
        visits.append({
            'record_id': patient_id,
            'redcap_event_name': 'baseline_arm_1',
            'redcap_repeat_instrument': 'visit_log',
            'redcap_repeat_instance': 1,
            'visit_date': baseline_date.strftime('%Y-%m-%d'),
            'visit_type': 'Baseline Visit',
            'visit_location': patient['site'],
            'ecog_performance': diagnosis['ecog_status'],
            'weight_kg': round(random.uniform(50, 100), 1),
            'height_cm': round(random.uniform(150, 190), 1),
        })
        
        # Visits during treatment (every 2 weeks)
        visit_instance = 2
        for treatment in treatment_list:
            treatment_start = treatment['start']
            treatment_end = treatment['end']
            
            # Create visits every 14 days during treatment
            current_date = treatment_start
            while current_date <= treatment_end:
                visits.append({
                    'record_id': patient_id,
                    'redcap_event_name': f'treatment_{treatment["instance"]}_arm_1',
                    'redcap_repeat_instrument': 'visit_log',
                    'redcap_repeat_instance': visit_instance,
                    'visit_date': current_date.strftime('%Y-%m-%d'),
                    'visit_type': random.choice(['Cycle Day 1', 'Cycle Day 8', 'Cycle Day 15']),
                    'visit_location': patient['site'],
                    'ecog_performance': random.choice(['0', '1', '2']),
                    'weight_kg': round(random.uniform(48, 102), 1),
                    'height_cm': round(random.uniform(150, 190), 1),
                })
                current_date += timedelta(days=14)
                visit_instance += 1
        
        # Follow-up visits after treatment (monthly for 6 months)
        if treatment_list:
            last_treatment_end = treatment_list[-1]['end']
            followup_date = last_treatment_end + timedelta(days=30)
            
            for month in range(1, 7):
                visits.append({
                    'record_id': patient_id,
                    'redcap_event_name': 'followup_arm_1',
                    'redcap_repeat_instrument': 'visit_log',
                    'redcap_repeat_instance': visit_instance,
                    'visit_date': followup_date.strftime('%Y-%m-%d'),
                    'visit_type': 'Follow-up',
                    'visit_location': patient['site'],
                    'ecog_performance': random.choice(['0', '1', '2']),
                    'weight_kg': round(random.uniform(48, 102), 1),
                    'height_cm': round(random.uniform(150, 190), 1),
                })
                followup_date += timedelta(days=30)
                visit_instance += 1
    
    # ============================================
    # FORM 5: LAB RESULTS (REPEATING FORM)
    # ============================================
    
    labs = []
    lab_tests = [
        ('2160-0', 'Creatinine', 'mg/dL', 0.7, 1.3),
        ('718-7', 'Hemoglobin', 'g/dL', 12.0, 16.0),
        ('777-3', 'Platelet Count', '10^9/L', 150, 400),
        ('6690-2', 'WBC Count', '10^9/L', 4.5, 11.0),
        ('1975-2', 'Total Bilirubin', 'mg/dL', 0.1, 1.2),
    ]
    
    for patient_id, treatment_list in treatment_map.items():
        diagnosis = next((d for d in diagnoses if d['record_id'] == patient_id), None)
        baseline_date = datetime.strptime(diagnosis['diagnosis_date'], '%Y-%m-%d')
        
        lab_instance = 1
        
        # Baseline labs
        for lab_code, lab_name, unit, normal_low, normal_high in lab_tests:
            labs.append({
                'record_id': patient_id,
                'redcap_event_name': 'baseline_arm_1',
                'redcap_repeat_instrument': 'lab_results',
                'redcap_repeat_instance': lab_instance,
                'lab_date': baseline_date.strftime('%Y-%m-%d'),
                'lab_code': lab_code,
                'lab_name': lab_name,
                'lab_result': round(random.uniform(normal_low, normal_high), 2),
                'lab_unit': unit,
                'lab_normal_low': normal_low,
                'lab_normal_high': normal_high,
            })
            lab_instance += 1
        
        # Labs during treatment (every 2 weeks, often abnormal)
        for treatment in treatment_list:
            lab_date = treatment['start']
            
            while lab_date <= treatment['end']:
                for lab_code, lab_name, unit, normal_low, normal_high in lab_tests:
                    # 40% chance of abnormal during chemo
                    if random.random() > 0.6:
                        value = round(random.uniform(normal_low * 0.4, normal_high * 1.4), 2)
                    else:
                        value = round(random.uniform(normal_low, normal_high), 2)
                    
                    labs.append({
                        'record_id': patient_id,
                        'redcap_event_name': f'treatment_{treatment["instance"]}_arm_1',
                        'redcap_repeat_instrument': 'lab_results',
                        'redcap_repeat_instance': lab_instance,
                        'lab_date': lab_date.strftime('%Y-%m-%d'),
                        'lab_code': lab_code,
                        'lab_name': lab_name,
                        'lab_result': value,
                        'lab_unit': unit,
                        'lab_normal_low': normal_low,
                        'lab_normal_high': normal_high,
                    })
                    lab_instance += 1
                
                lab_date += timedelta(days=14)
    
    # ============================================
    # FORM 6: ADVERSE EVENTS (REPEATING FORM)
    # ============================================
    
    adverse_events = []
    ae_list = [
        'Neuropathy',
        'Nausea/Vomiting',
        'Fatigue',
        'Anemia',
        'Neutropenia',
        'Diarrhea',
        'Elevated Liver Enzymes'
    ]
    
    for patient_id, treatment_list in treatment_map.items():
        ae_instance = 1
        
        # Each patient has 0-4 adverse events during treatment
        for treatment in treatment_list:
            num_aes = random.randint(0, 4)
            
            for _ in range(num_aes):
                ae_date = treatment['start'] + timedelta(
                    days=random.randint(7, int((treatment['end'] - treatment['start']).days))
                )
                
                adverse_events.append({
                    'record_id': patient_id,
                    'redcap_event_name': f'treatment_{treatment["instance"]}_arm_1',
                    'redcap_repeat_instrument': 'adverse_events',
                    'redcap_repeat_instance': ae_instance,
                    'ae_date': ae_date.strftime('%Y-%m-%d'),
                    'ae_event_name': random.choice(ae_list),
                    'ae_grade': random.choice(['1', '2', '3', '4']),
                    'ae_relationship': random.choice(['Related', 'Possibly Related', 'Not Related']),
                    'ae_action_taken': random.choice(['None', 'Dose Reduction', 'Discontinuation']),
                    'ae_outcome': random.choice(['Resolved', 'Ongoing', 'Unknown']),
                    'treatment_start_date': treatment['start'].strftime('%Y-%m-%d'),
                })
                ae_instance += 1
    
    # ============================================
    # SAVE TO JSON FILES
    # ============================================
    
    files_created = {
        'patients.json': patients,
        'diagnoses.json': diagnoses,
        'treatments.json': treatments,
        'visits.json': visits,  # ✅ NEW!
        'labs.json': labs,
        'adverse_events.json': adverse_events,
    }
    
    for filename, data in files_created.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Generated {filename}: {len(data)} records")
    
    print(f"\n✅ All cancer eCRF data saved to {output_dir}/")
    print("\nDataset Summary:")
    print(f"  - Patients: {len(patients)}")
    print(f"  - Diagnoses: {len(diagnoses)}")
    print(f"  - Treatments: {len(treatments)}")
    print(f"  - Visits: {len(visits)}")
    print(f"  - Lab Results: {len(labs)}")
    print(f"  - Adverse Events: {len(adverse_events)}")


if __name__ == "__main__":
    generate_mock_redcap_data(50)  