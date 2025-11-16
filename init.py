"""
init.py
COMPLETE Main simulation runner for Yao et al. L2/3 human microcircuit
100-cell replica using NetPyNE

Now supports:
- TMS protocols (configured in cfg.py)
- LFP recording (configured in cfg.py)

Usage:
    python init.py

Output:
    - output/Yao_L23_100cell_data.json
    - output/Yao_L23_100cell_raster.png
    - output/Yao_L23_100cell_traces.png
    - output/Yao_L23_100cell_LFP.dat (if LFP enabled)
"""

import os
import sys
from neuron import h
import neuron

# Load NEURON mechanisms
print("\n" + "="*70)
print("YAO ET AL. L2/3 HUMAN CORTICAL MICROCIRCUIT - 100 CELLS")
print("="*70)

print("\n[1/7] Checking prerequisites...")

# Check for required files
required_files = [
    'cfg.py',
    'netParams.py',
    'cellwrapper.py',
    'Circuit_param.xls'
]

missing_files = []
for fname in required_files:
    if not os.path.exists(fname):
        missing_files.append(fname)

if missing_files:
    print(f"✗ ERROR: Missing required files: {missing_files}")
    sys.exit(1)

print("✓ All required Python files present")

# Check for cell-specific templates
required_templates = [
    'models/NeuronTemplate_HL23PYR.hoc',
    'models/NeuronTemplate_HL23SST.hoc',
    'models/NeuronTemplate_HL23PV.hoc',
    'models/NeuronTemplate_HL23VIP.hoc'
]

missing_templates = []
for template in required_templates:
    if not os.path.exists(template):
        missing_templates.append(template)

if missing_templates:
    print(f"\n✗ ERROR: Missing cell-specific template files!")
    print(f"   Missing: {missing_templates}")
    print(f"\n   Run this first: python create_templates.py")
    sys.exit(1)

print("✓ All cell-specific templates present")

print("\n[2/7] Loading NEURON mechanisms...")
if os.path.exists('x86_64'):
    neuron.load_mechanisms('x86_64')
    print("✓ Loaded mechanisms from x86_64/")
elif os.path.exists('mod'):
    print("✗ ERROR: mod/ folder exists but not compiled!")
    print("   Run: nrnivmodl mod/")
    sys.exit(1)
else:
    print("⚠ WARNING: No mechanism folder found, using default NEURON mechanisms")

# Import NetPyNE
print("\n[3/7] Importing NetPyNE...")
from netpyne import sim

# Import configuration
print("\n[4/7] Loading configuration...")
from cfg import cfg
print(f"✓ Simulation duration: {cfg.duration} ms")
print(f"✓ Time step: {cfg.dt} ms")
print(f"✓ Cell populations: {cfg.allpops}")
print(f"✓ Total cells: {sum(cfg.cellNumber.values())}")

# Fix LFP configuration (convert boolean to list if needed)
if hasattr(cfg, 'recordLFP'):
    if isinstance(cfg.recordLFP, bool):
        if cfg.recordLFP and hasattr(cfg, 'LFP_electrodes'):
            cfg.recordLFP = cfg.LFP_electrodes
            print(f"✓ LFP recording enabled: {len(cfg.recordLFP)} electrodes")
        else:
            cfg.recordLFP = []
            print("  (LFP disabled)")
    elif isinstance(cfg.recordLFP, list) and len(cfg.recordLFP) > 0:
        print(f"✓ LFP recording enabled: {len(cfg.recordLFP)} electrodes")
    else:
        print("  (LFP disabled)")

# Report TMS status (check if tms_enabled flag is set)
if hasattr(cfg, 'tms_enabled') and cfg.tms_enabled:
    print(f"✓ TMS enabled")
    if hasattr(cfg, 'tms_params'):
        print(f"  Field strength: {cfg.tms_params.get('ef_amp_V_per_m', 0)} V/m")
        print(f"  Frequency: {cfg.tms_params.get('freq_Hz', 0)} Hz")
else:
    print("  (TMS disabled)")

# Import network parameters
print("\n[5/7] Loading network parameters...")
from netParams import netParams

