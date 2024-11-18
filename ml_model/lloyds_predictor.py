import joblib
import pickle
import os
import pandas as pd
import numpy as np

from ml_model.list_ import state_dict
from typing import List
from fastapi import HTTPException

####################################################################
####################################################################

## Import ML model, Encoder and MinMax scaler
def import_model(path_dir):
    try:
        # # Get the directory of the current script
        # script_dir = os.path.dirname(os.path.abspath(__file__))
        # # Construct the full path to the model file
        # model_path = os.path.join(script_dir, 'pkl_files', path_dir)
        model_path = f"ml_model/pkl_files/{path_dir}"
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Model files not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model files: {e}")
    
####################################################################
####################################################################

## Calculate 12-18 Month Runway
def cal_runway(financial):
    try:
        current_assets = financial['current_assets']
        current_liabilities = financial['current_liabilities']
        net_income_loss = financial['net_income_loss']

        if (current_assets * 1.5) > current_liabilities:
            print("Runway: True")
            return True
        
        elif (current_assets * 1.5) > (current_liabilities + abs(net_income_loss)):
            print("Runway: False")
            return False
        
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing financial key: {e}")
        


## Financial calculations
def cal_financials(financial):
    try:
        current_assets = financial['current_assets']
        current_liabilities = financial['current_liabilities']
        total_assets = financial['total_assets']
        total_liabilities = financial['total_liabilities']

        working_capital = current_assets - current_liabilities
        book_value_equity = total_assets - total_liabilities

        debt_to_equity_ratio = 0 if book_value_equity == 0 else total_liabilities / (-book_value_equity)
        return working_capital, book_value_equity, debt_to_equity_ratio
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing financial key: {e}")
    
    
## Convert Streamlit select box varables to list
def generate_coverage_combinations(selected_coverages: List[str]) -> List[str]:
    # Define the order for sorting
    order = {"D": 0, "E": 1, "F": 2}
    # Sort selected coverages
    sorted_coverages = sorted(selected_coverages, key=lambda x: order[x])
    # Join sorted coverages into a single comma-separated string
    return [",".join(sorted_coverages)] if sorted_coverages else []


####################################################################
####################################################################

### Create Dictionary from Variables
def create_data_dict(applicant, financial):

    try:

        working_capital, book_value_equity, debt_to_equity_ratio = cal_financials(financial)

        data ={
                'NAICS/NOPS' : applicant['naics'],
                'Zip Code' : applicant['zipcode'],
                'State' : applicant['state'].name,
                'Coverage(s)' : generate_coverage_combinations(financial['coverage'])[0], #

                'NAML Eligible?' : financial['NAML_eligible'].name,
                'Total Claims $ L3Y' : financial['total_claims'], ###

                'Most Recent Year End Current Assets' : financial['current_assets'],
                'Most Recent Year End Total Assets' : financial['total_assets'],
                'Most Recent Year End Current Liabilities' : financial['current_liabilities'],
                'Most Recent Year End Total Liabilities' : financial['total_liabilities'],
                'Most Recent Year End Working Capital':working_capital, 

                'Most Recent Year End Retained Earnings' : financial['retained_earning'], ###
                'Most Recent Year End EBIT' : financial['end_ebit'], ###

                'Book Value of Equity':book_value_equity, 
                'Most Recent Year End Revenue' : financial['revenue'], #
                'Most Recent Year End Net Income/Loss' : financial['net_income_loss'],
                'Total Employee Count' : financial['employee_count'],
                'Debt to Equity Ratio':debt_to_equity_ratio,             
                '12-18 Months Runway?' : cal_runway(financial), #

        }
        # print(data)

        return data
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing key in applicant or financial data: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating DataFrame: {e}")
    
## Create the Data Frame
def create_df(data):
    try:
        # Convert dictionary to DataFrame
        X_test_df = pd.DataFrame([data])
        print("SUCCESS : DataFrame is Created")

        currnt_drop_columns = ['Total Claims $ L3Y', 
                            'Most Recent Year End Current Assets', 'Most Recent Year End Current Liabilities',
                            'Most Recent Year End Total Assets', 'Most Recent Year End Total Liabilities',
                            'Most Recent Year End Retained Earnings', 'Most Recent Year End EBIT',
                            'Most Recent Year End Revenue', '12-18 Months Runway?', 'Coverage(s)',
                            ]
        X_test_df_final = X_test_df.drop(currnt_drop_columns, axis=1)
        return X_test_df_final
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing key in applicant or financial data: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating DataFrame: {e}")


## State mapping
def map_state_zipcode(df):
    try:
        df['State'] = df['State'].map(state_dict)
        df['Zip Code'] = (df['State'].astype(str) + df['Zip Code'].astype(str).str.zfill(5)).astype(int)
        print("SUCCESS : State is mapped to Zip Code")
        return df.drop('State', axis=1)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"State mapping error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in mapping state to zip code: {e}")

## Label encoding and MinMax Scaling
def feature_engineering(df, le, sc):
    try:

        le_col = 'NAML Eligible?'
        df[le_col] = le[le_col].transform(df[le_col])
        # Convert 'NAICS/NOPS' to int
        df['NAICS/NOPS'] = df['NAICS/NOPS'].astype(int)
        df2 = sc.transform(df)
        df3 = pd.DataFrame(df2, columns=df.columns)
        print("SUCCESS : Data is Scaled")
        return df3
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Encoding error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in feature engineering: {e}")



# Payload handling
def payload_handle(payload):
    try:
        applicant = payload['applicant']
        # NAML_eligible = payload['NAML_eligible'].name
        financial = payload['financial']
        # employee = payload['employee']
        broker = payload['broker']

        return applicant, financial, broker
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Payload missing key: {e}")

####################################################################
####################################################################

# Model prediction function
def model(payload):
    try:
        ## import models
        le = import_model('label_encoder.sav')
        sc = import_model('scaler.sav')
        lloyd_model = import_model('Lloyd_model.sav')

        applicant, financial, broker = payload_handle(payload)
        df_dict = create_data_dict(applicant, financial)
        df1 = create_df(df_dict)
        df2 = map_state_zipcode(df1)
        df3 = feature_engineering(df2, le, sc)
        ## Prediction
        y_test_pred = lloyd_model.predict(df3)
        return "ACCEPT" if y_test_pred == 1 else "REJECT"
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in prediction model: {e}")

####################################################################
####################################################################

def check_naml_eligibility(applicant, financial, claims):

    naics = applicant['naics']
    revenue = financial['revenue']
    employee_count = financial['employee_count']
    coverage = generate_coverage_combinations(financial['coverage'])[0] ## D,E,F
    state = applicant['state'].name

    # claims_amount = 
    ## last 3 policy periods, or last 3 calendar years from the date we received the submission
    paid_claims = financial['total_claims']
    do_claims = claims['']
    epl_claims = claims['']
    fid_claims = claims['']
    total_claims = claims[''] ## claims for the entire account

    not_cover_naics = []
    
          
    # Check revenue limit
    if revenue > 300000000 and not (coverage == "E" and employee_count <= 300):
        return False

    # Check employee count limit
    if employee_count > 300 and not (coverage == "D" and revenue <= 300000000):
        return False

    # Check standalone CA EPL restriction
    if state == "CA" and coverage == "E":
        return False

    # Check claims restrictions
    # if claims_amount:
    if paid_claims > 250000:
        return False
    if do_claims >= 3:
        return False
    if epl_claims >= 3:
        return False
    if fid_claims >= 3:
        return False
    if total_claims >= 5:
        return False

    if naics in ['']:
        return False
    

    return True
