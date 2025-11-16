"""
cfg.py
Complete simulation configuration for Yao et al. L2/3 human cortical microcircuit
100-cell replica using NetPyNE
"""

from netpyne import specs
import os

cfg = specs.SimConfig()

#------------------------------------------------------------------------------
# SIMULATION CONFIGURATION
#------------------------------------------------------------------------------
cfg.simType = 'Yao_L23_100cell'
cfg.coreneuron = False

#------------------------------------------------------------------------------
# AD (Alzheimer's Disease) Configuration
#------------------------------------------------------------------------------
cfg.ADmodel = False             # False = Healthy, True = AD
cfg.ADstage = 1                 # AD stage: 1 = early hyperexcitability, 2 = intermediate, 3 = late hypoexcitability
cfg.ADpopulations = ['HL23PYR'] # Which populations to apply AD changes to (currently only HL23PYR supported)
cfg.conditionLabel = 'Healthy'  # Condition label for naming outputs (set by run_aim1.py)

#------------------------------------------------------------------------------
# Run parameters
#------------------------------------------------------------------------------
cfg.duration = 3000.0           # Duration of simulation, in ms (extended for TMS stim window)
cfg.dt = 0.025                  # Internal integration timestep
cfg.seeds = {'conn': 4321, 'stim': 1234, 'loc': 4321}
cfg.hParams = {'celsius': 34, 'v_init': -80}
cfg.verbose = False
cfg.createNEURONObj = True
cfg.createPyStruct = True
cfg.cvode_active = False
cfg.cache_efficient = True
cfg.printRunTime = 0.1

cfg.includeParamsLabel = False
cfg.printPopAvgRates = True
cfg.checkErrors = False

#------------------------------------------------------------------------------
# TMS Parameters (Source of Truth)
# This is the ONLY place to configure TMS parameters
#------------------------------------------------------------------------------
cfg.tms_params = dict(
    freq_Hz=30.,                        # Pulse frequency (Hz)
    duration_ms=cfg.duration,           # Simulation duration (ms)
    pulse_resolution_ms=cfg.dt,         # Time step (ms)
    stim_start_ms=2000.,                # TMS stimulation starts (ms)
    stim_end_ms=3000.,                  # TMS stimulation ends (ms)
    ef_amp_V_per_m=60.,                 # Electric field strength (V/m)
    width_ms=1.0,                       # Pulse width (ms) - biphasic total duration
    pshape="Sine",                      # Pulse shape
    decay_rate_percent_per_mm=10,       # Spatial decay rate
    E_field_dir=[-1, -1, -1],          # Field direction
    decay_dir=[0, 0, -1],              # Decay direction
    ref_point_um=[0, 0, 0],            # Reference point
)

#------------------------------------------------------------------------------
# Network size
#------------------------------------------------------------------------------
cfg.scale = 1.0
cfg.sizeY = 3300.0              # Column height (um)
cfg.sizeX = 250.0               # Column radius (um)
cfg.sizeZ = 250.0

#------------------------------------------------------------------------------
# Cell populations (100 cells total, matching Yao et al. proportions)
#------------------------------------------------------------------------------
cfg.allpops = ['HL23PYR', 'HL23SST', 'HL23PV', 'HL23VIP']

# Population sizes (total = 100)
# Yao ratios: PYR ~80%, SST ~8%, PV ~6%, VIP ~6%
cfg.cellNumber = {
    'HL23PYR': 80,      # Excitatory pyramidal
    'HL23SST': 8,       # Somatostatin interneurons
    'HL23PV': 6,        # Parvalbumin interneurons
    'HL23VIP': 6        # VIP interneurons
}

#------------------------------------------------------------------------------
# Recording
#------------------------------------------------------------------------------
cfg.recordCells = [(pop, 0) for pop in cfg.allpops]  # Record first cell of each type

cfg.recordTraces = {
    'V_soma': {'sec': 'soma_0', 'loc': 0.5, 'var': 'v'},
}

cfg.recordStim = False
cfg.recordTime = False
cfg.recordStep = 0.1

#------------------------------------------------------------------------------
# Saving
#------------------------------------------------------------------------------
cfg.simLabel = 'Yao_L23_100cell_AD_Stage2'
cfg.saveFolder = 'output'
cfg.savePickle = False
cfg.saveJson = True
cfg.saveDataInclude = ['simData', 'simConfig', 'netParams']
cfg.backupCfgFile = None
cfg.gatherOnlySimData = False
cfg.saveCellSecs = True
cfg.saveCellConns = True

