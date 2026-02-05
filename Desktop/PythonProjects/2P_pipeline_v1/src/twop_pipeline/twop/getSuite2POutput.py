import os, traceback, numpy as np
from twop_pipeline.utils.getDataFiles import get2p_foldername_field
from twop_pipeline.utils.getFPS import scope_fs_from_xml

class Suite2POutput:
    """
    Class to initialize Suite2P output data for a given plane and perform further analyses after 2p ran

    Parameters:
        suite2p_path (str; Path-like): output folder after running suite2p

        plane (str, optional): plane in the format 'plane{plane #}', default is plane0

        scope_fs (float; default:1.366): capture rate of 2P scope
    """
    def __init__(self, suite2p_path, plane='plane0', scope_fs=None): 
        self.suite2p_path = find_s2p_datapath(suite2p_path)
        self.tif_folder = os.path.dirname(suite2p_path)
        self.scope_fs = scope_fs
        try:
            self.scope_fs = scope_fs_from_xml(self.suite2p_path, scope_fs=self.scope_fs)
        except:
            traceback.print_exc()
        plane_path = os.path.normpath(os.path.join(self.suite2p_path, plane))
        if not os.path.exists(plane_path):
            raise ValueError(f'{plane_path} is not a valid path containing suite2p data. Please check plane (default: "plane0")')
        else:
            suite2p_path = plane_path
        try:
            # load s2p output files into class 
            # flourescence, neuropil flourescence, iscell, options, spikes, and stats files, etc
            self.F = np.load(os.path.join(suite2p_path,'F.npy'), allow_pickle= True)
            self.Fneu = np.load(os.path.join(suite2p_path,'Fneu.npy'), allow_pickle= True)
            self.iscell = np.load(os.path.join(suite2p_path, 'iscell.npy'), allow_pickle= True)[:, 0].astype(bool)
            self.ops = np.load(os.path.join(suite2p_path, 'ops.npy'), allow_pickle= True)
            self.ops_dict = self.ops[()]
            self.spks = np.load(os.path.join(suite2p_path, 'spks.npy'), allow_pickle= True)
            self.stat = np.load(os.path.join(suite2p_path, 'stat.npy'), allow_pickle= True)
            self.rois, self.nframes = self.F.shape[0], self.F.shape[1] - 1
            self.cell_indices = np.where(self.iscell == True)[0]
            self.num_cells = len(self.cell_indices)
        except Exception:
            traceback.print_exc()

def find_s2p_datapath(suite2p_path):
    # # if basepath accidentally provided, try checking if suite2p folder exists within
    # # provided suite2p_path
    if not suite2p_path.endswith('suite2p') or not os.path.exists(suite2p_path):
        poss_paths = [os.path.join(suite2p_path, 'suite2p'),
                        get2p_foldername_field(suite2p_path)]
        for poss_path in poss_paths:
            if poss_path is not None:
                if os.path.exists(poss_path):
                    suite2p_path = poss_path
    print(f'Found Suite2P Path {suite2p_path}!')
    return suite2p_path