import numpy as np, os
from twop_pipeline.utils.stats import *
from twop_pipeline.utils.filtering import *

def calc_deltaF_arrays(F, cell_indices, scope_fs=None, method='baseline', q=0.1, window_len=600, detrend=True,
                 F_neuropil=False, Fneu=None, ops_dict=None, neucoeff=None,
                 save_csv=False, output_filepath=None, output_df=False):
    """
    Function to calculate ΔF/F of cells' calcium traces

    Args:
        method (str; default='baseline', options= 'baseline', 'median', 'mean'): method used to calculate DFF

        q (float between 0 and 1; default: 0.1): quantile to use for moving baseline

        window_len (int; default=600): window length in seconds to filter/convolve signal

        detrend (bool; default=True): whether to detrend calcium signal with a median filter

        **F_neuropil (bool; default=False): set to True if calculating ΔF of neuropils

        save_csv (bool; default=False): whether to save ΔF/F output as a csv

        output_filepath (str or Path-like; default=None): output file name to save dff to csv

        output_df (bool; default=False): whether to output DeltaF calculation result as a pandas df (pd.DataFrame)

    Returns:
        deltaF (np.ndarray, pd.DataFrame): array of shape (num_cells, num_frames+1) with delta f of calcium signal OR
        pd.DataFrame of length num_frames if output_df == True
        
        timeEst (1D np.ndarray): estimated times of scope frames from scope_fps

    """
    # get raw fluourescence from cells 
    rawF = F[cell_indices, :].astype(np.float64)
    if F_neuropil:
        if Fneu is None:
            raise ValueError('Fneu (neuropil fluorescence) not provided. \
                             Set a value for Fneu if F_neuropil == True, else set F_neuropil = False.')
        neuropil_F = Fneu[cell_indices, :].astype(np.float64)
        if ops_dict is None and neucoeff is None:
            raise ValueError('Neuropil coefficient was not found. \
                             Provide either a suite2p ops dict or manually enter the neuropil coefficient from preprocessing.')
        if ops_dict is not None:
            neuropil_coef = float(ops_dict.get("neucoeff", 0.7))
        else:
            neuropil_coef = neucoeff
        F_neuropil_corrected = F[cell_indices, :] - neuropil_coef * neuropil_F
        rawF = F_neuropil_corrected
    if method == 'median':
        medianF = np.median(rawF, axis=1, keepdims=True)
        deltaF = (rawF - medianF) / medianF
    elif method == 'mean':
        meanF = np.mean(rawF, axis=1, keepdims=True)
        deltaF = (rawF - meanF) / meanF
    elif method == "baseline":
        if scope_fs is None:
            raise ValueError('Could not calculate deltaF because scope fps was not provided')
        # using sliding baseline (10 minutes window)
        winLen = min(round(window_len * scope_fs), rawF.shape[1])  # window size in frames
        baseline = np.zeros_like(rawF)
        for i in range(rawF.shape[0]):
            # Use a 10th percentile moving baseline (approximation using quantile filter)
            baseline[i, :] = movquant(rawF[i, :], q=q, window=winLen)
        deltaF = (rawF - baseline) / baseline
    else:
        raise ValueError(f"{method} method of computing df/F not recognized")
    # remove cells with all NaNs (ex. edge artifacts)
    valid_cells = ~np.isnan(deltaF).all(axis=1)
    deltaF = deltaF[valid_cells, :]
    # remove low-frequency trends using median filter
    if detrend:
        trend = median_filter(deltaF, size=(1, window_len))  # apply median filter across time axis
        deltaF = deltaF - trend
    ### save to csv if true and output filepath provided
    if save_csv and output_filepath is not None:
        if not output_filepath.endswith('.csv'):
            output_filepath += '.csv'
        np.savetxt(output_filepath, deltaF, delimiter=',')
    ## output dataframe if output_df = True 
    if output_df:
           # add timing info from num frames and scope fps
        num_frames = rawF.shape[1]
        timeEst = np.arange(num_frames) / scope_fs
        if (deltaF.shape[1]) != len(timeEst):
            raise ValueError('Timestamps are not the same length as deltaF frames!!')
            # Create DataFrame with rows: first is time, then deltaF rows
        all_data = np.vstack([timeEst[np.newaxis, :], deltaF])  # shape: (n_cells+1, n_timepoints)
        # Create DataFrame
        dff_df = pd.DataFrame(all_data)
        return dff_df
    return deltaF

