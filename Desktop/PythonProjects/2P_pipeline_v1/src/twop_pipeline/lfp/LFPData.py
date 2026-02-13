from twop_pipeline.intan.IntanData import *
from twop_pipeline.lfp.readLFP import *

class LFPData:
    def __init__(self, basepath, intan_data: IntanData, channels, out_fs = 1250, out_dir = None):
        self.basepath = basepath
        self.intan_data = intan_data
        self.header = self.intan_data.intan_header
        self.channels = channels
        self.out_fs = out_fs
        if out_dir is None:
            self.out_dir = basepath
        else:
            self.out_dir = out_dir

    def run_extract(self, 
                    out_fs: int = 1250,
                    lopass: float = 450.0,
                    overwrite = True,
                    output_lfppath: str = None,
                    csv_savepath: str = None,
                    return_data: bool = True,
                    chunk_size: int = 2_000_000,           # input samples per chunk (at in_fs)
                    raw_memmap: np.ndarray | np.memmap = None,  # <- OPTIONAL: preallocated raw matrix (samples, total_channels)
                    dtype_in = np.int16):

        extract_lfp(self.basepath,
                        intan_header=self.header,
                        channels = self.channels,
                        out_fs = out_fs,
                        lopass = lopass,
                        overwrite = overwrite,
                        output_lfppath = output_lfppath,
                        csv_savepath = csv_savepath,
                        return_data =  return_data,
                        chunk_size = chunk_size,           # input samples per chunk (at in_fs)
                        raw_memma = raw_memmap,  # <- OPTIONAL: preallocated raw matrix (samples, total_channels)
                        dtype_in = dtype_in
                        )
        
def load(self, lfp_source=None, num_channels=2):
    if lfp_source is None:
        for file in os.listdir(self.out_dir):
            if file.endswith('.lfp'):
                lfp_source = os.path.join(self.out_dir, file)
    load_lfp(lfp_source, num_channels=num_channels)

def lfp_times(self, export=False):
    intan_sampling_rate = self.header['']