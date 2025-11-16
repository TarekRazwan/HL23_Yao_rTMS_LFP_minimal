# HL23 Yao rTMS + LFP - Minimal Implementation

## Overview

This is a minimal, self-contained implementation of the 100-cell human L2/3 cortical microcircuit model with:

- **Biophysics**: Yao et al. (2024) human cortical cell types (PYR, SST, PV, VIP)
- **Network**: Fernando's L2/3 connectivity matrix (Circuit_param.xls)
- **Pathophysiology**: Alzheimer's Disease (AD) stages 1-3 with hyperexcitability and depolarization block
- **Stimulation**: 30 Hz, 60 V/m repetitive TMS (rTMS) from 2000-3000 ms with 1 ms biphasic pulses
- **Recording**: 5-electrode laminar LFP array spanning L2/3 (600-1000 µm depth)

## Quick Start

### 1. Run Quick Test (Single Condition)

```bash
python test_rtms_lfp_quick.py
```

This runs a single simulation (Healthy or AD) with rTMS and LFP recording. Results saved to `output/`, `figures/`.

### 2. Run Full Suite (3 Conditions)

```bash
python run_rtms_lfp_suite.py
```

This runs all 3 conditions:
- **Healthy_40Vm**: Healthy baseline + rTMS
- **AD1_40Vm**: AD Stage 1 (hyperexcitable) + rTMS
- **AD3_40Vm**: AD Stage 3 (depolarization block) + rTMS

**Note**: Despite "40Vm" in the names (legacy naming), all conditions use **60 V/m, 30 Hz, 2000-3000 ms** as configured in `cfg.tms_params`.

## TMS Configuration

**All TMS parameters are controlled ONLY in `cfg.py` via `cfg.tms_params`:**

```python
cfg.tms_params = dict(
    freq_Hz=30.,                  # Pulse frequency: 30 Hz
    ef_amp_V_per_m=60.,           # Electric field: 60 V/m
    stim_start_ms=2000.,          # Start time: 2000 ms
    stim_end_ms=3000.,            # End time: 3000 ms
    width_ms=1.0,                 # Biphasic pulse width: 1 ms
    # ... spatial parameters
)
```

**Do NOT modify TMS parameters in `tms.py` or `run_rtms_lfp_suite.py`**. The suite script only toggles AD pathophysiology flags (`cfg.ADmodel`, `cfg.ADstage`).

## Directory Structure

```
HL23_Yao_rTMS_LFP_minimal/
├── cfg.py                      # Simulation config (TMS params, LFP config)
├── netParams.py                # Network parameters
├── cellwrapper.py              # Cell template loader
├── init.py                     # Main simulation runner
├── tms.py                      # TMS implementation (field→current, biphasic pulses)
├── analyze_rtms_lfp.py         # Analysis script (raster, rates, LFP, spectra)
├── test_rtms_lfp_quick.py      # Quick test script
├── run_rtms_lfp_suite.py       # 3-condition suite
├── Circuit_param.xls           # Connectivity matrix
├── mod/                        # NEURON mechanisms (.mod files)
├── x86_64/                     # Compiled mechanisms
├── models/                     # Cell templates (.hoc files)
├── morphologies/               # Cell morphologies (.swc files)
├── output/                     # Simulation data (.json)
├── results/                    # Summary results (.json)
└── figures/                    # Analysis plots (.png)
```

## Output Files

After running simulations, you'll find:

- **output/**: `{condition}_data.json` - spike times, LFP data, traces
- **results/**: `rtms_lfp_suite_summary.json` - suite execution summary
- **figures/**: `rtms_lfp_{condition}.png` - 6-panel analysis plots:
  - Panel A: Raster plot (all populations)
  - Panel B: Population firing rates over time
  - Panel C: LFP traces (5 electrodes)
  - Panel D: LFP spectrogram (middle electrode)
  - Panel E: Power spectrum (pre-TMS vs during-TMS)
  - Panel F: LFP power by frequency band

## Requirements

- Python 3.8+
- NEURON 8.0+ with Python interface
- NetPyNE 1.0+
- NumPy, Matplotlib, SciPy

## Notes

- **LFP Configuration**: `cfg.recordLFP` must be a **list** of electrode positions `[[x,y,z], ...]`, not a boolean. This is already set correctly in `cfg.py`.
- **AD Stages**:
  - Stage 0: Healthy baseline
  - Stage 1: Early hyperexcitability (reduced M-current, enhanced NMDA)
  - Stage 3: Late hypoexcitability (depolarization block prone)
- **TMS Protocol**: 30 pulses at 30 Hz = 1 second of stimulation (2000-3000 ms window)

## Troubleshooting

If you get `TypeError: object of type 'bool' has no len()`:
- This means `cfg.recordLFP` was set to a boolean instead of a list
- Check `cfg.py` line 226: should be `cfg.recordLFP = cfg.LFP_electrodes`

If TMS parameters don't match expectations:
- Check `cfg.py` lines 50-63 for `cfg.tms_params` values
- Verify `tms.py` uses direct dictionary access (no `.get()` with defaults)

## Citation

If you use this code, please cite:

- Yao et al. (2024) - Human cortical cell type biophysics
- Fernando et al. - L2/3 connectivity and network architecture
- NetPyNE framework (www.netpyne.org)
