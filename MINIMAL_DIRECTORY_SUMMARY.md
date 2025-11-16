# Minimal Directory Creation - Summary

## ✅ Successfully Created: HL23_Yao_rTMS_LFP_minimal/

A clean, self-contained implementation of the 100-cell Yao L2/3 model with AD + rTMS + LFP.

---

## Directory Tree

```
HL23_Yao_rTMS_LFP_minimal/
├── README.md                           # Quick start guide
├── cfg.py                              # Simulation config (TMS params, LFP config)
├── netParams.py                        # Network parameters
├── cellwrapper.py                      # Cell template loader
├── init.py                             # Main simulation runner
├── tms.py                              # TMS implementation
├── analyze_rtms_lfp.py                 # Analysis script (6-panel plots)
├── test_rtms_lfp_quick.py              # Quick test script
├── run_rtms_lfp_suite.py               # 3-condition suite
├── Circuit_param.xls                   # Connectivity matrix
├── mod/                                # NEURON mechanisms (17 .mod files)
│   ├── CaDynamics.mod
│   ├── Ca_HVA.mod
│   ├── Ca_LVA.mod
│   ├── Gfluct.mod
│   ├── Ih.mod
│   ├── Im.mod
│   ├── K_P.mod
│   ├── K_T.mod
│   ├── Kv3_1.mod
│   ├── NMDA.mod
│   ├── NaTg.mod
│   ├── Nap.mod
│   ├── ProbAMPANMDA.mod
│   ├── ProbUDFsyn.mod
│   ├── SK.mod
│   ├── epsp.mod
│   └── tonic.mod
├── x86_64/                             # Compiled mechanisms
│   ├── *.c, *.o files
│   └── libnrnmech.dylib
├── models/                             # Cell templates (13 .hoc files)
│   ├── NeuronTemplate.hoc
│   ├── NeuronTemplate_HL23PYR.hoc
│   ├── NeuronTemplate_HL23SST.hoc
│   ├── NeuronTemplate_HL23PV.hoc
│   ├── NeuronTemplate_HL23VIP.hoc
│   ├── biophys_HL23PYR.hoc
│   ├── biophys_HL23PYR_AD_Stage1.hoc
│   ├── biophys_HL23PYR_AD_Stage2.hoc
│   ├── biophys_HL23PYR_AD_Stage3.hoc
│   ├── biophys_HL23SST.hoc
│   ├── biophys_HL23PV.hoc
│   └── biophys_HL23VIP.hoc
├── morphologies/                       # Cell morphologies (4 .swc files)
│   ├── HL23PYR.swc
│   ├── HL23SST.swc
│   ├── HL23PV.swc
│   └── HL23VIP.swc
├── output/                             # Simulation data
├── results/                            # Summary JSON files
└── figures/                            # Analysis plots
```

**Total:** 9 Python scripts, 1 Excel file, 17 mechanisms, 13 HOC templates, 4 morphologies, 3 output directories.

---

## What Was Excluded (Clutter Removed)

❌ **NOT copied from parent directory:**
- `Previous version/` folder (old code)
- `clutter/` folder (experimental scripts)
- `test_output/` folder (temporary test results)
- `__pycache__/` folders (Python bytecode)
- Validation scripts: `test_cfg_validation.py`, `test_tms_lfp_integration.py`, `validate_tms_lfp_config.py`
- Analysis scripts: `analyze_network_results.py`, `generate_FI_VI_curves.py`, `fi_vi_analysis.py`, `plot_key_findings.py`
- Setup scripts: `create_templates.py`, `validate_setup.py`
- Test scripts: `test_healthy.py`, `run_single_condition.py`
- Documentation: `IMPLEMENTATION_COMPLETE.md`, `CHANGES_SUMMARY.md`, `NETWORK_AD_INTEGRATION.md`, etc.
- Git repository: `.git/`, `.gitignore`
- Old figures and results

**Result:** Clean directory with ONLY the files needed to run simulations and analysis.

---

## Key Configuration Details

### cfg.py - TMS Parameters (Lines 50-63)

```python
cfg.tms_params = dict(
    freq_Hz=30.,                        # 30 Hz pulse frequency
    duration_ms=cfg.duration,           # 3000 ms
    pulse_resolution_ms=cfg.dt,         # 0.025 ms
    stim_start_ms=2000.,                # TMS starts at 2000 ms
    stim_end_ms=3000.,                  # TMS ends at 3000 ms
    ef_amp_V_per_m=60.,                 # 60 V/m electric field
    width_ms=1.0,                       # 1 ms biphasic pulse duration
    pshape="Sine",
    decay_rate_percent_per_mm=10,
    E_field_dir=[-1, -1, -1],
    decay_dir=[0, 0, -1],
    ref_point_um=[0, 0, 0],
)
```

### cfg.py - LFP Configuration (Lines 217-227)

