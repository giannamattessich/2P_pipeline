import os, traceback, shutil
import numpy as np
import pickle, joblib


'''
Generic function to load .pkl file into memory

Args:
    file_path: .pkl file to read

Returns:
    data(np.ndarray): data from file
'''
def load_pickle_file(file_path):
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    return data

# create an array of len (ncells_TOTAL, nframes_TOTAL) by stacking values of all recording and filling with nan for recordings that 
# have less frames than the max num of frames in recordings
def pad_and_stack_vals(values_dict, s2p_outs_dict):
    max_frames_group = max({recording:s2p_out.nframes for recording,s2p_out in s2p_outs_dict.items()}.values())
    padded_arrs = {recording:np.pad(value_arr, pad_width=((0, 0), (0, max_frames_group - value_arr.shape[1])), constant_values=np.nan) 
                            for recording, value_arr in values_dict.items()}
    flat_valuelist = list(padded_arrs.values())
    stacked_arr = np.vstack(flat_valuelist)
    return stacked_arr

def rename_dat(rec_path):
    rec = os.path.basename(rec_path)
    new_dat_path = os.path.join(rec_path, f'{rec}.dat')
    dat_file_to_rename = None
    if not os.path.exists(new_dat_path):
        for file in os.listdir(rec_path):
            if os.path.isfile(os.path.join(rec_path, file)):
                if file == 'amplifier_analogin_auxiliary_int16.dat':
                    dat_file_to_rename = os.path.join(rec_path, file)
                elif file == 'analogin.dat':
                    if os.path.getsize(os.path.join(rec_path, 'analogin.dat')) != 0:
                        dat_file_to_rename = os.path.join(rec_path, file)
    else:
        return
    if dat_file_to_rename is not None:
        print(f'Renaming {dat_file_to_rename} for {new_dat_path}')   
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm == 'y':
            print("Continuing...")
        elif confirm == 'n':
            print("Terminating.")
            exit()
        os.rename(dat_file_to_rename, new_dat_path)
    else:
        print(f'Found no intan dat to rename. Skipping rec {rec_path}')

def rename_all_dats(rec_dirnames):
#def rename_dat_to_base(rec_dirnames):
    for day_path in rec_dirnames:
        rename_dat(day_path)

def copy_neuroscope_xml(source_xml, rec_dirnames):
    if not source_xml.endswith('.xml'):
        # try to see if directory was provided by accident
        source_xml = os.path.join(source_xml, f'{os.path.basename(source_xml)}.xml')
    if not os.path.exists(source_xml):
        raise ValueError(f'Provided source xml does not exist.')
    for day_path in rec_dirnames:
        xml_path = os.path.join(day_path, f'{os.path.basename(day_path)}.xml')
        if not os.path.exists(xml_path):
            shutil.copy(source_xml, xml_path)
            print(f'Copied {source_xml} to {day_path}!')

# def delete_xmls(source_day, datapaths):
#     del_files = [os.path.join(path, f'{os.path.basename(path)}.xml') for path in datapaths if not path.endswith('p9')]
#     for file in del_files:
#         os.remove(file)

def get2p_foldername_field(data_basepath):
    """ 
    Get 2P folder name, and append suite2p path to get the datapath of suite2p files.
    ***NOTE: this only works if you have data saved under folder starting with the word 'field'

    Args:
        data_basepath (str): parent base folder of tif files
    Returns:
        suite2p folder path (str): path to s2p folder
    """
    files = os.listdir(data_basepath)
    foldername = ''
    for folder in files:
        if folder.lower().startswith('field'):
            foldername = os.path.join(data_basepath, folder)
    if foldername == '':
        return None
    return os.path.join(data_basepath, foldername, 'suite2p')

def get_recording_paths_sorted(basepath):
    rec_paths = [
        os.path.join(basepath, rec_path) for rec_path in os.listdir(basepath) if not rec_path.endswith('stim') and rec_path.startswith('p')]
    days = []
    for path in rec_paths:
        day = os.path.basename(path)
        days.append(int(day[1:]))
    days = sorted(days)
    days = [os.path.join(basepath, f'p{str(day)}') for day in days]    
    return days