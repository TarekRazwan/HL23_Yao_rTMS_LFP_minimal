"""
cellwrapper.py
Fernando's exact approach - expects cell-specific template files
MODIFIED for Aim 1: Python-side AD parameter application
"""

import sys
import os


def apply_AD_changes_to_HL23PYR(cell, ad_stage):
    """
    Apply AD-related biophysical changes to HL23PYR cell (Python-side).

    This function modifies ion channel conductances post-hoc to implement
    stage-dependent AD pathophysiology with clear network-level effects.

    AD Stage 1 (Early Hyperexcitability):
    - Target: Increased PYR firing (~3.5-4 Hz vs ~2.6 Hz Healthy)
    - Mechanism: Enhanced excitability, reduced adaptation
    - Changes: ↑NaTg/Nap (easier spiking), ↓Kv3.1/SK/Ih (less repolarization/adaptation)

    AD Stage 2 (Impaired Dynamic Range / Partial Hypo):
    - Target: Reduced PYR firing (~1.5-2 Hz) with irregular patterns
    - Mechanism: Membrane dysfunction, network inhibition dominance
    - Changes: Partial NaTg recovery, severe Kv3.1/SK/Ih loss, increased leak

    Args:
        cell: NEURON cell object (HL23PYR)
        ad_stage: 1 (early hyperexcitability) or 2 (impaired/hypo)
    """

    if ad_stage == 1:
        # STAGE 1: HYPEREXCITABILITY
        # Goal: Clear firing rate increase vs Healthy (2.6 Hz → 3.5-4 Hz)

        for sec in cell.all:
            for seg in sec:
                # Increase excitability: boost Nav channels
                if hasattr(seg, 'NaTg'):
                    seg.NaTg.gbar *= 1.25  # +25% sodium (easier spike initiation)
                if hasattr(seg, 'Nap'):
                    seg.Nap.gbar *= 1.30   # +30% persistent sodium (sustained depolarization)

                # Reduce repolarization: cut K+ channels
                if hasattr(seg, 'Kv3_1'):
                    seg.Kv3_1.gbar *= 0.65  # -35% Kv3.1 (broader spikes)
                if hasattr(seg, 'SK'):
                    seg.SK.gbar *= 0.55     # -45% SK (less adaptation)
                if hasattr(seg, 'K_T'):
                    seg.K_T.gbar *= 0.70    # -30% transient K

                # Reduce Ih (less stabilization)
                if hasattr(seg, 'Ih'):
                    seg.Ih.gbar *= 0.65     # -35% Ih (less hyperpolarization-activated rebound)

        print(f"  [AD Stage 1] Applied hyperexcitability changes:")
        print(f"    NaTg: ×1.25, Nap: ×1.30, Kv3.1: ×0.65, SK: ×0.55, Ih: ×0.65")

    elif ad_stage == 2:
        # STAGE 2: IMPAIRED / PARTIAL HYPO
        # Goal: Reduced firing vs Healthy (2.6 Hz → 1.5-2 Hz), altered dynamics

        for sec in cell.all:
            for seg in sec:
                # Partial Nav recovery (less excitable than Stage 1)
                if hasattr(seg, 'NaTg'):
                    seg.NaTg.gbar *= 1.10  # +10% (reduced from Stage 1's +25%)
                if hasattr(seg, 'Nap'):
                    seg.Nap.gbar *= 1.05   # +5% (reduced from Stage 1's +30%)

                # Severe K+ channel loss (worse than Stage 1)
                if hasattr(seg, 'Kv3_1'):
                    seg.Kv3_1.gbar *= 0.45  # -55% (worse than Stage 1's -35%)
                if hasattr(seg, 'SK'):
                    seg.SK.gbar *= 0.35     # -65% (worse than Stage 1's -45%)
                if hasattr(seg, 'K_T'):
                    seg.K_T.gbar *= 0.50    # -50%

                # Further Ih reduction
                if hasattr(seg, 'Ih'):
                    seg.Ih.gbar *= 0.45     # -55% (worse than Stage 1)

                # Increased leak (membrane dysfunction)
                if hasattr(seg, 'pas'):
                    seg.pas.g *= 1.15       # +15% leak conductance (harder to maintain Vm)

        print(f"  [AD Stage 2] Applied impaired/hypo changes:")
        print(f"    NaTg: ×1.10, Nap: ×1.05, Kv3.1: ×0.45, SK: ×0.35, Ih: ×0.45, g_pas: ×1.15")

    elif ad_stage == 3:
        # STAGE 3: DEPOLARIZATION BLOCK PRONE
        # Goal: Steep early F-I slope followed by depolarization block
        # Mechanism: Excessive NaP + severe repolarization deficit → sustained depolarization → Na inactivation

        for sec in cell.all:
            for seg in sec:
                # Aggressive NaP increase (drives sustained depolarization)
                if hasattr(seg, 'NaTg'):
                    seg.NaTg.gbar *= 1.20  # +20% transient sodium
                if hasattr(seg, 'Nap'):
                    seg.Nap.gbar *= 1.60   # +60% persistent sodium (AGGRESSIVE)

                # Extreme K+ channel loss (unable to repolarize)
                if hasattr(seg, 'Kv3_1'):
                    seg.Kv3_1.gbar *= 0.30  # -70% Kv3.1 (critical repolarization deficit)
                if hasattr(seg, 'SK'):
                    seg.SK.gbar *= 0.25     # -75% SK (minimal adaptation)
                if hasattr(seg, 'K_T'):
                    seg.K_T.gbar *= 0.40    # -60% transient K

                # Severe Ih reduction (no hyperpolarization rebound)
                if hasattr(seg, 'Ih'):
                    seg.Ih.gbar *= 0.30     # -70% Ih

                # Further increased leak
                if hasattr(seg, 'pas'):
                    seg.pas.g *= 1.20       # +20% leak

        print(f"  [AD Stage 3] Applied depolarization-block-prone changes:")
        print(f"    NaTg: ×1.20, Nap: ×1.60, Kv3.1: ×0.30, SK: ×0.25, Ih: ×0.30, g_pas: ×1.20")