def get_cell_spikes_arrays(spks, cell_indices, save_to_csv= False, output_filepath= None, output_df= False, df_filepath= None):
    """
    Args:
        save_to_csv (bool; default=False): whether to save spikes of cells as a CSV file

        output_filepath (str or Path-like; default=None): output file path to save spikes to  

        output_df (bool; default=False): whether to output cell spikes as a pandas df (pd.DataFrame)
        
        df_filepath (str or Path-like; default=None): output file name to save spikes dataframe to csv if output_df == True

    Returns:
        spikes (np.ndarray OR pd.DataFrame): spikes of cells in shape (num_cells, num_frames) OR pandas DF is output_df = True
    """
    cell_spikes = spks[cell_indices, :].astype(np.float64)
    if save_to_csv and output_filepath is not None:
        if not output_filepath.endswith('.csv'):
            output_filepath += '.csv'
        np.savetxt(output_filepath, cell_spikes, delimiter=',')
    ## output dataframe if save_df = True and output_df_path  
    if output_df:
        spikes_df = pd.DataFrame(cell_spikes)
        if df_filepath is not None:
            spikes_df.to_csv(df_filepath)
        return spikes_df
    return cell_spikes

def get_SNR_arrays(F, Fneu, ops_dict, iscell):
    """
    Function to calculate the per-cell signal-to-noise ratio 

    Args:
        None

    Returns:
        SNR (array-like): array of length = cells, with SNR value per cell
    """
    neuropil_coef = float(ops_dict.get("neucoeff", 0.7))
    neuropil_f = Fneu[iscell, :]
    cells_f = F[iscell, :]
    # #Fs = F - r*Fneu              
    F_neuropil_corrected = cells_f - neuropil_coef * neuropil_f            # neuropil-corrected
    neuropil_dff = calc_deltaF_arrays(F_neuropil=True)[0]
    # Noise estimate: scaled MAD of baseline points (low ΔF/F)
    # pick frames below the 20th percentile per cell as "baseline"
    # initialize to empty arrs of length frames
    SNR = np.zeros(F_neuropil_corrected.shape[0])
    noise_sigma = np.zeros(F_neuropil_corrected.shape[0])
    #resp_amp = np.zeros(Fs.shape[0])
    signal_peaks = np.zeros(F_neuropil_corrected.shape[0])

    for cell_idx in range(F_neuropil_corrected.shape[0]):
        dff_threshold = np.percentile(neuropil_dff[cell_idx], 20)
        dff_above_thresh = neuropil_dff[cell_idx][neuropil_dff[cell_idx] <= dff_threshold]
        mad = np.median(np.abs(dff_above_thresh - np.median(dff_above_thresh)))
        sigma = 1.4826 * mad + 1e-12
        noise_sigma[cell_idx] = sigma
        # signal amplitude: robust peak (95th percentile of ΔF/F)
        signal_peaks[cell_idx] = np.percentile(neuropil_dff[cell_idx], 95)
        SNR[cell_idx] = signal_peaks[cell_idx] / sigma
    return SNR

def get_spike_df_arrays(spks, cell_indices, num_frames, scope_times = None, scope_fs = None,
                  to_parquet=False, parquet_output_dir=None):
    spikes = get_cell_spikes_arrays(spks, cell_indices)
    cells, times, spike_vals = [] , [] , []
    spike_df = pd.DataFrame({}, columns=['Cell','Time','Value'])
    for cell in range(spikes.shape[0]):
        cell_spikes = spikes[cell]
        if spikes.shape[1] != num_frames:
            cell_spikes = cell_spikes[:-1]
        cells.extend([cell] * num_frames)
        spike_vals.extend(cell_spikes)
        if scope_times is not None:
            times.extend(scope_times)
        else:
            times.extend(np.arange(0, len(cell_spikes)) * scope_fs)
    spike_df = pd.DataFrame({'Cell': cells, 'Time': times, 'Value': spike_vals})
    if to_parquet:
        if parquet_output_dir is None:
            raise ValueError(f'to_parquet == True but no output directory or file name was provided.')
        if os.path.isdir(parquet_output_dir):
            savefile = os.path.join(parquet_output_dir, 'spikes_flat.parquet')
        else:
            print(f'WARNING!! Provided parquet output {parquet_output_dir} is not a directory. \
                  If its a file ending with .parquet, it will save to this relative path.')
            if os.path.basename(parquet_output_dir).endswith('.parquet'):
                savefile = parquet_output_dir
        spike_df.to_parquet(savefile)
    return spike_df            