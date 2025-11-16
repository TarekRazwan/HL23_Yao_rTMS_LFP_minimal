"""
analyze_rtms_lfp.py

Comprehensive analysis script for rTMS + LFP simulations.

Loads simulation outputs (spikes, LFP) and generates multi-panel figures showing:
- Raster plots with TMS pulse markers
- Population firing rates over time
- LFP traces from selected electrodes
- Pre vs post TMS LFP amplitude comparison
- Power spectral density (PSD) analysis

Usage:
    python analyze_rtms_lfp.py <data_file.json> [output_prefix]

Example:
    python analyze_rtms_lfp.py output/Healthy_rTMS_40Vm_data.json figures/healthy_rtms
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import signal
import sys
import os

# Matplotlib settings
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 100
})


class RTMSLFPAnalyzer:
    """
    Analyzer for rTMS + LFP simulation data.
    """

    def __init__(self, data_file):
        """
        Initialize analyzer and load data.

        Args:
            data_file: Path to NetPyNE output JSON file
        """
        self.data_file = data_file
        self.data = None
        self.spikes = None
        self.lfp = None
        self.config = None
        self.duration = None

        self.load_data()

    def load_data(self):
        """Load simulation data from JSON file."""
        print(f"\n[Loading] {self.data_file}")

        with open(self.data_file, 'r') as f:
            self.data = json.load(f)

        # Extract spike data
        if 'simData' in self.data and 'spkt' in self.data['simData']:
            self.spikes = {
                'times': np.array(self.data['simData']['spkt']),
                'ids': np.array(self.data['simData']['spkid'])
            }
            print(f"  ✓ Loaded {len(self.spikes['times'])} spikes")
        else:
            print("  ✗ No spike data found")
            self.spikes = {'times': np.array([]), 'ids': np.array([])}

        # Extract LFP data
        if 'simData' in self.data and 'LFP' in self.data['simData']:
            self.lfp = np.array(self.data['simData']['LFP'])
            print(f"  ✓ Loaded LFP: shape {self.lfp.shape}")
        else:
            print("  ✗ No LFP data found")
            self.lfp = None

        # Extract config
        if 'simConfig' in self.data:
            self.config = self.data['simConfig']
            self.duration = self.config.get('duration', 2000.0)
            print(f"  ✓ Duration: {self.duration} ms")
        else:
            self.duration = 2000.0

    def get_population_cell_count(self, pop_name):
        """
        Get number of cells in a population.

        Args:
            pop_name: Population name (e.g., 'HL23PYR')

        Returns:
            Number of cells in that population
        """
        # Try simConfig.cellNumber first (most reliable)
        if self.config and 'cellNumber' in self.config:
            return self.config['cellNumber'].get(pop_name, 0)

        # Fallback: try net.pops
        if 'net' in self.data and 'pops' in self.data['net']:
            if pop_name in self.data['net']['pops']:
                return self.data['net']['pops'][pop_name].get('cellGids', 0)

        # Last resort: count from cells if available
        if 'net' in self.data and 'cells' in self.data['net']:
            return sum(1 for cell in self.data['net']['cells']
                      if cell.get('tags', {}).get('pop') == pop_name)

        return 0

    def get_population_gids(self, pop_name):
        """
        Get cell GIDs for a specific population.

        Args:
            pop_name: Population name

        Returns:
            List of GIDs for that population
        """
        # Try net.cells first (most detailed)
        if 'net' in self.data and 'cells' in self.data['net']:
            return [cell['gid'] for cell in self.data['net']['cells']
                   if cell.get('tags', {}).get('pop') == pop_name]

        # Fallback: use cellNumber to infer GID ranges
        # Assumes sequential GID assignment in order: PYR, PV, SST, VIP
        if self.config and 'cellNumber' in self.config:
            cell_counts = self.config['cellNumber']
            pop_order = ['HL23PYR', 'HL23PV', 'HL23SST', 'HL23VIP']

            gid_start = 0
            for pop in pop_order:
                count = cell_counts.get(pop, 0)
                if pop == pop_name:
                    return list(range(gid_start, gid_start + count))
                gid_start += count

        return []

    def get_population_spikes(self, pop_name):
        """
        Extract spikes for a specific population.

        Args:
            pop_name: Population name (e.g., 'HL23PYR')

        Returns:
            Array of spike times for that population
        """
        # Get cell IDs for this population
        pop_gids = self.get_population_gids(pop_name)

        if not pop_gids:
            return np.array([])

        # Filter spikes
        mask = np.isin(self.spikes['ids'], pop_gids)
        return self.spikes['times'][mask]

    def compute_firing_rate_histogram(self, pop_name, bin_size=50.0):
        """
        Compute firing rate over time using histogram.

        Args:
            pop_name: Population name
            bin_size: Bin size (ms)

        Returns:
            bin_centers, firing_rates (Hz)
        """
        spike_times = self.get_population_spikes(pop_name)

        # Get cell count using robust method
        n_cells = self.get_population_cell_count(pop_name)

        if len(spike_times) == 0 or n_cells == 0:
            n_bins = int(self.duration / bin_size)
            return np.arange(n_bins) * bin_size + bin_size/2, np.zeros(n_bins)

        # Histogram
        bins = np.arange(0, self.duration + bin_size, bin_size)
        counts, bin_edges = np.histogram(spike_times, bins=bins)

        # Convert to Hz
        firing_rates = counts / (bin_size / 1000.0) / n_cells

        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        return bin_centers, firing_rates

    def get_tms_pulse_times(self):
        """
        Extract TMS pulse times from config.

        Returns:
            List of pulse times (ms)
        """
        if self.config is None:
            return []

        tms_cfg = self.config.get('tms', {})

        if not tms_cfg.get('enabled', False):
            return []

        onset = tms_cfg.get('onset', 500.0)
        protocol = tms_cfg.get('protocol', 'single')

        if protocol == 'repetitive':
            n_pulses = tms_cfg.get('n_pulses', 10)
            frequency = tms_cfg.get('frequency', 10)
            interval = 1000.0 / frequency

            return [onset + i * interval for i in range(n_pulses)]
        else:
            return [onset]

    def compute_lfp_spectrum(self, electrode_idx, time_window=None, nperseg=256):
        """
        Compute power spectral density of LFP.

        Args:
            electrode_idx: Electrode index
            time_window: [t_start, t_end] in ms (None = full duration)
            nperseg: FFT segment length

        Returns:
            freqs, psd
        """
        if self.lfp is None:
            return np.array([]), np.array([])

        lfp_dt = self.config.get('LFP_dt', 0.1)  # ms
        fs = 1000.0 / lfp_dt  # Hz

        lfp_trace = self.lfp[:, electrode_idx]

        # Select time window
        if time_window is not None:
            t_start, t_end = time_window
            idx_start = int(t_start / lfp_dt)
            idx_end = int(t_end / lfp_dt)
            lfp_trace = lfp_trace[idx_start:idx_end]

        # Welch's method for PSD
        freqs, psd = signal.welch(lfp_trace, fs=fs, nperseg=nperseg, scaling='density')

        return freqs, psd

    def plot_comprehensive_analysis(self, output_prefix='figures/rtms_lfp_analysis',
                                     electrode_idx=2, pre_window=[0, 500],
                                     post_window=[1500, 2000]):
        """
        Generate comprehensive multi-panel figure.

        Args:
            output_prefix: Output file prefix
            electrode_idx: Which electrode to plot (default: middle electrode)
            pre_window: [t_start, t_end] for pre-TMS analysis (ms)
            post_window: [t_start, t_end] for post-TMS analysis (ms)
        """
        fig = plt.figure(figsize=(18, 14))
        gs = GridSpec(4, 3, figure=fig, hspace=0.35, wspace=0.35,
                      left=0.08, right=0.95, top=0.95, bottom=0.05)

        pulse_times = self.get_tms_pulse_times()

        # Color scheme
        colors = {
            'HL23PYR': '#2E86AB',
            'HL23SST': '#A23B72',
            'HL23PV': '#F18F01',
            'HL23VIP': '#C73E1D'
        }

        populations = ['HL23PYR', 'HL23SST', 'HL23PV', 'HL23VIP']

        # ========== Panel A: Raster Plot ==========
        ax_raster = fig.add_subplot(gs[0, :])

        y_offset = 0
        y_ticks = []
        y_labels = []

        for pop in populations:
            # Get cell IDs for this pop using robust method
            pop_gids = self.get_population_gids(pop)

            if len(pop_gids) > 0:
                # Plot spikes
                for i, gid in enumerate(pop_gids):
                    # Get spikes for this specific cell
                    cell_spike_mask = self.spikes['ids'] == gid
                    cell_spike_times = self.spikes['times'][cell_spike_mask]

                    if len(cell_spike_times) > 0:
                        ax_raster.scatter(cell_spike_times,
                                        np.ones_like(cell_spike_times) * (y_offset + i),
                                        s=2, c=colors[pop], marker='|', linewidths=0.5)

                y_ticks.append(y_offset + len(pop_gids) / 2)
                y_labels.append(pop)
                y_offset += len(pop_gids) + 2

        # Mark TMS pulses
        for t in pulse_times:
            ax_raster.axvline(t, color='red', linestyle='--', alpha=0.5, linewidth=1.5)

        ax_raster.set_xlim(0, self.duration)
        ax_raster.set_ylim(0, y_offset)
        ax_raster.set_yticks(y_ticks)
        ax_raster.set_yticklabels(y_labels)
        ax_raster.set_xlabel('Time (ms)', fontweight='bold')
        ax_raster.set_ylabel('Population', fontweight='bold')
        ax_raster.set_title('A. Raster Plot with rTMS Pulses', fontweight='bold', fontsize=13)
        ax_raster.grid(True, alpha=0.3, axis='x')

        # ========== Panel B: Population Firing Rates ==========
        ax_rates = fig.add_subplot(gs[1, :])

        for pop in populations:
            times, rates = self.compute_firing_rate_histogram(pop, bin_size=50.0)
            ax_rates.plot(times, rates, linewidth=2, label=pop, color=colors[pop])

        # Mark TMS pulses
        for t in pulse_times:
            ax_rates.axvline(t, color='red', linestyle='--', alpha=0.5, linewidth=1.5)

        ax_rates.set_xlabel('Time (ms)', fontweight='bold')
        ax_rates.set_ylabel('Firing Rate (Hz)', fontweight='bold')
        ax_rates.set_title('B. Population Firing Rates (50 ms bins)', fontweight='bold', fontsize=13)
        ax_rates.legend(frameon=True, fancybox=True)
        ax_rates.grid(True, alpha=0.3)
        ax_rates.set_xlim(0, self.duration)

        # ========== Panel C: LFP Trace ==========
        ax_lfp = fig.add_subplot(gs[2, :])

        if self.lfp is not None:
            lfp_dt = self.config.get('LFP_dt', 0.1)
            t_lfp = np.arange(self.lfp.shape[0]) * lfp_dt

            ax_lfp.plot(t_lfp, self.lfp[:, electrode_idx], 'k-', linewidth=0.8)

            # Mark TMS pulses
            for t in pulse_times:
                ax_lfp.axvline(t, color='red', linestyle='--', alpha=0.5, linewidth=1.5)

            # Shade pre/post windows
            ax_lfp.axvspan(pre_window[0], pre_window[1], alpha=0.1, color='blue', label='Pre-TMS')
            ax_lfp.axvspan(post_window[0], post_window[1], alpha=0.1, color='green', label='Post-TMS')

            ax_lfp.set_xlabel('Time (ms)', fontweight='bold')
            ax_lfp.set_ylabel('LFP (mV)', fontweight='bold')
            ax_lfp.set_title(f'C. LFP Trace (Electrode {electrode_idx})', fontweight='bold', fontsize=13)
            ax_lfp.legend(frameon=True, fancybox=True)
            ax_lfp.grid(True, alpha=0.3)
            ax_lfp.set_xlim(0, self.duration)
        else:
            ax_lfp.text(0.5, 0.5, 'No LFP Data Available', ha='center', va='center',
                        transform=ax_lfp.transAxes, fontsize=14)
            ax_lfp.set_title('C. LFP Trace', fontweight='bold', fontsize=13)

        # ========== Panel D: Pre-TMS LFP Detail ==========
        ax_pre = fig.add_subplot(gs[3, 0])

        if self.lfp is not None:
            idx_pre_start = int(pre_window[0] / lfp_dt)
            idx_pre_end = int(pre_window[1] / lfp_dt)
            t_pre = np.arange(idx_pre_start, idx_pre_end) * lfp_dt

            ax_pre.plot(t_pre, self.lfp[idx_pre_start:idx_pre_end, electrode_idx], 'b-', linewidth=1)
            ax_pre.set_xlabel('Time (ms)', fontweight='bold')
            ax_pre.set_ylabel('LFP (mV)', fontweight='bold')
            ax_pre.set_title('D. Pre-TMS LFP Detail', fontweight='bold', fontsize=11)
            ax_pre.grid(True, alpha=0.3)

            # Stats
            pre_lfp = self.lfp[idx_pre_start:idx_pre_end, electrode_idx]
            pre_mean = np.mean(pre_lfp)
            pre_std = np.std(pre_lfp)
            ax_pre.text(0.02, 0.98, f'Mean: {pre_mean:.3f} mV\nStd: {pre_std:.3f} mV',
                        transform=ax_pre.transAxes, va='top', fontsize=8,
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        else:
            ax_pre.text(0.5, 0.5, 'No LFP', ha='center', va='center', transform=ax_pre.transAxes)

        # ========== Panel E: Post-TMS LFP Detail ==========
        ax_post = fig.add_subplot(gs[3, 1])

        if self.lfp is not None:
            idx_post_start = int(post_window[0] / lfp_dt)
            idx_post_end = int(post_window[1] / lfp_dt)
            t_post = np.arange(idx_post_start, idx_post_end) * lfp_dt

            ax_post.plot(t_post, self.lfp[idx_post_start:idx_post_end, electrode_idx], 'g-', linewidth=1)
            ax_post.set_xlabel('Time (ms)', fontweight='bold')
            ax_post.set_ylabel('LFP (mV)', fontweight='bold')
            ax_post.set_title('E. Post-TMS LFP Detail', fontweight='bold', fontsize=11)
            ax_post.grid(True, alpha=0.3)

            # Stats
            post_lfp = self.lfp[idx_post_start:idx_post_end, electrode_idx]
            post_mean = np.mean(post_lfp)
            post_std = np.std(post_lfp)
            ax_post.text(0.02, 0.98, f'Mean: {post_mean:.3f} mV\nStd: {post_std:.3f} mV',
                         transform=ax_post.transAxes, va='top', fontsize=8,
                         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        else:
            ax_post.text(0.5, 0.5, 'No LFP', ha='center', va='center', transform=ax_post.transAxes)

        # ========== Panel F: Power Spectrum Comparison ==========
        ax_psd = fig.add_subplot(gs[3, 2])

        if self.lfp is not None:
            # Pre-TMS spectrum
            freqs_pre, psd_pre = self.compute_lfp_spectrum(electrode_idx, time_window=pre_window)

            # Post-TMS spectrum
            freqs_post, psd_post = self.compute_lfp_spectrum(electrode_idx, time_window=post_window)

            if len(freqs_pre) > 0:
                ax_psd.semilogy(freqs_pre, psd_pre, 'b-', linewidth=2, label='Pre-TMS', alpha=0.7)
            if len(freqs_post) > 0:
                ax_psd.semilogy(freqs_post, psd_post, 'g-', linewidth=2, label='Post-TMS', alpha=0.7)

            ax_psd.set_xlabel('Frequency (Hz)', fontweight='bold')
            ax_psd.set_ylabel('PSD (mV²/Hz)', fontweight='bold')
            ax_psd.set_title('F. Power Spectral Density', fontweight='bold', fontsize=11)
            ax_psd.legend(frameon=True, fancybox=True)
            ax_psd.grid(True, alpha=0.3, which='both')
            ax_psd.set_xlim(0, 100)  # Focus on low frequencies
        else:
            ax_psd.text(0.5, 0.5, 'No LFP', ha='center', va='center', transform=ax_psd.transAxes)

        # Save figure
        os.makedirs(os.path.dirname(output_prefix) if os.path.dirname(output_prefix) else '.', exist_ok=True)
        figpath = f"{output_prefix}.png"
        plt.savefig(figpath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"\n[SAVED] {figpath}")

    def print_summary(self):
        """Print summary statistics."""
        print("\n" + "="*70)
        print("SIMULATION SUMMARY")
        print("="*70)

        print(f"Duration: {self.duration} ms")
        print(f"Total spikes: {len(self.spikes['times'])}")

        # Population stats
        populations = ['HL23PYR', 'HL23SST', 'HL23PV', 'HL23VIP']
        print("\nPopulation firing rates:")

        total_cells = 0
        for pop in populations:
            spike_times = self.get_population_spikes(pop)
            n_cells = self.get_population_cell_count(pop)
            total_cells += n_cells

            if n_cells > 0:
                rate = len(spike_times) / (self.duration / 1000.0) / n_cells
                print(f"  {pop:12s}: {rate:.2f} Hz ({len(spike_times)} spikes, {n_cells} cells)")
            else:
                print(f"  {pop:12s}: No cells")

        print(f"\nTotal cells: {total_cells}")

        # TMS info
        pulse_times = self.get_tms_pulse_times()
        if pulse_times:
            print(f"\nTMS pulses: {len(pulse_times)}")
            print(f"  Times: {pulse_times}")

            if self.config and 'tms' in self.config:
                tms_cfg = self.config['tms']
                if tms_cfg.get('use_field_based', False):
                    print(f"  Field strength: {tms_cfg.get('field_strength_Vm', 0)} V/m")
                print(f"  Protocol: {tms_cfg.get('protocol', 'single')}")
                print(f"  Pulse type: {tms_cfg.get('pulse_type', 'monophasic')}")

        # LFP info
        if self.lfp is not None:
            print(f"\nLFP recording:")
            print(f"  Shape: {self.lfp.shape} (timepoints × electrodes)")
            print(f"  Electrodes: {self.lfp.shape[1]}")
            print(f"  Sampling: {self.config.get('LFP_dt', 0.1)} ms")

        print("="*70)


def main():
    """Main execution."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_rtms_lfp.py <data_file.json> [output_prefix]")
        print("\nExample:")
        print("  python analyze_rtms_lfp.py output/Healthy_rTMS_40Vm_data.json figures/healthy_rtms")
        sys.exit(1)

    data_file = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else 'figures/rtms_lfp_analysis'

    if not os.path.exists(data_file):
        print(f"ERROR: File not found: {data_file}")
        sys.exit(1)

    # Create analyzer
    analyzer = RTMSLFPAnalyzer(data_file)

    # Print summary
    analyzer.print_summary()

    # Generate plots
    print("\nGenerating comprehensive analysis figure...")
    analyzer.plot_comprehensive_analysis(
        output_prefix=output_prefix,
        electrode_idx=2,          # Middle electrode
        pre_window=[0, 500],      # Pre-TMS window
        post_window=[1500, 2000]  # Post-TMS window
    )

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
