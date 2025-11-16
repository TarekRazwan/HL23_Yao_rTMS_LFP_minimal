"""
tms.py
Transcranial Magnetic Stimulation (TMS) module for NetPyNE simulations

Implements realistic field-based rTMS with biphasic pulses and field→current conversion.
"""

from neuron import h
import numpy as np


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


def apply_tms_from_params(sim, cfg, target_pop='HL23PYR'):
    """
    Apply TMS protocol using cfg.tms_params (new standard format).
    
    Reads from cfg.tms_params and applies field-based biphasic rTMS.
    """
    if not hasattr(cfg, 'tms_params'):
        print("[TMS] No tms_params found - skipping")
        return []
    
    tms_params = cfg.tms_params
    
    # Extract parameters (NO defaults - cfg.tms_params is source of truth)
    field_Vm = tms_params['ef_amp_V_per_m']
    freq_Hz = tms_params['freq_Hz']
    stim_start = tms_params['stim_start_ms']
    stim_end = tms_params['stim_end_ms']
    width_ms = tms_params['width_ms']
    
    # Calculate number of pulses
    stim_duration = stim_end - stim_start
    n_pulses = int(stim_duration * freq_Hz / 1000.0)
    pulse_interval = 1000.0 / freq_Hz
    
    # Convert field to current
    amp_nA = convert_field_to_current(field_Vm, cell_type=target_pop, compartment='soma')
    
    print(f"[TMS] ========== TMS Protocol (from tms_params) ==========")
    print(f"[TMS] Field strength: {field_Vm} V/m → {amp_nA:.4f} nA")
    print(f"[TMS] Frequency: {freq_Hz} Hz")
    print(f"[TMS] Number of pulses: {n_pulses}")
    print(f"[TMS] Pulse duration: {width_ms} ms (biphasic)")
    print(f"[TMS] Stimulation window: {stim_start} - {stim_end} ms")
    print(f"[TMS] Target population: {target_pop}")
    
    # Apply pulses to all cells in target population
    clamps = []
    cell_count = 0
    
    for cell in sim.net.cells:
        if cell.tags.get('pop') == target_pop:
            # Find soma section
            soma_sec = None
            if 'soma_0' in cell.secs:
                soma_sec = cell.secs['soma_0']['hObj']
            elif 'soma' in cell.secs:
                soma_sec = cell.secs['soma']['hObj']
            else:
                first_sec_name = list(cell.secs.keys())[0]
                soma_sec = cell.secs[first_sec_name]['hObj']
            
            # Apply pulse train
            for pulse_idx in range(n_pulses):
                pulse_onset = stim_start + pulse_idx * pulse_interval
                pulse_clamps = apply_biphasic_pulse(soma_sec, pulse_onset, amp_nA, duration=width_ms)
                clamps.extend(pulse_clamps)
            
            cell_count += 1
    
    print(f"[TMS] Applied to {cell_count} cells")
    print(f"[TMS] Total IClamp objects: {len(clamps)}")
    print(f"[TMS] ================================================\n")
    
    return clamps


def get_tms_pulse_times(cfg):
    """Return the exact times of all TMS pulses for analysis/plotting."""
    if hasattr(cfg, 'tms_params'):
        freq_Hz = cfg.tms_params['freq_Hz']
        stim_start = cfg.tms_params['stim_start_ms']
        stim_end = cfg.tms_params['stim_end_ms']

        stim_duration = stim_end - stim_start
        n_pulses = int(stim_duration * freq_Hz / 1000.0)
        pulse_interval = 1000.0 / freq_Hz

        return [stim_start + i * pulse_interval for i in range(n_pulses)]

    return []