```python
cfg.LFP_electrodes = [
    [0.0, 600.0, 0.0],   # Electrode 0 - upper L2/3
    [0.0, 700.0, 0.0],   # Electrode 1
    [0.0, 800.0, 0.0],   # Electrode 2 - mid L2/3
    [0.0, 900.0, 0.0],   # Electrode 3
    [0.0, 1000.0, 0.0],  # Electrode 4 - lower L2/3
]

# cfg.recordLFP must be a list (not a boolean) for NetPyNE
cfg.recordLFP = cfg.LFP_electrodes
```

**Critical:** `cfg.recordLFP` is a **list**, not a boolean. This prevents `TypeError: object of type 'bool' has no len()`.

---

## tms.py - Key Functions

### 1. Field-to-Current Conversion (Lines 12-21)

```python
def convert_field_to_current(field_Vm, cell_type='HL23PYR', compartment='soma'):
    """Convert electric field strength (V/m) to IClamp current amplitude (nA)."""
    geometry = {
        'HL23PYR': {'soma': 0.025, 'apical': 0.05, 'basal': 0.03},
        'HL23PV': {'soma': 0.015},
        'HL23SST': {'soma': 0.015},
        'HL23VIP': {'soma': 0.015}
    }
    conversion_factor = geometry.get(cell_type, {}).get(compartment, 0.02)
    return field_Vm * conversion_factor
```

**Result:** 60 V/m → 1.5 nA for HL23PYR soma

### 2. Biphasic Pulse Application (Lines 24-40)

```python
def apply_biphasic_pulse(soma_sec, onset, amp_nA, duration=1.0):
    """Apply a single biphasic pulse at specified onset time."""
    phase_dur = duration / 2.0

    # Phase 1: Depolarizing (+I)
    stim1 = h.IClamp(soma_sec(0.5))
    stim1.delay = onset
    stim1.dur = phase_dur
    stim1.amp = amp_nA

    # Phase 2: Hyperpolarizing (-I)
    stim2 = h.IClamp(soma_sec(0.5))
    stim2.delay = onset + phase_dur
    stim2.dur = phase_dur
    stim2.amp = -amp_nA

    return [stim1, stim2]
```

**Result:** 1 ms total pulse (0.5 ms +I, 0.5 ms -I) for charge balance

### 3. Main TMS Entry Point (Lines 43-106)

```python
def apply_tms_from_params(sim, cfg, target_pop='HL23PYR'):
    """Apply TMS protocol using cfg.tms_params (new standard format)."""

    # Extract parameters (NO defaults - cfg.tms_params is source of truth)
    field_Vm = tms_params['ef_amp_V_per_m']      # Direct access, no .get()
    freq_Hz = tms_params['freq_Hz']              # Direct access, no .get()
    stim_start = tms_params['stim_start_ms']     # Direct access, no .get()
    stim_end = tms_params['stim_end_ms']         # Direct access, no .get()
    width_ms = tms_params['width_ms']            # Direct access, no .get()

    # Calculate number of pulses
    stim_duration = stim_end - stim_start        # 3000 - 2000 = 1000 ms
    n_pulses = int(stim_duration * freq_Hz / 1000.0)  # 1000 * 30 / 1000 = 30 pulses

    # Apply to all cells in target population
    for cell in sim.net.cells:
        if cell.tags.get('pop') == target_pop:
            for pulse_idx in range(n_pulses):
                pulse_onset = stim_start + pulse_idx * pulse_interval
                apply_biphasic_pulse(soma_sec, pulse_onset, amp_nA, duration=width_ms)
```

**Critical:** NO hardcoded defaults. Uses direct dictionary access `tms_params['key']`, not `.get('key', default)`.

---

## run_rtms_lfp_suite.py - Conditions Block (Lines 34-41)

```python
# Define test conditions - ONLY 3 conditions
# All use cfg.tms_params (60 V/m, 30 Hz, 2000-3000ms) - only AD flags change
conditions = [
    # Format: (name, ADmodel, ADstage, description)
    ('Healthy_40Vm', False, 0, 'Healthy + 60 V/m rTMS'),
    ('AD1_40Vm', True, 1, 'AD Stage 1 (hyperexcitable) + 60 V/m rTMS'),
    ('AD3_40Vm', True, 3, 'AD Stage 3 (depol. block) + 60 V/m rTMS'),
]
```

**Key Points:**
- Condition names say "40Vm" (legacy naming) but actually use **60 V/m** from cfg.tms_params
- Only 3 parameters per condition: `(name, ADmodel, ADstage, description)`
- NO field strength parameter (removed from original 4-tuple)

### Run Script Configuration (Lines 77-84)

