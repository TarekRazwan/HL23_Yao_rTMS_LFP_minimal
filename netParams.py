"""
netParams.py
COMPLETE Network parameters for Yao et al. human L2/3 microcircuit
100 cells with biophysically detailed models
"""

from netpyne import specs
import pandas as pd
import numpy as np
import sys

netParams = specs.NetParams()

try:
    from __main__ import cfg
except:
    from cfg import cfg

#------------------------------------------------------------------------------
# Network parameters
#------------------------------------------------------------------------------
netParams.scale = cfg.scale
netParams.sizeX = cfg.sizeX
netParams.sizeY = cfg.sizeY
netParams.sizeZ = cfg.sizeZ
netParams.shape = 'cylinder'

#------------------------------------------------------------------------------
# General connectivity parameters
#------------------------------------------------------------------------------
netParams.defaultThreshold = -10.0
netParams.defaultDelay = 0.5
netParams.propVelocity = 300.0

# Layer boundaries (y-axis, from pia to white matter)
layer = {
    '1': [0.0, 250.0],
    '23': [250.0, 1200.0],
    '23soma': [550.0, 1200.0],  # Soma placement zone
    '4': [1200.0, 1580.0],
    '5': [1580.0, 2300.0],
    '6': [2300.0, 3300.0]
}

#------------------------------------------------------------------------------
# Import cell models using cellwrapper.py
#------------------------------------------------------------------------------
print("\n" + "="*70)
print("LOADING CELL MODELS")
print("="*70)

for cellName in cfg.allpops:
    print(f"\nImporting {cellName}...")
    try:
        # Build cellArgs dictionary with AD support for HL23PYR
        cellArgs = {'cellName': cellName}

        # Add AD parameters for populations specified in cfg.ADpopulations
        if cfg.ADmodel and cellName in cfg.ADpopulations:
            cellArgs['ad'] = True
            cellArgs['ad_stage'] = cfg.ADstage
            print(f"  [AD MODE] Stage {cfg.ADstage} enabled for {cellName}")

        cellRule = netParams.importCellParams(
            label=cellName,
            somaAtOrigin=False,
            conds={'cellType': cellName, 'cellModel': 'HH_full'},
            fileName='cellwrapper.py',
            cellName='loadCell_' + cellName,
            cellInstance=True,
            cellArgs=cellArgs
        )
        print(f"✓ {cellName} imported successfully")
    except Exception as e:
        print(f"✗ ERROR importing {cellName}: {e}")
        sys.exit(1)

#------------------------------------------------------------------------------
# Load connectivity parameters from Circuit_param.xls
#------------------------------------------------------------------------------
print("\n" + "="*70)
print("LOADING CIRCUIT PARAMETERS")
print("="*70)

try:
    circuit_params = pd.read_excel('Circuit_param.xls', sheet_name=None, index_col=0)
    print(f"✓ Loaded {len(circuit_params)} sheets from Circuit_param.xls")

    conn_probs = circuit_params['conn_probs']
    syn_cond = circuit_params['syn_cond']
    n_cont = circuit_params['n_cont']
    Depression = circuit_params['Depression']
    Facilitation = circuit_params['Facilitation']
    Use = circuit_params['Use']
    Syn_pos = circuit_params['Syn_pos']

    print(f"\nConnection probability matrix:")
    print(conn_probs)

except Exception as e:
    print(f"✗ ERROR loading Circuit_param.xls: {e}")
    print("Using default connectivity values...")

    # Default values if Excel file fails
    cell_names = cfg.allpops
    conn_probs = pd.DataFrame(0.1, index=cell_names, columns=cell_names)
    syn_cond = pd.DataFrame(0.001, index=cell_names, columns=cell_names)
    n_cont = pd.DataFrame(1, index=cell_names, columns=cell_names)
    Depression = pd.DataFrame(0.0, index=cell_names, columns=cell_names)
    Facilitation = pd.DataFrame(0.0, index=cell_names, columns=cell_names)
    Use = pd.DataFrame(0.5, index=cell_names, columns=cell_names)
    Syn_pos = pd.DataFrame(0, index=cell_names, columns=cell_names)

