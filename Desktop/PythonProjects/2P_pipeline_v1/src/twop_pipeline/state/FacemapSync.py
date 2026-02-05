import os
from twop_pipeline.intan.IntanData import *
from twop_pipeline.utils.alignmentFunctions import align_scope_triggers_to_frames
from twop_pipeline.state.getFacemapOutput import FacemapOutput
from twop_pipeline.utils.io import ensure_dir, save_npy

class FacemapSync:

    def __init__(self, s2p_output: Suite2POutput, intan_data: IntanData, out_dir_name = 'synced'):
        
        self.s2p_output = s2p_output
        self.intan_data = intan_data
        self.out_dir = os.path.join(self.intan_data.intan_basepath, out_dir_name)
        self.scope_times, self.scope_times_end = self.intan_data.scope_times, self.intan_data.scope_times_end
        try:
            self.scope_times, self.scope_times_end = align_scope_triggers_to_frames(self.s2p_out, self.scope_times)
        except:
            print(f'Did not realign scope times')
        self.frame_times_synced = self.scope_times

    def run(self, overwrite: bool = False, save_manifest: bool = True, overwrite_manifest: bool = True) -> "TwoPSync":
        """
        Compute or validate frame_times_universal.
        Minimal: require it to be provided.
        """
        if self.frame_times_synced is None:
            raise ValueError(
                "Minimal TwoPSync requires frame_times_synced to be provided. "
                "Later you can compute this from Intan scope triggers."
            )

        self.out_dir = ensure_dir(self.out_dir)
        save_npy(os.path.join(self.out_dir, "frame_times_synced.npy"), self.frame_times_synced, overwrite=overwrite)
        if save_manifest:
            self.save_manifest(overwrite=overwrite_manifest)
        return self

    def save_manifest(self, overwrite: bool = True) -> None:
        """
        Save basic provenance.
        """
        manifest = {
            "created_unix": time.time(),
            "twop_suite2p_path": str(self.s2p_output.suite2p_path),
            "outputs": {
                "frame_times_universal": "frame_times_universal.npy",
            },
            "notes": "Minimal manifest; extend with git commit, params, hashes, QC later.",
        }
        manifest_out_file = os.path.join(self.out_dir, "twop_manifest.json")
        write_json(manifest_out_file, manifest, overwrite=overwrite)
        print(f'Saved manifest to {manifest_out_file}')