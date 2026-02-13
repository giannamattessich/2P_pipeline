import os, time
from twop_pipeline.intan.IntanData import *
from twop_pipeline.state.getFacemapOutput import FacemapOutput
from twop_pipeline.utils.io import ensure_dir, save_npy, save_parquet, write_json
from twop_pipeline.utils.filtering import *
from twop_pipeline.utils.getFPS import *
from twop_pipeline.state.getState import *

class FacemapSync:

    def __init__(self, facemap_output: FacemapOutput, intan_data: IntanData, out_dir_name = 'synced'):
        self.facemap_output = facemap_output
        self.intan_data = intan_data
        self.facemap_data = facemap_output.facemap_data
        self.out_dir = os.path.join(self.intan_data.intan_basepath, out_dir_name)
        self.camera_times, self.camera_times_end = self.intan_data.camera_times, self.intan_data.camera_times_end       
        self.saved_outputs = {}

    def run(self, overwrite: bool = True, save_manifest: bool = True,
             overwrite_manifest: bool = True, save_motion_npy: bool = False,
             save_pupil_data: bool = False, save_paw_data: bool = False,
             smoothing_kernel: int = 5, movement_percentile: int = 70, min_duration_s = 1,
             motion_indices ={ 'motion':1}, min_max_norm: bool = False, annotate_state: bool = False) -> "FacemapSync":
        if self.camera_times is None:
            raise ValueError('No camera timings provided from IntanData. Ensure that a channel was provided' \
            'when instantiating the object')
        self.out_dir = ensure_dir(self.out_dir)
        if not overwrite:
            return
        state_dataframe = None
        try:
            annotate_state_pupil = False
            if save_pupil_data and annotate_state:
                annotate_state_pupil = True
            state_dataframe = get_state_df(self.facemap_data, self.camera_times,
                                        treadmill_signal = self.intan_data.treadmill_raw,
                                        smoothing_kernel= smoothing_kernel, motion_indices = motion_indices,
                                            min_duration_s = min_duration_s, movement_percentile=movement_percentile,
                                            pupil_data = save_pupil_data, paw_data = save_paw_data,
                                            annotate_state = annotate_state,
                                              annotate_state_with_pupil = annotate_state_pupil,
                                              min_max_norm = min_max_norm)
        except:
            print('Failed to make state dataframe')
            traceback.print_exc()
        out_parquet_path = os.path.join(self.out_dir, 'facemap_data.parquet')
        save_parquet(state_dataframe, out_parquet_path, overwrite=overwrite)
        self.saved_outputs['facemap_data_synced'] = out_parquet_path
        if save_motion_npy:
            motion_npy = os.path.join(self.out_dir, 'motion.npy')
            save_npy(motion_npy, state_dataframe['motion'])
            self.saved_outputs['motion_data_synced'] = motion_npy
        if save_manifest and overwrite_manifest:
            self.save_manifest(overwrite=overwrite_manifest)
        return self        

    def save_manifest(self, overwrite: bool = True) -> None:
        """
        Save basic provenance.
        """
        manifest = {
            "created_unix": time.time(),
            "facemap_path": str(self.facemap_output.facemap_path),
            "outputs": self.saved_outputs,
            "notes": "Minimal manifest; extend with git commit, params, hashes, QC later.",
        }
        manifest_out_file = os.path.join(self.out_dir, "facemap_manifest.json")
        write_json(manifest_out_file, manifest, overwrite=overwrite)
        print(f'Saved manifest to {manifest_out_file}')