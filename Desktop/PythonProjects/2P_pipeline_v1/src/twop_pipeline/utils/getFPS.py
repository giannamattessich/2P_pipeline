import xml.etree.ElementTree as ET
import os, numpy as np

def get_fps_from_xml(xml_file):
    if not os.path.exists(xml_file):
        raise ValueError('Experiment.XML file not found to get imaging FPS!!!')
    tree = ET.parse(xml_file)
    root = tree.getroot()
    lsm_info = root.findall('LSM')
    framerate = float(lsm_info[0].get('frameRate'))
    if root.find('LSM').get('averageMode') == '1':
        framerate = float(framerate) / float(root.find('LSM').get('averageNum'))
    return framerate

def get_camera_fps(camera_times, method='median'):
    '''OPTIONS: method = median or method = total'''
    if method == 'median':
        return 1 / np.median(np.diff(camera_times))
    else:
        return len(camera_times) / (camera_times[-1] - camera_times[0])

def scope_fs_from_xml(suite2p_path, scope_fs):
# check if can find scope fps from experiment meta data file (must be within same 2p folder in 'field_xx'), if not default to provided arg to function
    experiment_metadata_file = os.path.join(os.path.dirname(suite2p_path), 'Experiment.xml')
    if not os.path.exists(experiment_metadata_file):
        print(f"WARNING!!!! Experiment.xml file ({experiment_metadata_file}) not found in same directory as suite2p folder. \
               This will cause incorrect or failed downstream analyses if manual setting of scope_fs is incorrect.")
        scope_fs = scope_fs
    else:
        scope_fps = get_fps_from_xml(experiment_metadata_file)
        print(f'Found scope fps from Experiment.xml file: {scope_fps}')
        scope_fs = scope_fps    
    return scope_fs