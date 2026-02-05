import os, numpy as np
from twop_pipeline.intan.IntanData import IntanData

def export_signal_times(intan_data: IntanData, out_dir=None):
    '''
    Function to export signals for analog inputs

    Args:
        intan_data: Object of type IntanData 
        out_dir: relative path name for folder to be saved in intan basepath
    Returns:
        None -> exports data to out_dir
    '''
    # signals = [intan_data.photodiode_raw, intan_data.twop_raw, intan_data.camera_raw, intan_data.treadmill_raw]
    signal_timings = [intan_data.pd_times, intan_data.scope_times, intan_data.camera_times, intan_data.treadmill_times]
    signal_types = ['phodiode', 'scope', 'camera', 'treadmill']
    # if relative path provided, set directory to intan path
    if not os.path.isdir(out_dir):
        if out_dir is not None:
            out_dir = os.path.join(intan_data.intan_basepath, out_dir)
        else:
            out_dir = os.path.join(intan_data.intan_basepath, 'synced')
    print(f'Exporting signal times to {out_dir}')
    for signal_idx in range(len(signal_timings)):
        savepath_times = os.path.join(out_dir, f'{signal_types[signal_idx]}_times_raw.npy')
        np.save(savepath_times, signal_timings[signal_idx])