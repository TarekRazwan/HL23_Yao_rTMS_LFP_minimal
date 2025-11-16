"""
run_rtms_lfp_suite.py

Complete test suite for rTMS + LFP simulations.

Runs 3 conditions with 40 V/m field strength:
- Healthy_40Vm
- AD1_40Vm (hyperexcitable)
- AD3_40Vm (depolarization block prone)

All use:
- 40 V/m electric field
- 10 Hz repetitive protocol
- Biphasic pulses (1 ms)
- 10 pulses total

Usage:
    python run_rtms_lfp_suite.py
"""

import os
import sys
import subprocess
import json

# Ensure we're in the project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("rTMS + LFP SIMULATION SUITE - 40 V/m CONDITIONS ONLY")
print("="*80)


# Define test conditions - ONLY 3 conditions
# All use cfg.tms_params (60 V/m, 30 Hz, 2000-3000ms) - only AD flags change
conditions = [
    # Format: (name, ADmodel, ADstage, description)
    ('Healthy_40Vm', False, 0, 'Healthy + 60 V/m rTMS'),
    ('AD1_40Vm', True, 1, 'AD Stage 1 (hyperexcitable) + 60 V/m rTMS'),
    ('AD3_40Vm', True, 3, 'AD Stage 3 (depol. block) + 60 V/m rTMS'),
]


def run_single_simulation(name, ad_model, ad_stage, description):
    """
    Run a single simulation with specified parameters.

    Args:
        name: Condition name (for file naming)
        ad_model: True/False for AD
        ad_stage: 0 (healthy), 1, 2, or 3
        description: Human-readable description
    """
    print("\n" + "="*80)
    print(f"CONDITION: {name}")
    print(f"  {description}")
    print("="*80)

    # Create run script that directly modifies cfg and runs
    run_script = f"""
import os
import sys
from neuron import h
import neuron

# Load mechanisms
if os.path.exists('x86_64'):
    neuron.load_mechanisms('x86_64')

# Import NetPyNE
from netpyne import sim

# Load base config
from cfg import cfg

# === CONFIGURE THIS SIMULATION ===
# AD configuration (ONLY thing that changes between conditions)
cfg.ADmodel = {ad_model}
cfg.ADstage = {ad_stage}
cfg.conditionLabel = '{name}'

# TMS: Use cfg.tms_params defaults from cfg.py (60 V/m, 30 Hz, 2000-3000ms)
# DO NOT MODIFY cfg.tms_params - it's already set correctly in cfg.py
cfg.tms_enabled = True

# LFP configuration - ensure it's a list
if isinstance(cfg.recordLFP, bool):
    if cfg.recordLFP and hasattr(cfg, 'LFP_electrodes'):
        cfg.recordLFP = cfg.LFP_electrodes
    else:
        cfg.recordLFP = [
            [0.0, 600.0, 0.0],
            [0.0, 700.0, 0.0],
            [0.0, 800.0, 0.0],
            [0.0, 900.0, 0.0],
            [0.0, 1000.0, 0.0],
        ]
cfg.saveLFP = True

# Simulation settings
cfg.simLabel = '{name}'
cfg.saveFolder = 'output'

# Disable plots to speed up
cfg.analysis['plotRaster']['saveFig'] = False
cfg.analysis['plotTraces']['saveFig'] = False
cfg.analysis['plot2Dnet']['saveFig'] = False
cfg.analysis['plotConn']['saveFig'] = False

print(f"[CONFIG] AD: {{cfg.ADmodel}}, Stage: {{cfg.ADstage}}")
print(f"[CONFIG] TMS: {{cfg.tms_params['ef_amp_V_per_m']}} V/m, {{cfg.tms_params['freq_Hz']}} Hz, {{cfg.tms_params['stim_start_ms']}}-{{cfg.tms_params['stim_end_ms']}} ms")
print(f"[CONFIG] LFP: {{len(cfg.recordLFP)}} electrodes")

# Load network
from netParams import netParams

# Create network
print("\\n[Creating network...]")
sim.create(netParams, cfg)

# Apply TMS
print("\\n[Applying TMS...]")
import tms
tms_clamps = tms.apply_tms_from_params(sim, cfg)

# Run simulation
print("\\n[Running simulation...]")
sim.simulate()

# Save data
print("\\n[Saving data...]")
sim.analyze()

print("\\n[DONE]")
"""

    # Write run script
    script_path = f'_temp_run_{name}.py'
    with open(script_path, 'w') as f:
        f.write(run_script)

    # Run simulation
    try:
        python_path = '/opt/miniconda3/envs/netpyne/bin/python3'
        if not os.path.exists(python_path):
            python_path = 'python3'

        result = subprocess.run(
            [python_path, script_path],
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"\n✓ Simulation '{name}' completed successfully")
            success = True
        else:
            print(f"\n✗ Simulation '{name}' failed with return code {result.returncode}")
            success = False

    except Exception as e:
        print(f"\n✗ ERROR running simulation '{name}': {e}")
        success = False

    finally:
        # Cleanup
        if os.path.exists(script_path):
            os.remove(script_path)

    return success