# Create output directory
if not os.path.exists(cfg.saveFolder):
    os.makedirs(cfg.saveFolder)
    print(f"✓ Created output directory: {cfg.saveFolder}/")

# Create and run simulation
print("\n[6/7] Creating network...")
print("-" * 70)

try:
    # Create network
    sim.create(netParams, cfg)

    # Apply TMS if enabled
    if hasattr(cfg, 'tms_enabled') and cfg.tms_enabled:
        print("\n[Applying TMS...]")
        import tms
        tms_clamps = tms.apply_tms_from_params(sim, cfg)

    # Run simulation
    print("\n[7/7] Running simulation...")
    print("-" * 70)
    sim.simulate()

    # Analysis and saving
    print("\n[Analyzing and saving...]")
    sim.analyze()

    print("\n" + "="*70)
    print("✅ SIMULATION COMPLETE!")
    print("="*70)
    print(f"\nResults saved to: {cfg.saveFolder}/")
    print("\nGenerated files:")

    # List generated files
    output_files = []
    if os.path.exists(cfg.saveFolder):
        for fname in os.listdir(cfg.saveFolder):
            if fname.startswith(cfg.simLabel):
                output_files.append(fname)
                print(f"  ✓ {fname}")

    if not output_files:
        print("  (No output files found - check cfg.saveFolder)")

    # Print summary statistics
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)

    if hasattr(sim, 'allSimData') and 'spkt' in sim.allSimData:
        total_spikes = len(sim.allSimData['spkt'])
        duration_sec = cfg.duration / 1000.0
        num_cells = sum(cfg.cellNumber.values())
        avg_rate = total_spikes / (duration_sec * num_cells) if num_cells > 0 else 0

        print(f"Total spikes: {total_spikes}")
        print(f"Average firing rate: {avg_rate:.2f} Hz")
        print(f"Simulation time: {cfg.duration} ms")
        print(f"Number of cells: {num_cells}")

        # Per-population stats
        print("\nPer-population firing rates:")
        for pop in cfg.allpops:
            pop_gids = [cell.gid for cell in sim.net.cells if cell.tags.get('pop') == pop]
            pop_spikes = [t for i, t in enumerate(sim.allSimData['spkt'])
                          if sim.allSimData['spkid'][i] in pop_gids]
            pop_cells = cfg.cellNumber[pop]
            pop_rate = len(pop_spikes) / (duration_sec * pop_cells) if pop_cells > 0 else 0
            print(f"  {pop}: {pop_rate:.2f} Hz ({len(pop_spikes)} spikes)")
    else:
        print("No spike data available")

    # LFP stats
    if hasattr(sim, 'allSimData') and 'LFP' in sim.allSimData:
        import numpy as np
        lfp_data = np.array(sim.allSimData['LFP'])
        print(f"\nLFP data recorded:")
        print(f"  Shape: {lfp_data.shape} (timepoints × electrodes)")
        print(f"  Duration: {lfp_data.shape[0] * cfg.LFP_dt:.1f} ms")

    print("\n" + "="*70)
    print("🎉 SUCCESS! Check the output/ folder for results!")
    print("="*70 + "\n")

except KeyboardInterrupt:
    print("\n\n" + "="*70)
    print("⚠ SIMULATION INTERRUPTED BY USER")
    print("="*70 + "\n")
    sys.exit(0)

except Exception as e:
    print("\n" + "="*70)
    print("❌ SIMULATION FAILED!")
    print("="*70)
    print(f"\nError: {e}")
    print("\nTroubleshooting steps:")
    print("1. Make sure you ran: python create_templates.py")
    print("2. Check that all HOC files exist in models/")
    print("3. Check that all SWC files exist in morphologies/")
    print("4. Check that Circuit_param.xls exists")
    print("5. Verify mechanisms compiled: ls x86_64/")
    print("6. Check cellwrapper.py functions load correctly")

    import traceback
    print("\nFull error traceback:")
    print("-" * 70)
    traceback.print_exc()
    print("="*70 + "\n")
    sys.exit(1)
