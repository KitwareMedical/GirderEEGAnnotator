import logging
from pathlib import Path

import mne
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import butter, lfilter

from girdereegannotator.database.models import Asset

logger = logging.getLogger(__name__)


def filter_eeg(raw_eeg_path: str, eeg_path: str) -> Asset:
    """
    Converts an EDF file into a neonatal binary format for Eegviz.

    Filters the 13 required EEG channels into two bands ([0.53, 70] Hz and [0.53, 35] Hz),
    normalizes the amplitude to a 16-bit range (-1024 to +1024 µV -> 0 to 65535),
    and exports a big-endian binary file.
    """
    sampling_frequency = 256
    electrodes = ["Fp2", "F4", "T4", "C4", "O2", "Fz", "Cz", "Pz", "Fp1", "F3", "T3", "C3", "O1"]

    # Define constants for encoding range mapping
    maximum_encoded = 1024
    minimum_encoded = -1024
    sensitive_amplitude = maximum_encoded - minimum_encoded

    # Butterworth Filter Coefficients (5th order bandpass)
    nyq = sampling_frequency / 2
    b1, a1 = butter(5, [0.53 / nyq, 70.0 / nyq], btype="bandpass")
    b2, a2 = butter(5, [0.53 / nyq, 35.0 / nyq], btype="bandpass")

    try:
        raw = mne.io.read_raw_edf(raw_eeg_path, preload=True, stim_channel=False, verbose=False)
        ch_names = raw.ch_names

        raw_signal_list = []
        for electrode in electrodes:
            candidates = [electrode, f"EEG_{electrode}", f"EEG {electrode}"]
            matched_ch = next((ch for ch in ch_names if ch in candidates), None)

            if matched_ch is None:
                raw_signal_list.append(("zeros", electrode))
                continue

            sfreq = raw.info["sfreq"]
            data, _ = raw[matched_ch]
            data = data[0] * 1e6  # convert Volts to Microvolts (µV)

            if sfreq < 256:
                logger.debug(f"Signal {matched_ch} is sampled at {sfreq} Hz < 256 Hz. Upsampling...")
                n_source_points = len(data)
                source_times = np.arange(n_source_points) / sfreq
                source_duration = n_source_points / sfreq

                n_resampled_points = int(source_duration * 256)
                resampled_times = np.linspace(0, source_duration, n_resampled_points)

                # Linear interpolation
                f_interp = interp1d(
                    source_times, data, kind="linear", bounds_error=False, fill_value=(data[0], data[-1])
                )
                resampled_data = f_interp(resampled_times)
                raw_signal_list.append(resampled_data)

            elif sfreq == 256:
                raw_signal_list.append(data)
            else:
                raise ValueError(f"Downsampling from {sfreq} Hz is not implemented yet.")

        # Backfill the zero channels with the correct length now that we know it
        target_len = next((len(x) for x in raw_signal_list if not isinstance(x, tuple)), None)
        if target_len is None:
            raise ValueError("No valid EEG channels found to determine signal length.")

        for idx, item in enumerate(raw_signal_list):
            if isinstance(item, tuple) and item[0] == "zeros":
                raw_signal_list[idx] = np.zeros(target_len)

        # Stack into a 2D array: shape (channels, time)
        raw_signal_data = np.vstack(raw_signal_list)

        # Apply Filters
        filtered1 = lfilter(b1, a1, raw_signal_data, axis=1)
        filtered2 = lfilter(b2, a2, raw_signal_data, axis=1)
        array_like = np.concatenate([filtered1.flatten(), filtered2.flatten()])

        # Normalize and Encode to 16-bit Range [0, 65535]
        binary = np.round(((array_like - minimum_encoded) / sensitive_amplitude) * 65536)
        binary = np.clip(binary, 0, 65535).astype(np.uint16)

        logger.info("Successfully processed EEG file")
        with Path(eeg_path).open("wb") as file:
            file.write(binary.astype(">u2").tobytes())

        return Asset(name=Path(eeg_path).name, path=eeg_path)

    except Exception as e:
        logger.error(f"EEG file cannot be processed: {e}.")