def loadCell_HL23PYR(cellName, ad=False, ad_stage=None):
    """
    Load HL23PYR cell with optional AD staging support.

    Args:
        cellName (str): Cell name (e.g., 'HL23PYR')
        ad (bool): If True, apply AD variant biophysics (Python-side)
        ad_stage (int): AD stage (1=early hyperexcitability, 2=impaired/hypo)

    Returns:
        NEURON cell object
    """
    templatepath = 'models/NeuronTemplate_HL23PYR.hoc'
    morphpath = 'morphologies/' + cellName + '.swc'
    biophysics = 'models/biophys_' + cellName + '.hoc'  # Always load healthy baseline

    from neuron import h
    h.load_file("stdrun.hoc")
    h.load_file('import3d.hoc')
    h.xopen(biophysics)

    try:
       h.xopen(templatepath)
    except:
        pass

    cell = getattr(h, 'NeuronTemplate_HL23PYR')(morphpath)
    h.biophys_HL23PYR(cell)  # Apply healthy baseline first

    # Apply AD changes if requested (Python-side post-hoc modification)
    if ad:
        stage = ad_stage if ad_stage is not None else 1
        print(f"[AD STAGE {stage}] Applying Python-side AD parameter changes to {cellName}")
        apply_AD_changes_to_HL23PYR(cell, stage)

        # Print post-AD conductances for verification
        print(f"  Post-AD verification:")
        print(f"    Kv3.1 gbar (soma): {cell.soma[0](0.5).gbar_Kv3_1:.6f}")
        print(f"    SK gbar (soma): {cell.soma[0](0.5).gbar_SK:.8f}")
        print(f"    NaTg gbar (axon): {cell.axon[0](0.5).gbar_NaTg:.6f}")
    else:
        print(f"[HEALTHY] Loading {cellName} with healthy baseline biophysics")
        print(f"  Kv3.1 gbar (soma): {cell.soma[0](0.5).gbar_Kv3_1:.6f}")
        print(f"  SK gbar (soma): {cell.soma[0](0.5).gbar_SK:.8f}")
        print(f"  NaTg gbar (axon): {cell.axon[0](0.5).gbar_NaTg:.6f}")

    return cell


def loadCell_HL23VIP(cellName):
    templatepath = 'models/NeuronTemplate_HL23VIP.hoc'
    biophysics = 'models/biophys_' + cellName + '.hoc'
    morphpath = 'morphologies/' + cellName + '.swc'
    
    from neuron import h
    h.load_file("stdrun.hoc")
    h.load_file('import3d.hoc')
    h.xopen(biophysics)
        
    try:
       h.xopen(templatepath)
    except:
        pass
    
    cell = getattr(h, 'NeuronTemplate_HL23VIP')(morphpath)
    print(cell)
    h.biophys_HL23VIP(cell)
    return cell


def loadCell_HL23PV(cellName):
    templatepath = 'models/NeuronTemplate_HL23PV.hoc'
    biophysics = 'models/biophys_' + cellName + '.hoc'
    morphpath = 'morphologies/' + cellName + '.swc'
    
    from neuron import h
    h.load_file("stdrun.hoc")
    h.load_file('import3d.hoc')
    h.xopen(biophysics)
        
    try:
       h.xopen(templatepath)
    except:
        pass
    
    cell = getattr(h, 'NeuronTemplate_HL23PV')(morphpath)
    print(cell)
    h.biophys_HL23PV(cell)
    return cell


def loadCell_HL23SST(cellName):
    templatepath = 'models/NeuronTemplate_HL23SST.hoc'
    biophysics = 'models/biophys_' + cellName + '.hoc'
    morphpath = 'morphologies/' + cellName + '.swc'
    
    from neuron import h
    h.load_file("stdrun.hoc")
    h.load_file('import3d.hoc')
    h.xopen(biophysics)
        
    try:
       h.xopen(templatepath)
    except:
        pass
    
    cell = getattr(h, 'NeuronTemplate_HL23SST')(morphpath)
    print(cell)
    h.biophys_HL23SST(cell)
    return cell