import os, traceback, numpy as np
import twop_pipeline.intan.readIntanHeader as rhd_utils
from twop_pipeline.intan.IntanQC import *
from twop_pipeline.utils.alignmentFunctions import get_analog_times

class IntanData:

    def __init__(self, intan_basepath,
                  twop_channel=None, pd_channel=None,
                    camera_channel=None, treadmill_channel=None, 
                    plot_intan=False, intan_plot_start_s=None, intan_plot_end_s=None,
                      save_plot=False, plot_save_filename=None):
        
        self.intan_basepath = intan_basepath
        # initialize recording channels info
        self.twop_chan = twop_channel
        self.pd_chan = pd_channel
        self.camera_chan = camera_channel
        self.treadmill_chan = treadmill_channel
        # setup plotting info
        self.plot_intan = plot_intan
        self.intan_plot_start_s = intan_plot_start_s
        self.intan_plot_end_s = intan_plot_end_s
        self.save_plot = save_plot
        self.plot_save_filename = plot_save_filename

        # get all data
        self.amp_analog_aux_in, self.intan_header, self.time_file = self.get_intan_files()

        self.data, self.intan_fs, self.convertUnitsVolt, self.intan_header = self.get_intan_data()
        
        self.photodiode_raw, self.twop_raw, self.camera_raw, self.treadmill_raw = self.get_all_intan_signals()  

                ## get times in seconds of TTL triggers for scope, photodiode, camera, and treadmill
        self.scope_times, self.scope_times_end = get_analog_times(self.twop_raw, upTransition=True, signal_name='scope')
        self.pd_times, self.pd_times_end = get_analog_times(self.photodiode_raw, signal_name='photodiode')
        self.camera_times, self.camera_times_end = get_analog_times(self.camera_raw, signal_name='camera')
        self.treadmill_times, self.treadmill_times_end = get_analog_times(self.treadmill_raw, signal_name='treadmill') 

        # return name of intan analog recording file and intan header file
    def get_intan_files(self):
        """
        Given the data basepath, find .dat intan files containing the recording data. 

        If amp_analog_aux file (concatenated data file of all input signals) exists, return this.
        If not found, return analogin.dat file (nonconcatenated analog signals data).

        Args:
            intan_basepath (str, Path-like): data filepath of directory containing intan files 
                                            directory must contain:
                                                - either 'amplifier_analogin_auxiliary_int16.dat' OR 'analogin.dat'
                                                - 'info.rhd'
        Returns:
            amp_analog_aux_in (str): filepath name of file containing signals data
            intan_header (dict): dictionary containing header info from found info.rhd file
            time_file (str, None): filepath of time.dat file, None if not found
        """
        # === Locate Intan analog input file ===
        intan_basepath = self.intan_basepath
        amp_analog_aux_in = os.path.join(intan_basepath, 'amplifier_analogin_auxiliary_int16.dat')
        basename = os.path.basename(intan_basepath)
        if not os.path.exists(amp_analog_aux_in):
            for poss_file in [f"{basename}.dat", "analogin.dat"]:
                path_candidate = os.path.join(intan_basepath, poss_file)
                if (os.path.exists(path_candidate)):
                    if os.path.getsize(path_candidate) != 0:
                        amp_analog_aux_in = path_candidate
                        break
                    print(f'WARNING!! Found candidate path file {path_candidate} in basepath, but it is empty. \
                        Please check file names and their sizes: the data file should be called\
                        amp_analogin_auxiliary_int16.dat file, (basepath).dat or analogin.dat')
            else:
                raise ValueError('No valid analog input file found in intan_basepath.')
        # attempt to find time.dat file. if not found it is ok as this does not contain signal amplitude info
        time_file = os.path.join(intan_basepath, 'time.dat')
        if not os.path.exists(time_file):
            time_file = None
            print('Warning: could not infer channel #s from missing time.dat file.')
        # Load Intan info header
        info_file = os.path.join(intan_basepath, 'info.rhd')
        if not os.path.exists(info_file):
            raise ValueError('Info file (info.rhd) not found in intan_basepath.')
        ## read intan header for info 
        with open(info_file, 'rb') as f:
            intan_header = rhd_utils.read_header(f)
        return amp_analog_aux_in, intan_header, time_file
    
    def get_intan_data(self):
        """
        Read from intan header to get number timepoints and channel information, all signals data, volt conversion units for file type

        Args:
            intan_basepath (str, Path-like): data filepath of directory containing intan files 
                                            directory must contain:
                                                - either 'amplifier_analogin_auxiliary_int16.dat' OR 'analogin.dat'
                                                - 'info.rhd'
            plot_intan (bool; default False): whether to plot with all signals plotted

            intan_plot_start_s (int; default None): start in seconds of intan plot if plot_intan == True

            intan_plot_end_s (int; default None): end in seconds of intan plot if plot_intan == True
        Returns:
            data (np.ndarray / numpy memorymap): numpy mmap of shape (num_channels, num_samples)
            fs_analog (sample rate of intan; default=20e3):"
            convertUnitsVolt (float)
            intan_header (dict)
        """
        # === Locate Intan analog input file ===
        amp_analog_aux_in, intan_header, time_file = self.amp_analog_aux_in, self.intan_header, self.time_file
        fs_analog = intan_header['sample_rate']
        # Determine data type and microvolt conversion
        if 'analogin.dat' in amp_analog_aux_in:
            dtype = 'uint16'
            convertUnitsVolt = 0.000050354
        else:
            dtype = 'int16'
            convertUnitsVolt = 0.00010071
        # calc num channels from header, if available use time.dat file instead
        num_channels = (len(intan_header['amplifier_channels']) +
                        len(intan_header['aux_input_channels']) +
                        len(intan_header['board_adc_channels']))
        analog_filesize = os.path.getsize(amp_analog_aux_in)
        num_samples_total = analog_filesize // np.dtype(dtype).itemsize
        # uncomment if you have ONLY a time.dat file. WARNING: analog data is not located here 
        #if os.path.exists(time_file):
        #     # get file size, each sample is int32 (4 bytes)
        #     inferred_channels = num_channels
        #     #num_time_samples = os.path.getsize(time_file) // 4
        #     #num_channels = num_samples_total // num_time_samples
        #     if inferred_channels != num_channels:
        #         print('Warning! Number channels from time samples differ from header!')
        num_timepoints = num_samples_total // num_channels
        # Memory-map analog data file
        mmap = np.memmap(amp_analog_aux_in, dtype=dtype, mode='r')
        data = mmap.reshape((num_timepoints, num_channels)).T
        if self.plot_intan:
            if self.intan_plot_start_s is not None:
                if self.intan_plot_end_s is None:
                    self.intan_plot_end_s = num_timepoints // fs_analog
                plot_raw_intan(data, start_s=self.intan_plot_start_s, end_s=self.intan_plot_end_s,
                               intan_fs=fs_analog, save_plot=self.save_plot, plot_save_filename=self.plot_save_filename)
            else:
                traceback.print_exc()
                print(f'Attempted to create raw intan plot: intan time not provided')
        return data, fs_analog, convertUnitsVolt, intan_header

    def get_all_intan_signals(self):
    ## PROVIDE ANALOG CHANNELS AS NUM ADC CHANNEL (0-8), NOT ANALOG/AUX TOTAL

        """
        Extract and load data from whole basepath: including 2P and intan data
        
        Args:

            intan_basepath (str, Path-like): path of directory where intan data is located 

            twop_chan (int; default 2): recording channel for scope

            pd_chan (int; default 5): photodiode channel number

            camera_chan (int; default 3): camera channel number

            treadmill_chan (int; default 6): treadmill channel number 

        Returns:

            fs_intan (default is 20e3): intan sampling rate

            phodiode_raw (np.array): raw photodiode signal, None if no channel provided

            twop_raw (np.array): raw 2P scope signal, None if no channel provided

            camera_raw (np.array): raw camera TTL signal, None is no channel provided

            treadmill_raw (np.array): raw treadmill signal, None if no channel

        """

        ###NOTE: probably dont need this but saving for later to test more EPHYS recordings
        # if amp channels were recorded, add number amp channels to analog channels, as the 
        # amplifier_analogin_auxiliary_int16.dat file is concatenated with ALL channels
        # if not keep the same analog channel numbers
        #num_amp_channels = self.intan_header['num_amplifier_channels']
        # if num_amp_channels > 0:
        #     if twop_chan is not None:
        #         twop_chan += num_amp_channels
        #     if pd_chan is not None:
        #         pd_chan += num_amp_channels
        #     if camera_chan is not None:
        #         camera_chan += num_amp_channels
        #     if treadmill_chan is not None:
        #         treadmill_chan += num_amp_channels
        photodiode_raw, twop_raw, camera_raw, treadmill_raw = None, None, None, None
        if self.pd_chan is not None:
            try:
                photodiode_raw = self.data[self.pd_chan] * self.convertUnitsVolt
            except:
                print(f'Could not find photodiode data, or channel # was not correctly provided.')
        if self.twop_chan is not None:
            try:
                twop_raw = self.data[self.twop_chan] * self.convertUnitsVolt
            except:
                traceback.print_exc()
                print(f'Could not find 2P trigger data, or channel # was not correctly provided.')
        if self.camera_chan is not None:
            try:
                camera_raw = self.data[self.camera_chan] * self.convertUnitsVolt
            except:
                print(f'Could not get camera data, or channel # was not correctly provided.')
        if self.treadmill_chan is not None:
            try:
                treadmill_raw = self.data[self.treadmill_chan] * self.convertUnitsVolt
            except:
                print(f'Could not find treadmill data, or channel # was not correctly provided.')
        return photodiode_raw, twop_raw, camera_raw, treadmill_raw