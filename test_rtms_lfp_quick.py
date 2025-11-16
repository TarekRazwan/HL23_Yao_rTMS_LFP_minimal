"""
test_rtms_lfp_quick.py

Quick test of rTMS + LFP functionality.

Runs a single test simulation (Healthy + 40 V/m rTMS) with LFP recording,
then analyzes and plots the results.

This is a fast demonstration of the complete pipeline.

Usage:
    python test_rtms_lfp_quick.py
"""

import os
import sys

# Ensure correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("QUICK TEST: rTMS + LFP SIMULATION")
print("="*80)
print("\nCondition: Healthy + 40 V/m biphasic rTMS (10 Hz, 10 pulses)")
print("Duration: 2000 ms")
print("LFP: 5-electrode laminar array")
print("="*80)

# Import required modules
from neuron import h
import neuron

print("\n[1/6] Loading NEURON mechanisms...")
if os.path.exists('x86_64'):
    neuron.load_mechanisms('x86_64')
    print("  ✓ Loaded from x86_64/")
else:
    print("  ⚠ No compiled mechanisms found")

print("\n[2/6] Importing NetPyNE...")
from netpyne import sim

print("\n[3/6] Loading configuration...")
from cfg import cfg

# Configure for this test
cfg.ADmodel = False  # Healthy
cfg.ADstage = 1
cfg.conditionLabel = 'Healthy_40Vm_Quick_Test'

# Override tms_params for this quick test (40 V/m, 10 Hz, starting at 500 ms)
cfg.tms_params['ef_amp_V_per_m'] = 40.
cfg.tms_params['freq_Hz'] = 10.
cfg.tms_params['stim_start_ms'] = 500.0
cfg.tms_params['stim_end_ms'] = 1500.0  # 1 second of stimulation
cfg.duration = 2000.0  # Keep quick test at 2 seconds

# Recalculate derived TMS values
_tms_duration = cfg.tms_params['stim_end_ms'] - cfg.tms_params['stim_start_ms']
_n_pulses = int(_tms_duration * cfg.tms_params['freq_Hz'] / 1000.0)

# TMS: 40 V/m, biphasic, 10 Hz, derived from tms_params
cfg.tms['enabled'] = True
cfg.tms['protocol'] = 'repetitive'
cfg.tms['pulse_type'] = 'biphasic'
cfg.tms['use_field_based'] = True
cfg.tms['field_strength_Vm'] = cfg.tms_params['ef_amp_V_per_m']
cfg.tms['frequency'] = cfg.tms_params['freq_Hz']
cfg.tms['n_pulses'] = _n_pulses
cfg.tms['onset'] = cfg.tms_params['stim_start_ms']
cfg.tms['biphasic_duration'] = cfg.tms_params['width_ms']

# LFP - cfg.recordLFP is now a list of electrode positions
# It's already set in cfg.py, but we can verify it's enabled (non-empty list)
if not cfg.recordLFP:
    # If empty, set to default electrodes
    cfg.recordLFP = [
        [0.0, 600.0, 0.0],
        [0.0, 700.0, 0.0],
        [0.0, 800.0, 0.0],
        [0.0, 900.0, 0.0],
        [0.0, 1000.0, 0.0],
    ]
    cfg.LFP_electrodes = cfg.recordLFP
cfg.saveLFP = True

# Simulation settings
cfg.simLabel = 'test_rtms_lfp_quick'
cfg.saveFolder = 'test_output'

# Reduce some plotting for speed
cfg.analysis['plotRaster']['saveFig'] = False
cfg.analysis['plotTraces']['saveFig'] = False
cfg.analysis['plot2Dnet']['saveFig'] = False
cfg.analysis['plotConn']['saveFig'] = False

print(f"  ✓ AD: {cfg.ADmodel}")
print(f"  ✓ TMS: {cfg.tms['field_strength_Vm']} V/m, {cfg.tms['protocol']}, {cfg.tms['pulse_type']}")
print(f"  ✓ LFP: {len(cfg.recordLFP)} electrodes")

print("\n[4/6] Loading network parameters...")
from netParams import netParams
print(f"  ✓ Network ready ({sum(cfg.cellNumber.values())} cells)")

print("\n[5/6] Creating network and running simulation...")
print("-" * 80)

# Create network
sim.create(netParams, cfg)

# Apply TMS
import tms
print("\n[Applying TMS...]")
tms_clamps = tms.apply_tms(sim, cfg)

# Run simulation
print("\n[Running simulation...]")
sim.simulate()

print("\n[Saving data...]")
sim.analyze()

print("-" * 80)
print("  ✓ Simulation complete")

# Analyze results
print("\n[6/6] Analyzing results...")

data_file = f'{cfg.saveFolder}/{cfg.simLabel}_data.json'
output_prefix = f'figures/{cfg.simLabel}_analysis'

if os.path.exists(data_file):
    print(f"  ✓ Data file found: {data_file}")

    # Import analyzer
    from analyze_rtms_lfp import RTMSLFPAnalyzer

    # Create analyzer
    analyzer = RTMSLFPAnalyzer(data_file)

    # Print summary
    analyzer.print_summary()

    # Generate plots
    print("\n  Generating comprehensive analysis figure...")
    analyzer.plot_comprehensive_analysis(
        output_prefix=output_prefix,
        electrode_idx=2,           # Middle electrode
        pre_window=[0, 500],       # Pre-TMS
        post_window=[1500, 2000]   # Post-TMS
    )

    print("\n" + "="*80)
    print("SUCCESS!")
    print("="*80)
    print(f"\nGenerated files:")
    print(f"  - {data_file}")
    print(f"  - {output_prefix}.png")
    print("\n" + "="*80)

else:
    print(f"  ✗ ERROR: Data file not found: {data_file}")
    sys.exit(1)