#------------------------------------------------------------------------------
# Add 'spiny' section list to all cells (for synapse placement)
#------------------------------------------------------------------------------
print("\n" + "="*70)
print("CREATING SPINY SECTION LISTS")
print("="*70)

for cellName in netParams.cellParams.keys():
    if 'secLists' not in netParams.cellParams[cellName]:
        netParams.cellParams[cellName]['secLists'] = {}

    # Get all sections
    all_secs = list(netParams.cellParams[cellName]['secs'].keys())

    # Define non-spiny sections (soma + axon)
    nonSpiny = [sec for sec in all_secs if 'soma' in sec or 'axon' in sec or 'myelin' in sec]

    # Spiny = everything else (dendrites)
    netParams.cellParams[cellName]['secLists']['spiny'] = [
        sec for sec in all_secs if sec not in nonSpiny
    ]

    # Also create basal and apical lists
    netParams.cellParams[cellName]['secLists']['basal'] = [
        sec for sec in all_secs if 'dend' in sec
    ]
    netParams.cellParams[cellName]['secLists']['apical'] = [
        sec for sec in all_secs if 'apic' in sec
    ]

    print(f"✓ {cellName}: {len(netParams.cellParams[cellName]['secLists']['spiny'])} spiny sections")

#------------------------------------------------------------------------------
# Population parameters
#------------------------------------------------------------------------------
print("\n" + "="*70)
print("CREATING POPULATIONS")
print("="*70)

for cellName in cfg.allpops:
    netParams.popParams[cellName] = {
        'cellType': cellName,
        'cellModel': 'HH_full',
        'numCells': cfg.cellNumber[cellName],
        'yRange': layer['23soma']
    }
    print(f"✓ {cellName}: {cfg.cellNumber[cellName]} cells")

#------------------------------------------------------------------------------
# Synaptic mechanisms (SIMPLE - using built-in Exp2Syn)
#------------------------------------------------------------------------------
print("\n" + "="*70)
print("DEFINING SYNAPTIC MECHANISMS")
print("="*70)

# Standard mechanisms (always available in NEURON)
netParams.synMechParams['AMPA'] = {
    'mod': 'Exp2Syn',
    'tau1': 0.3,
    'tau2': 3.0,
    'e': 0
}

netParams.synMechParams['NMDA'] = {
    'mod': 'Exp2Syn',
    'tau1': 2.0,
    'tau2': 65.0,
    'e': 0
}

netParams.synMechParams['GABAA'] = {
    'mod': 'Exp2Syn',
    'tau1': 1.0,
    'tau2': 10.0,
    'e': -80
}

print("✓ Defined 3 standard synapse types (AMPA, NMDA, GABAA)")

# Create connection-specific synapse parameters
cell_names = cfg.allpops
for pre in cell_names:
    for post in cell_names:
        if "PYR" in pre:  # Excitatory
            netParams.synMechParams[pre + post] = {
                'mod': 'Exp2Syn',
                'tau1': 0.3,
                'tau2': 3.0,
                'e': 0
            }
        else:  # Inhibitory
            netParams.synMechParams[pre + post] = {
                'mod': 'Exp2Syn',
                'tau1': 1.0,
                'tau2': 10.0,
                'e': -80
            }

print(f"✓ Created {len(cell_names)**2} connection-specific synapse types")

#------------------------------------------------------------------------------
# Connectivity rules (from Circuit_param.xls)
#------------------------------------------------------------------------------
print("\n" + "="*70)
print("CREATING CONNECTIVITY RULES")
print("="*70)