def analyze_simulation(name):
    """
    Run analysis on simulation output.

    Args:
        name: Condition name
    """
    data_file = f'output/{name}_data.json'
    output_prefix = f'figures/rtms_lfp_{name}'

    if not os.path.exists(data_file):
        print(f"  ✗ Data file not found: {data_file}")
        return False

    print(f"\n[Analyzing] {name}...")

    try:
        python_path = '/opt/miniconda3/envs/netpyne/bin/python3'
        if not os.path.exists(python_path):
            python_path = 'python3'

        result = subprocess.run(
            [python_path, 'analyze_rtms_lfp.py', data_file, output_prefix],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"  ✓ Analysis complete: {output_prefix}.png")
            return True
        else:
            print(f"  ✗ Analysis failed")
            print(f"  STDERR: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ✗ ERROR in analysis: {e}")
        return False


def main():
    """Main execution."""

    # Create output directories
    os.makedirs('output', exist_ok=True)
    os.makedirs('figures', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    print(f"\nWill run {len(conditions)} conditions (all use cfg.tms_params: 60 V/m, 30 Hz):")
    for name, ad, stage, desc in conditions:
        print(f"  - {name}: {desc}")

    input("\nPress Enter to start (Ctrl+C to cancel)...")

    # Track results
    results = {
        'simulations': {},
        'analyses': {}
    }

    # Run simulations
    print("\n" + "="*80)
    print("PHASE 1: RUNNING SIMULATIONS")
    print("="*80)

    for name, ad_model, ad_stage, description in conditions:
        success = run_single_simulation(name, ad_model, ad_stage, description)
        results['simulations'][name] = success

    # Run analyses
    print("\n" + "="*80)
    print("PHASE 2: ANALYZING RESULTS")
    print("="*80)

    for name, _, _, _ in conditions:
        if results['simulations'].get(name, False):
            success = analyze_simulation(name)
            results['analyses'][name] = success
        else:
            print(f"\n[Skipping] {name} (simulation failed)")
            results['analyses'][name] = False

    # Summary
    print("\n" + "="*80)
    print("SUITE SUMMARY")
    print("="*80)

    print("\nSimulations:")
    for name, success in results['simulations'].items():
        status = "✓" if success else "✗"
        print(f"  {status} {name}")

    print("\nAnalyses:")
    for name, success in results['analyses'].items():
        status = "✓" if success else "✗"
        print(f"  {status} {name}")

    # Save summary
    summary_file = 'results/rtms_lfp_suite_summary.json'

    with open(summary_file, 'w') as f:
        json.dump({
            'conditions': [
                {'name': n, 'ad_model': a, 'ad_stage': s, 'description': d}
                for n, a, s, d in conditions
            ],
            'results': results
        }, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")

    print("\n" + "="*80)
    print("SUITE COMPLETE")
    print("="*80)

    # Count successes
    sim_success = sum(1 for s in results['simulations'].values() if s)
    ana_success = sum(1 for s in results['analyses'].values() if s)

    print(f"\nSuccessful simulations: {sim_success}/{len(conditions)}")
    print(f"Successful analyses: {ana_success}/{len(conditions)}")

    if sim_success == len(conditions) and ana_success == len(conditions):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠ Some tests failed - check output above")


if __name__ == '__main__':
    main()
