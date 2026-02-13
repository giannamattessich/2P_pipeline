import traceback 
import os, numpy as np

class FacemapOutput:
    """
    Class to initialize Suite2P output data for a given plane and perform further analyses after 2p ran

    Parameters:
        facemap_path (str; Path-like): output folder containing facemap output files. One of the following:
            ..._proc.npy file 
            ..._proc.mat file
    """
    def __init__(self, facemap_path):
        self.facemap_path = facemap_path
        if not os.path.exists(self.facemap_path):
            raise ValueError(f'Provided facemap path: {facemap_path} does not exist.')
        self.facemap_data = None
        try:
            self.facemap_data = get_facemap_data(self.facemap_path)
        except:
            traceback.print_exc()
            raise ValueError('Could not load facemap data')
        
def get_facemap_data(data_basepath):
    """
    HELPER FUNCTION TO INPUT DATA BASEPATH OF WHERE FACEMAP OUTPUT IS STORED,
    OUTPUT IS DICT WITH FACEMAP DATA-> if numpy file is saved it will load data 
    from numpy file. if not found, try to load .mat 

    Args:
        data_basepath (str): Path to directory where facemap data is stored

    Returns:
        facemap_data (dict): Loaded facemap data 
    """
    file_type = None
    for file in os.listdir(data_basepath):
        # if numpy file found, break loop
        if file.endswith('_proc.npy'):
            facemap_file_path = os.path.join(data_basepath, file)
            file_type = 'npy'
            break
        # only use mat file if numpy file doesnt exist
        elif file.endswith('_proc.mat'):
            facemap_file_path = os.path.join(data_basepath, file)
            file_type = 'mat'
    if file_type is None:
        print(f'WARNING!! The facemap file was not found in the path {data_basepath}')
    if file_type == 'npy':
        facemap_data = np.load(facemap_file_path, allow_pickle=True).item()
    elif file_type == 'mat':
        import scipy.io as sio
        facemap_data = sio.loadmat(facemap_file_path)
    print(f'Found facemap file path {facemap_file_path}')
    return facemap_data 