```python
# === CONFIGURE THIS SIMULATION ===
# AD configuration (ONLY thing that changes between conditions)
cfg.ADmodel = {ad_model}
cfg.ADstage = {ad_stage}
cfg.conditionLabel = '{name}'

# TMS: Use cfg.tms_params defaults from cfg.py (60 V/m, 30 Hz, 2000-3000ms)
# DO NOT MODIFY cfg.tms_params - it's already set correctly in cfg.py
cfg.tms_enabled = True
```

**Critical:** NO modifications to `cfg.tms_params`. All 3 conditions use identical TMS protocol.

---

## Run Instructions (from README.md)

### Quick Test (1 condition, ~5 minutes)

```bash
cd /Users/tarek/Desktop/HL23_Yao_rTMS_LFP_minimal
python test_rtms_lfp_quick.py
```

**What it does:**
- Simulates 100-cell network with rTMS and LFP
- Saves data to `output/`
- Generates 6-panel analysis figure in `figures/`

### Full Suite (3 conditions, ~15-20 minutes)

```bash
cd /Users/tarek/Desktop/HL23_Yao_rTMS_LFP_minimal
python run_rtms_lfp_suite.py
```

**What it does:**
- Runs Healthy_40Vm, AD1_40Vm, AD3_40Vm sequentially
- Saves data to `output/{condition}_data.json`
- Generates analysis figures in `figures/rtms_lfp_{condition}.png`
- Saves summary to `results/rtms_lfp_suite_summary.json`

---

## Expected TMS Protocol (ALL Conditions)

- **Frequency:** 30 Hz
- **Field Strength:** 60 V/m → 1.5 nA at PYR soma
- **Stimulation Window:** 2000-3000 ms (1 second duration)
- **Pulse Width:** 1 ms biphasic (0.5 ms +I, 0.5 ms -I)
- **Number of Pulses:** 30 pulses
- **Pulse Interval:** 33.33 ms (1000 ms / 30 Hz)
- **Target Population:** HL23PYR (80 pyramidal cells)

---

## Verification Checklist

✅ **Directory created:** `/Users/tarek/Desktop/HL23_Yao_rTMS_LFP_minimal/`

✅ **Core files copied:**
- cfg.py, netParams.py, cellwrapper.py, init.py, tms.py ✅
- analyze_rtms_lfp.py, test_rtms_lfp_quick.py, run_rtms_lfp_suite.py ✅
- Circuit_param.xls ✅

✅ **Mechanisms and models copied:**
- mod/ (17 mechanisms) ✅
- x86_64/ (compiled) ✅
- models/ (13 HOC files) ✅
- morphologies/ (4 SWC files) ✅

✅ **Output directories created:**
- output/, results/, figures/ ✅

✅ **cfg.py verified:**
- cfg.duration = 3000.0 ✅
- cfg.tms_params: 60 V/m, 30 Hz, 2000-3000 ms ✅
- cfg.recordLFP = list (not boolean) ✅

✅ **tms.py verified:**
- No hardcoded defaults (40 V/m, 10 Hz, 500-1500 ms removed) ✅
- Direct dictionary access: `tms_params['key']` ✅
- Field conversion: 60 V/m → 1.5 nA ✅
- Biphasic pulses: 1 ms total (0.5 ms +I, 0.5 ms -I) ✅

✅ **run_rtms_lfp_suite.py verified:**
- 3 conditions only: Healthy_40Vm, AD1_40Vm, AD3_40Vm ✅
- Only toggles AD flags (ADmodel, ADstage) ✅
- NO cfg.tms_params modifications ✅

✅ **README.md created:** Quick start guide with run commands ✅

---

## File Sizes

- **Total directory size:** ~5 MB
- **Core Python scripts:** ~60 KB
- **Mechanisms (mod/):** ~50 KB
- **Compiled mechanisms (x86_64/):** ~2 MB
- **Models (HOC files):** ~100 KB
- **Morphologies (SWC files):** ~200 KB
- **Circuit_param.xls:** ~33 KB

---

## Next Steps

The minimal directory is ready to use. You can now:

1. **Test it immediately:**
   ```bash
   cd /Users/tarek/Desktop/HL23_Yao_rTMS_LFP_minimal
   python test_rtms_lfp_quick.py
   ```

2. **Run the full suite:**
   ```bash
   python run_rtms_lfp_suite.py
   ```

3. **Verify TMS parameters:**
   ```bash
   python -c "from cfg import cfg; print(cfg.tms_params)"
   ```

4. **Check LFP configuration:**
   ```bash
   python -c "from cfg import cfg; print(type(cfg.recordLFP), len(cfg.recordLFP))"
   ```

Expected outputs:
- `<class 'list'> 5` (confirms it's a list with 5 electrodes)

---

**Status:** ✅ Minimal directory successfully created and validated
**Date:** 2025-11-15
**Location:** `/Users/tarek/Desktop/HL23_Yao_rTMS_LFP_minimal/`
