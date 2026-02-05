import numpy as np
from twop_pipeline.twop.getSuite2POutput import *
from twop_pipeline.twop.compute_twop import *
from twop_pipeline.utils.getFPS import scope_fs_from_xml
from pathlib import Path


def get_deltaF(*, s2p_out: Suite2POutput | None = None, suite2p_path: Path | None = None, synced_twop_path: Path | None = None,
               scope_fs=None, method='baseline', q=0.1, window_len=600, detrend=True,
                 F_neuropil=False, Fneu=None, ops_dict=None, neucoeff=None,
                 s2p_plane='plane0', save_csv=False, output_filepath=None, output_df=False):
    provided = [s2p_out is not None, suite2p_path is not None, synced_twop_path is not None]
    if sum(provided) != 1:
        raise ValueError("Provide exactly one of: s2p_out, suite2p_path, synced_twop_path")
    if suite2p_path is not None:
        s2p_out = Suite2POutput(suite2p_path, s2p_plane)
    if s2p_out is not None:
        F = s2p_out.F
        Fneu = s2p_out.Fneu
        cell_indices = s2p_out.cell_indices
        scope_fs = s2p_out.scope_fs
        ops_dict = s2p_out.ops_dict
    # elif synced_twop_path is not None:
    # 	F = numpy.load(synced_twop_path/manifest.npy"['F_source'], mmap_mode="r")
    #     Fneu = numpy.load(synced_twop_path/manifest.npy"['Fneu_source'], mmap_mode="r")
    dff = calc_deltaF_arrays(F, cell_indices, scope_fs, method=method, q=q, window_len=window_len, detrend=detrend,
                 F_neuropil=F_neuropil, Fneu=Fneu, ops_dict=ops_dict, neucoeff=neucoeff,
                 save_csv=save_csv, output_filepath=output_filepath, output_df=output_df)
    ###*** NOTE fix and move this logic into calc_deltaF_arrays
    if output_df:
        dff = pd.DataFrame(dff)
        if output_filepath is not None:
            if output_filepath.endswith('.parquet'):
                dff.to_parquet(output_filepath)
            elif output_filepath.endswith('.csv'):
                dff.to_csv(output_filepath)
        return dff 
    
    if output_filepath is not None:
        if not output_filepath.endswith('.npy'):
            output_filepath += '.npy'
        np.save(output_filepath, dff)
    return dff