if cfg.addConn:
    conn_count = 0
    for pre in cell_names:
        for post in cell_names:
            prob = conn_probs.at[pre, post]

            if prob > 0.0:
                # Determine target section based on pre/post types
                if "PYR" in pre and "PYR" in post:
                    target_sec = 'spiny'  # E->E: dendrites
                elif "PYR" in pre:
                    target_sec = 'spiny'  # E->I: dendrites
                else:
                    target_sec = 'spiny'  # I->E or I->I: dendrites

                # Apply gain factors
                if "PYR" in pre and "PYR" in post:
                    weight = syn_cond.at[pre, post] * cfg.EEGain
                elif "PYR" in pre:
                    weight = syn_cond.at[pre, post] * cfg.EIGain
                elif "PYR" in post:
                    weight = syn_cond.at[pre, post] * cfg.IEGain
                else:
                    weight = syn_cond.at[pre, post] * cfg.IIGain

                netParams.connParams[pre + '->' + post] = {
                    'preConds': {'pop': pre},
                    'postConds': {'pop': post},
                    'probability': prob,
                    'weight': weight,
                    'delay': 0.5,
                    'synMech': pre + post,
                    'synsPerConn': int(n_cont.at[pre, post]),
                    'sec': target_sec
                }

                conn_count += 1
                print(f"✓ {pre}->{post}: P={prob:.3f}, W={weight:.4f}, N={int(n_cont.at[pre, post])}")

    print(f"\n✓ Created {conn_count} connectivity rules")
else:
    print("✗ Connectivity disabled in cfg.py")

#------------------------------------------------------------------------------
# Background stimulation (NetStim)
#------------------------------------------------------------------------------
print("\n" + "="*70)
print("ADDING BACKGROUND STIMULATION")
print("="*70)

if cfg.addBackground:
    for pop in cfg.allpops:
        # Create NetStim source
        netParams.stimSourceParams[f'bkg_{pop}'] = {
            'type': 'NetStim',
            'rate': cfg.backgroundRate[pop],
            'noise': 1.0,
            'start': 0
        }

        # Connect to population
        netParams.stimTargetParams[f'bkg->{pop}'] = {
            'source': f'bkg_{pop}',
            'conds': {'pop': pop},
            'weight': cfg.backgroundWeight[pop],
            'delay': 0.5,
            'synMech': 'AMPA',
            'sec': 'spiny'
        }

        print(f"✓ Background -> {pop}: {cfg.backgroundRate[pop]} Hz, weight={cfg.backgroundWeight[pop]}")
else:
    print("✗ Background stimulation disabled")

#------------------------------------------------------------------------------
# Current clamp (optional)
#------------------------------------------------------------------------------
if cfg.addIClamp:
    print("\n" + "="*70)
    print("ADDING CURRENT CLAMPS")
    print("="*70)

    for key in [k for k in dir(cfg) if k.startswith('IClamp')]:
        params = getattr(cfg, key, None)
        if params:
            pop, sec, loc, start, dur, amp = [
                params[s] for s in ['pop', 'sec', 'loc', 'start', 'dur', 'amp']
            ]

            netParams.stimSourceParams[key] = {
                'type': 'IClamp',
                'delay': start,
                'dur': dur,
                'amp': amp
            }

            netParams.stimTargetParams[key + '_' + pop] = {
                'source': key,
                'conds': {'pop': pop},
                'sec': sec,
                'loc': loc
            }

            print(f"✓ IClamp -> {pop}: {amp} nA for {dur} ms")

#------------------------------------------------------------------------------
print("\n" + "="*70)
print("NETWORK PARAMETERS COMPLETE")
print("="*70)
print(f"✓ Total populations: {len(netParams.popParams)}")
print(f"✓ Total connectivity rules: {len(netParams.connParams)}")
print(f"✓ Total synaptic mechanisms: {len(netParams.synMechParams)}")
print(f"✓ Total cells: {sum(cfg.cellNumber.values())}")
print("="*70 + "\n")
