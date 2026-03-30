import logging
import requests

logger = logging.getLogger(__name__)

# The base URL where your server is running.
# Change this if running on a different port or host.
BASE_URL = "http://localhost:8081"

# ---------------------------------------------------------
# Test Data Constants
# ---------------------------------------------------------
TEST_SOLVENT = "CCO"  # Ethanol
TEST_SOLUTE = "CC(=O)O" # Acetic Acid

# ---------------------------------------------------------
# Tests for DirectML and SoluteML Estimators
# ---------------------------------------------------------

def test_dGsolv_estimator_success():
    payload = {
        "solvent_smiles": TEST_SOLVENT,
        "solute_smiles": TEST_SOLUTE
    }
    
    response = requests.post(f"{BASE_URL}/dGsolv_estimator", json=payload)
    
    # Verify the HTTP response
    assert response.status_code == 200
    
    # Verify the JSON payload structure
    data = response.json()
    assert "avg_pred" in data
    assert "epi_unc" in data
    assert "valid_indices" in data


def test_dHsolv_estimator_success():
    payload = {
        "solvent_smiles": TEST_SOLVENT,
        "solute_smiles": TEST_SOLUTE
    }
    
    response = requests.post(f"{BASE_URL}/dHsolv_estimator", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    assert "avg_pred" in data
    assert "epi_unc" in data
    assert "valid_indices" in data


def test_SoluteML_estimator_success():
    payload = {
        "solute_smiles": TEST_SOLUTE
    }
    
    response = requests.post(f"{BASE_URL}/SoluteML_estimator", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    assert "avg_pred" in data
    assert "epi_unc" in data
    assert "valid_indices" in data


def test_invalid_payload_fails():
    # Sending a bad type (like string instead of float for temperature)
    # should raise a 422 Unprocessable Entity from Pydantic
    payload = {
        "temperature": "not_a_number"
    }
    response = requests.post(f"{BASE_URL}/dGsolv_estimator", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------
# Tests for the Solubility Calculators
# ---------------------------------------------------------

def test_calc_solubility_no_ref():
    payload = {
        "solvent_smiles": TEST_SOLVENT,
        "solute_smiles": TEST_SOLUTE,
        "temperature": 298.15
    }
    
    response = requests.post(f"{BASE_URL}/calc_solubility_no_ref", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    
    # based on the previous version from rmg.mit.edu
    assert round(data["logsT_method1"], 3) == 1.146
    assert round(data["logsT_method2"], 3) == 1.146
    assert round(data["gsolv_T"], 2) == -7.12
    assert round(data["hsolv_T"], 2) == -12.08
    assert round(data["ssolv_T"] * 1000, 2) == -16.62
    assert round(data["hsubl_298"], 2) == 14.86
    assert round(data["Cp_gas"], 2) == 15.93
    assert round(data["Cp_solid"], 2) == 22.18


def test_calc_solubility_with_ref():
    payload = {
        "solvent_smiles": TEST_SOLVENT,
        "solute_smiles": TEST_SOLUTE,
        "temperature": 298.15,
        "reference_solvent": "O", # Water
        "reference_solubility": -1.5
    }
    
    response = requests.post(f"{BASE_URL}/calc_solubility_with_ref", json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    assert round(data["logsT_method1"], 3) == -1.223
    assert round(data["logsT_method2"], 3) == -1.223
    assert round(data["gsolv_T"], 2) == -7.12
    assert round(data["hsolv_T"], 2) == -12.08
    assert round(data["ssolv_T"] * 1000, 2) == -16.62
    assert round(data["hsubl_298"], 2) == 14.86
    assert round(data["Cp_gas"], 2) == 15.93
    assert round(data["Cp_solid"], 2) == 22.18

if __name__ == "__main__":
    test_dGsolv_estimator_success()
    test_dHsolv_estimator_success()
    test_SoluteML_estimator_success()
    test_invalid_payload_fails()
    test_calc_solubility_no_ref()
    test_calc_solubility_with_ref()
    logger.info("All tests passed!")
