import numpy as np, os, traceback

def plot_raw_intan(intan_data, start_s, end_s, intan_fs=20e3, save_plot=False, plot_save_filename=None):
    start, end = int(start_s*intan_fs), int(end_s * intan_fs)
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(intan_data.shape[0], 1, figsize=(8, 12))
    for chan in range(intan_data.shape[0]):
        axs[chan].plot(np.arange(start, end), intan_data[chan][start:end], color='black')
    if save_plot and plot_save_filename is not None:
        try:
            plt.savefig(plot_save_filename)
        except:
            traceback.print_exc()
    plt.suptitle('Recorded channel data')
    plt.tight_layout()
    plt.show()