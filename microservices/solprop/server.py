from fastapi import FastAPI
from pydantic import BaseModel
import logging
import pandas as pd
import numpy as np
from typing import Optional

from chemprop_solvation.solvation_estimator import load_DirectML_Gsolv_estimator, load_DirectML_Hsolv_estimator, load_SoluteML_estimator
from solvation_predictor.solubility.solubility_calculator import SolubilityCalculations
from solvation_predictor.solubility.solubility_predictions import SolubilityPredictions
from solvation_predictor.solubility.solubility_data import SolubilityData
from solvation_predictor.solubility.solubility_models import SolubilityModels

logger = logging.getLogger(__name__)


class SolubilityDataWrapper:
    """
    Class for storing the input data for solubility prediction
    """
    def __init__(self, solvent_smiles=None, solute_smiles=None, temp=None, ref_solub=None, ref_solv=None):
        self.smiles_pairs = [(solvent_smiles, solute_smiles)]
        self.temperatures = np.array([temp]) if temp is not None else None
        self.reference_solubility = np.array([ref_solub]) if ref_solub is not None else None
        self.reference_solvents = np.array([ref_solv]) if ref_solv is not None else None


app = FastAPI()

dGsolv_estimator = None
dHsolv_estimator = None
SoluteML_estimator = None
solub_models = None

@app.on_event("startup")
def load_models():
    global dGsolv_estimator, dHsolv_estimator, SoluteML_estimator, solub_models
    
    logger.info("Loading models...")
    
    dGsolv_estimator = load_DirectML_Gsolv_estimator()
    dHsolv_estimator = load_DirectML_Hsolv_estimator()
    
    solub_models = SolubilityModels(
        load_g=True, load_h=True,
        reduced_number=False, load_saq=True,
        load_solute=True, logger=None, verbose=False
    )
    
    SoluteML_estimator = load_SoluteML_estimator()
    
    logger.info("Models loaded.")

class SolubilityRequest(BaseModel):
    solvent_smiles: Optional[str] = None
    solute_smiles: Optional[str] = None
    temperature: Optional[float] = None
    reference_solvent: Optional[str] = None
    reference_solubility: Optional[float] = None
    hsub298: Optional[float] = None
    cp_gas_298: Optional[float] = None
    cp_solid_298: Optional[float] = None
    use_reference: bool = False
    
@app.post("/dGsolv_estimator")
def _dGsolv_estimator(req: SolubilityRequest):
    result = dGsolv_estimator([[req.solvent_smiles, req.solute_smiles]])
    return {
        "avg_pred": result[0],
        "epi_unc": result[1],
        "valid_indices": result[2]
    }

@app.post("/dHsolv_estimator")
def _dHsolv_estimator(req: SolubilityRequest):
    result = dHsolv_estimator([[req.solvent_smiles, req.solute_smiles]])
    return {
        "avg_pred": result[0],
        "epi_unc": result[1],
        "valid_indices": result[2]
    }

@app.post("/SoluteML_estimator")
def _SoluteML_estimator(req: SolubilityRequest):
    result = SoluteML_estimator([[req.solute_smiles]])
    return {
        "avg_pred": result[0],
        "epi_unc": result[1],
        "valid_indices": result[2]
    }

@app.post("/calc_solubility_no_ref")
def _calc_solubility_no_ref(req: SolubilityRequest):
    """
    Calculate solubility with no reference solvent and reference solubility
    """
    hsubl_298 = np.array([req.hsub298]) if req.hsub298 is not None else None
    Cp_solid = np.array([req.cp_solid_298]) if req.cp_solid_298 is not None else None
    Cp_gas = np.array([req.cp_gas_298]) if req.cp_gas_298 is not None else None

    solub_data = SolubilityDataWrapper(solvent_smiles=req.solvent_smiles, solute_smiles=req.solute_smiles, temp=req.temperature)
    predictions = SolubilityPredictions(solub_data, solub_models, predict_aqueous=True,
                                        predict_reference_solvents=False, predict_t_dep=True,
                                        predict_solute_parameters=True, verbose=False)
    calculations = SolubilityCalculations(predictions, calculate_aqueous=True,
                                          calculate_reference_solvents=False, calculate_t_dep=True,
                                          calculate_t_dep_with_t_dep_hdiss=True, verbose=False,
                                          hsubl_298=hsubl_298, Cp_solid=Cp_solid, Cp_gas=Cp_gas)
    
    return {
        "logsT_method1": calculations.logs_T_with_const_hdiss_from_aq[0],
        "logsT_method2": calculations.logs_T_with_T_dep_hdiss_from_aq[0],
        "gsolv_T": calculations.gsolv_T[0],
        "hsolv_T": calculations.hsolv_T[0],
        "ssolv_T": calculations.ssolv_T[0],
        "hsubl_298": calculations.hsubl_298[0],
        "Cp_gas": calculations.Cp_gas[0],
        "Cp_solid": calculations.Cp_solid[0],
        "logs_T_with_T_dep_hdiss_error_message": None if calculations.logs_T_with_T_dep_hdiss_error_message is None else calculations.logs_T_with_T_dep_hdiss_error_message[0],
    }


@app.post("/calc_solubility_with_ref")
def _calc_solubility_with_ref(req: SolubilityRequest):
    """
    Calculate solubility with a reference solvent and reference solubility
    """
    hsubl_298 = np.array([req.hsub298]) if req.hsub298 is not None else None
    Cp_solid = np.array([req.cp_solid_298]) if req.cp_solid_298 is not None else None
    Cp_gas = np.array([req.cp_gas_298]) if req.cp_gas_298 is not None else None

    solub_data = SolubilityDataWrapper(solvent_smiles=req.solvent_smiles, solute_smiles=req.solute_smiles, temp=req.temperature,
                                ref_solub=req.reference_solubility, ref_solv=req.reference_solvent)
    predictions = SolubilityPredictions(solub_data, solub_models, predict_aqueous=False,
                                        predict_reference_solvents=True, predict_t_dep=True,
                                        predict_solute_parameters=True, verbose=False)
    calculations = SolubilityCalculations(predictions, calculate_aqueous=False,
                                          calculate_reference_solvents=True, calculate_t_dep=True,
                                          calculate_t_dep_with_t_dep_hdiss=True, verbose=False,
                                          hsubl_298=hsubl_298, Cp_solid=Cp_solid, Cp_gas=Cp_gas)

    return {
        "logsT_method1": calculations.logs_T_with_const_hdiss_from_ref[0],
        "logsT_method2": calculations.logs_T_with_T_dep_hdiss_from_ref[0],
        "gsolv_T": calculations.gsolv_T[0],
        "hsolv_T": calculations.hsolv_T[0],
        "ssolv_T": calculations.ssolv_T[0],
        "hsubl_298": calculations.hsubl_298[0],
        "Cp_gas": calculations.Cp_gas[0],
        "Cp_solid": calculations.Cp_solid[0],
        "logs_T_with_T_dep_hdiss_error_message": None if calculations.logs_T_with_T_dep_hdiss_error_message is None else calculations.logs_T_with_T_dep_hdiss_error_message[0],
    }