#------------------------------------------------------------------------------
# Analysis and plotting
#------------------------------------------------------------------------------
cfg.analysis['plotRaster'] = {
    'include': cfg.allpops,
    'saveFig': True,
    'showFig': False,
    'orderInverse': True,
    'timeRange': [0, cfg.duration],
    'figSize': (14, 8),
    'fontSize': 12,
    'lw': 2,
    'markerSize': 8,
    'marker': '|',
    'dpi': 300
}

cfg.analysis['plotTraces'] = {
    'include': cfg.recordCells,
    'oneFigPer': 'cell',
    'overlay': False,
    'timeRange': [0, cfg.duration],
    'saveFig': True,
    'showFig': False,
    'figSize': (14, 10)
}

cfg.analysis['plot2Dnet'] = {
    'include': cfg.allpops,
    'saveFig': True,
    'showFig': False,
    'figSize': (12, 12),
    'fontSize': 10
}

cfg.analysis['plotConn'] = {
    'include': cfg.allpops,
    'saveFig': True,
    'showFig': False,
    'figSize': (10, 10)
}

#------------------------------------------------------------------------------
# Connectivity (from Circuit_param.xls)
#------------------------------------------------------------------------------
cfg.addConn = True

# Synaptic strength multipliers (for tuning E/I balance)
cfg.EEGain = 1.0    # E -> E
cfg.EIGain = 1.0    # E -> I
cfg.IEGain = 1.0    # I -> E
cfg.IIGain = 1.0    # I -> I

#------------------------------------------------------------------------------
# Background stimulation (NetStim inputs)
#------------------------------------------------------------------------------
cfg.addBackground = True

# Background rates (Hz) for each cell type
cfg.backgroundRate = {
    'HL23PYR': 100.0,
    'HL23SST': 100.0,
    'HL23PV': 100.0,
    'HL23VIP': 100.0
}

# Background weights (synaptic strength) - tuned values
cfg.backgroundWeight = {
    'HL23PYR': 0.0027,    # 0.01 ÷ 3.75 = target/actual ratio
    'HL23SST': 0.0015,    # 0.01 ÷ 6.76
    'HL23PV': 0.0088,     # 0.02 ÷ 2.28
    'HL23VIP': 0.0102     # 0.015 ÷ 1.47
}

#------------------------------------------------------------------------------
# Current clamp (for testing individual cells)
#------------------------------------------------------------------------------
cfg.addIClamp = False

cfg.IClamp1 = {
    'pop': 'HL23PYR',
    'sec': 'soma_0',
    'loc': 0.5,
    'start': 500,
    'dur': 500,
    'amp': 0.2
}

#------------------------------------------------------------------------------
# TMS Configuration - LEGACY (kept for compatibility but not used)
# All TMS parameters should be configured via cfg.tms_params above
# This block is disabled to avoid conflicts
#------------------------------------------------------------------------------
# NOTE: TMS is now configured ONLY through init.py or test scripts that read cfg.tms_params
# Do not manually edit this section - it is no longer used
cfg.tms_enabled = False  # Set to True in run scripts to enable TMS

#------------------------------------------------------------------------------
# LFP (Local Field Potential) Recording Configuration
#------------------------------------------------------------------------------
# IMPORTANT: NetPyNE expects cfg.recordLFP to be a list of electrode positions
# Format: [[x, y, z], ...] where coordinates are in µm
# Set to empty list [] to disable LFP recording

# Electrode positions (x, y, z in µm) - 5-electrode laminar array spanning L2/3
cfg.LFP_electrodes = [
    [0.0, 600.0, 0.0],   # Electrode 0 - upper L2/3
    [0.0, 700.0, 0.0],   # Electrode 1
    [0.0, 800.0, 0.0],   # Electrode 2 - mid L2/3
    [0.0, 900.0, 0.0],   # Electrode 3
    [0.0, 1000.0, 0.0],  # Electrode 4 - lower L2/3
]

# cfg.recordLFP must be a list (not a boolean) for NetPyNE
cfg.recordLFP = cfg.LFP_electrodes

# LFP recording parameters
cfg.LFP_dt = 0.1              # LFP sampling interval (ms)
cfg.LFP_pop = 'all'           # Which populations to include ('all' or list)
cfg.LFP_includeAxon = False   # Exclude axon from LFP calculation (faster)
cfg.saveLFP = True            # Save LFP data to file

#------------------------------------------------------------------------------
# External stimulation (TMS/tACS - disabled for basic model)
#------------------------------------------------------------------------------
cfg.addExternalStimulation = False
