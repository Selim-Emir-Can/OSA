import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

def get_thermal(batch_idx, order=2):
    # thermal = np.mean(bandpass_filter(batch_idx["thermal"][0,:,:,:], order=order), axis=(-2,-1))
    thermal = np.mean(batch_idx["thermal"][0,:,:,:], axis=(-2,-1))
    return thermal

def get_stats(pred, gt):
    tp = np.sum(pred * gt)
    fp = np.sum(pred * (1-gt))
    tn = np.sum((1-pred) * (1-gt))
    fn = np.sum((1-pred) * gt)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    accuracy = (tp + tn)/ (tp + tn + fp + fn)
    tpr = tp / (tp + fn)
    fpr = fp / (fp + tn)
    confusion_matrix = np.array([[tp, fn], [fp, tn]])
    return precision, recall, accuracy, confusion_matrix

def plot_classification_waveforms(time_axis, breathing_signal, groundtruth, estimated, gt_breathing=None):
    plt.figure(figsize=(10, 4))
    plt.plot(time_axis, groundtruth, color='blue', linewidth=4, label='Ground Truth Apnea Signal')
    plt.plot(time_axis, estimated, linestyle='--', color='red', linewidth=2, label='Estimated Apnea Signal')
    plt.plot(time_axis, breathing_signal, color='black', label='Thermal Image Signal')
    if(gt_breathing is not None):
        plt.plot(time_axis, gt_breathing, color='orange', label='Ground Truth Breathing Signal')
    for pos in ['right', 'top']: 
        plt.gca().spines[pos].set_visible(False) 
    # plt.yticks([-1, 1])
    font2 = {'family':'serif','color':'darkred','size':10}
    plt.ylabel('Amplitude', fontdict=font2) # Remove the y-axis label
    plt.xlabel('Time [sec]', fontdict=font2)
    mpl.rc('font',family='serif')

def hl_envelopes_idx(s, dmin=1, dmax=1, split=False):
    """
    Input :
    s: 1d-array, data signal from which to extract high and low envelopes
    dmin, dmax: int, optional, size of chunks, use this if the size of the input signal is too big
    split: bool, optional, if True, split the signal in half along its mean, might help to generate the envelope in some cases
    Output :
    lmin,lmax : high/low envelope idx of input signal s
    """
    lmin = (np.diff(np.sign(np.diff(s))) > 0).nonzero()[0] + 1 
    # locals max
    lmax = (np.diff(np.sign(np.diff(s))) < 0).nonzero()[0] + 1

    lmin = lmin[[max(i-dmin//2,0)+np.argmin(s[lmin[max(i-dmin//2,0):min(i+dmin//2,len(lmin))]]) for i in range(0,len(lmin),1)]]
    lmax = lmax[[max(i-dmax//2,0)+np.argmax(s[lmax[max(i-dmax//2,0):min(i+dmax//2,len(lmax))]]) for i in range(0,len(lmax),1)]]
    
    return lmin,lmax

def detect_NUKS(x):
    list_idx = []
    indexes = []
    i = 0
    while(i < (len(x)-1)):
        # getting Consecutive elements 
        if x[i] == x[i + 1]:
            while((i < (len(x)-1)) and (x[i] == x[i + 1])):
                indexes.append(i)
                i = i + 1
            list_idx.append(indexes)
            indexes = []
        i = i + 1
    for k in list_idx:
        if(len(k) > 30):
            return(True)
    return(False)

def detect_mode_lock(dataset_obj, idx):
    frame = dataset_obj[idx]["thermal"][0,0,:,:]
    return((frame == frame[0,0]).all())


def movement_detector(thermal, dmin=29, dmax=31, th=4.5, plot=False):

    lmin, lmax = hl_envelopes_idx(thermal, dmin=dmin, dmax=dmax)

    min_env = thermal[lmin]
    max_env = thermal[lmax]
    half_len = 4 

    dists_min = []
    dists_max = []
   
    for i in range(1, len(max_env)-1):
        vec_start = max(0, i - half_len)
        vec_end = min(len(max_env), i + half_len)
        vec = max_env[vec_start:vec_end]
        vec = np.array(vec)
        center_vec = np.repeat(max_env[i], len(vec))
        dist = np.sum((center_vec - vec)**2)/((1 or np.median(vec[np.argsort(vec)[::-1]]))*len(vec))
        dists_max.append(dist)

    for i in range(1, len(min_env)-1):
        vec_start = max(0, i - half_len)
        vec_end = min(len(min_env), i + half_len)
        vec = min_env[vec_start:vec_end]
        vec = np.array(vec)
        center_vec = np.repeat(min_env[i], len(vec))
        dist = np.sum((center_vec - vec)**2)/((1 or np.median(vec[np.argsort(vec)[::-1]]))*len(vec))
        dists_min.append(dist)

    dists_min = np.array(dists_min)
    dists_max = np.array(dists_max)
    if(plot == True):
        t_arr = np.linspace(0, len(thermal)/30, len(thermal))
        lx = t_arr[lmin][1:-1]
        mx = t_arr[lmax][1:-1]
        plt.plot(lx, dists_min)
        plt.plot(mx, dists_max)
        plt.show()
    ld, ud = max(dists_min), max(dists_max)
    if((ld > th) or (ud > th)):
        return(True)
    return(False)

def vid_movement_detector(thermal_vid, lb=12, ub=100):
    diff_arr = np.diff(thermal_vid, axis=0)
    mean_arr = np.std(diff_arr**2, axis=(1,2))
    if((np.std(mean_arr) < ub) and (np.std(mean_arr) > lb)):
        return(False)
    return(True)

def vid_std(thermal_vid):
    diff_arr = np.diff(thermal_vid, axis=0)
    mean_arr = np.std(diff_arr**2, axis=(1,2))
    return(np.std(mean_arr))

def plot_envelope(t_arr, thermal, dmin, dmax):
    lmin, lmax = hl_envelopes_idx(thermal, dmin=dmin, dmax=dmax)
    if(len(lmin) == 0 or len(lmax) == 0): # signal has no contrast
        return
    lx = t_arr[lmin]
    mx = t_arr[lmax]

    min_env = thermal[lmin]
    max_env = thermal[lmax]
    # dists_min, dists_max = get_motion_scores(max_env, min_env, half_len=2)
    # ld, ud = max(dists_min), max(dists_max)
    # if((ld > 4) or (ud > 4)):
    #     print('there is movement peak: ', True)
    # else:
    #     print('there is movement peak: ', False)
    plt.plot(lx, min_env, 'ro-', label='low')
    plt.plot(mx, max_env, 'go-', label='high')
    plt.plot(t_arr, thermal, color='black', label='Thermal Image Signal')
    plt.xlabel("Time (s)")
    plt.legend()
    plt.show()
    return

def predict(thermal, dmin, dmax, th, mode='max', percentage=25, interval=None, plot=False):
    """
    Input: 
    thermal: 1d-array, thermal signal
    dmin, dmax: int, optional, size of chunks
    th: float, threshold value
    mode: str, optional, mode of thresholding
    Output:
    pred: 1d-array, binary prediction
    """
    
    t_arr = np.linspace(0, len(thermal)/30, len(thermal))
    lmin, lmax = hl_envelopes_idx(thermal, dmin=dmin, dmax=dmax)
    print("lmin: ", len(lmin), "lmax: ", len(lmax), '\n')
    if(len(lmin) == 0 or len(lmax) == 0): # signal has no contrast
        return np.zeros(len(thermal))
    max_th = np.interp(t_arr, t_arr[lmax], thermal[lmax])
    min_th = np.interp(t_arr, t_arr[lmin], thermal[lmin])

    pred = None
    cn = None
    if(mode == 'max'):
        pred = ((max_th - min_th)/max(max_th - min_th) < th).astype(int)
        cn = max(max_th - min_th)
    elif(mode == '90th'):
        pred = ((max_th - min_th)/np.percentile(max_th - min_th, 90) < th).astype(int)
        cn = np.percentile(max_th - min_th, 90)
    elif(mode == 'median'):
        pred = ((max_th - min_th)/np.median(max_th - min_th) < th).astype(int)
        cn = np.median(max_th - min_th)
    elif(mode == 'mean'):
        pred = ((max_th - min_th)/np.mean(max_th - min_th) < th).astype(int)
        cn = np.mean(max_th - min_th)
    else:
        pred = ((max_th - min_th)/np.percentile(max_th - min_th, percentage) < th).astype(int)
        cn = np.percentile(max_th - min_th, percentage)
    
    if(plot == True):
        if(len(lmin) == 0 or len(lmax) == 0): # signal has no contrast
            return
        if(interval is not None):
            t_arr = t_arr + interval[0]/30
        lx = t_arr[lmin]
        mx = t_arr[lmax]

        min_env = thermal[lmin]
        max_env = thermal[lmax]
        dists_min, dists_max = get_motion_scores(max_env, min_env, half_len=2)
        plt.plot(lx, min_env, 'ro-', label='low env')
        plt.plot(mx, max_env, 'go-', label='high env')
        plt.plot(t_arr, thermal, color='black', label='Thermal Video Mean Over Time')
        # plt.title("Thermal Signal with Envelope")
        # plt.ylabel("Amplitude")
        # plt.xlabel("Time (s)")
        # plt.tick_params(
        #                 axis='x',          # changes apply to the x-axis
        #                 which='both',      # both major and minor ticks are affected
        #                 bottom=False,      # ticks along the bottom edge are off
        #                 top=False,         # ticks along the top edge are off
        #                 labelbottom=False) # labels along the bottom edge are off
        # plt.tick_params(
        #                 axis='y',          # changes apply to the y-axis
        #                 which='both',      # both major and minor ticks are affected
        #                 bottom=False,      # ticks along the bottom edge are off
        #                 top=False,         # ticks along the top edge are off
        #                 labelbottom=False) # labels along the bottom edge are off
        plt.axis('off')

        # plt.legend()
        plt.show()

        plt.plot(lx, dists_min, label='low')
        plt.plot(mx, dists_max, label='high')
        plt.title("Thermal Envelope Point Distance to Neighbors")
        plt.show()

        plt.plot(t_arr, (max_th - min_th)/cn, label='Normalized Envelope Difference')
        plt.plot(t_arr, pred, label='Prediction')
        plt.title("Thermal Pred Before Thresholding")
        plt.xlabel("Time (s)")
        plt.ylabel("Normalized Difference")
        plt.legend()
        plt.show()
    return pred

def get_motion_scores(max_env, min_env, half_len=2):
    start_vec = [(max_env[0]-max_env[1+i])**2 for i in range(half_len)]

    dists_max = [np.sum(start_vec)/len(start_vec)]

    for i in range(1, len(max_env)-1):
        vec_start = max(0, i - half_len)
        vec_end = min(len(max_env), i + half_len)
        vec = max_env[vec_start:vec_end]
        center_vec = np.repeat(max_env[i], len(vec))
        dist = np.sum((center_vec - vec)**2)/len(vec)
        dists_max.append(dist)

    end_vec = [(max_env[len(max_env)-1]-max_env[len(max_env)-2-i])**2  for i in range(half_len)]
    dists_max.append(np.sum(end_vec)/len(end_vec))


    start_vec = [(min_env[0]-min_env[1+i])**2 for i in range(half_len)]

    dists_min = [np.sum(start_vec)/len(start_vec)]

    for i in range(1, len(min_env)-1):
        vec_start = max(0, i - half_len)
        vec_end = min(len(min_env), i + half_len)
        vec = min_env[vec_start:vec_end]
        center_vec = np.repeat(min_env[i], len(vec))
        dist = np.sum((center_vec - vec)**2)/len(vec)
        dists_min.append(dist)

    end_vec = [(min_env[len(min_env)-1]-min_env[len(min_env)-2-i])**2  for i in range(half_len)]
    dists_min.append(np.sum(end_vec)/len(end_vec))
    return(dists_min, dists_max)

def get_motion_scores_v2(max_env, min_env, half_len=2):
    dists_min = []
    dists_max = []
 
    for i in range(1, len(max_env)-1):
        vec_start = max(0, i - half_len)
        vec_end = min(len(max_env), i + half_len)
        vec = max_env[vec_start:vec_end]
        vec = np.array(vec)
        center_vec = np.repeat(max_env[i], len(vec))
        dist = np.sum((center_vec - vec)**2)/((1 or np.median(vec[np.argsort(vec)[::-1]]))*len(vec))
        dists_max.append(dist)

    for i in range(1, len(min_env)-1):
        vec_start = max(0, i - half_len)
        vec_end = min(len(min_env), i + half_len)
        vec = min_env[vec_start:vec_end]
        vec = np.array(vec)
        center_vec = np.repeat(min_env[i], len(vec))
        dist = np.sum((center_vec - vec)**2)/((1 or np.median(vec[np.argsort(vec)[::-1]]))*len(vec))
        dists_min.append(dist)

    dists_min = np.array(dists_min)
    dists_max = np.array(dists_max)
    return(dists_min, dists_max)

################################################# RADAR #######################################################################
def movement_detector(thermal, dmin=29, dmax=31, plot=False, include_edges=False):

    lmin, lmax = hl_envelopes_idx(thermal, dmin=dmin, dmax=dmax)

    min_env = thermal[lmin]
    max_env = thermal[lmax]
    half_len = 4 

    dists_min = []
    dists_max = []

    if(include_edges == True):
        start_vec = [(max_env[0]-max_env[1+i])**2 for i in range(half_len)]
        start_vec = np.array(start_vec)
        dists_max.append(np.sum(start_vec)/((1 or np.mean(start_vec[np.argsort(start_vec)[::-1]]))*len(start_vec)))

   
    for i in range(1, len(max_env)-1):
        vec_start = max(0, i - half_len)
        vec_end = min(len(max_env), i + half_len)
        vec = max_env[vec_start:vec_end]
        vec = np.array(vec)
        center_vec = np.repeat(max_env[i], len(vec))
        dist = np.sum((center_vec - vec)**2)/((1 or np.mean(vec[np.argsort(vec)[::-1]]))*len(vec))
        dists_max.append(dist)

    if(include_edges == True):
        end_vec = [(max_env[len(max_env)-1]-max_env[len(max_env)-2-i])**2  for i in range(half_len)]
        end_vec = np.array(end_vec)
        dists_max.append(np.sum(end_vec)/((1 or np.mean(end_vec[np.argsort(end_vec)[::-1]]))*len(end_vec)))

        start_vec = [(min_env[0]-min_env[1+i])**2 for i in range(half_len)]
        start_vec= np.array(start_vec)
        dists_min.append(np.sum(start_vec)/((1 or np.mean(start_vec[np.argsort(start_vec)[::-1]]))*len(start_vec)))

    for i in range(1, len(min_env)-1):
        vec_start = max(0, i - half_len)
        vec_end = min(len(min_env), i + half_len)
        vec = min_env[vec_start:vec_end]
        vec = np.array(vec)
        center_vec = np.repeat(min_env[i], len(vec))
        dist = np.sum((center_vec - vec)**2)/((1 or np.mean(vec[np.argsort(vec)[::-1]]))*len(vec))
        dists_min.append(dist)

    if(include_edges == True):
        end_vec = [(min_env[len(min_env)-1]-min_env[len(min_env)-2-i])**2  for i in range(half_len)]
        end_vec = np.array(end_vec)
        dists_min.append(np.sum(end_vec)/((1 or np.mean(end_vec[np.argsort(end_vec)[::-1]]))*len(end_vec)))

    dists_min = np.array(dists_min)
    dists_max = np.array(dists_max)

    if(plot == True):
        t_arr = np.linspace(0, len(thermal)/30, len(thermal))

        if(len(lmin) == 0 or len(lmax) == 0): # signal has no contrast
            return
        lx = t_arr[lmin]
        min_env = thermal[lmin]

        mx = t_arr[lmax]
        max_env = thermal[lmax]

        
        dists_min, dists_max = get_motion_scores(max_env, min_env, half_len=2)
        plt.plot(lx, min_env, 'ro-', label='low')
        plt.plot(mx, max_env, 'go-', label='high')
        plt.plot(t_arr, thermal, color='black', label='Radar Signal')
        plt.title("Radar Signal with Envelope")
        plt.xlabel("Time (s)")
        plt.legend()
        plt.show()
        plt.plot(lx, dists_min, label='low')
        plt.plot(mx, dists_max, label='high')
        plt.title("Radar Envelope Point Distance to Neighbors")
        plt.show()


    return(dists_min, dists_max, lmin, lmax)

def find_movement_peaks(dists_min, dists_max, t_arr, th, x_th, lmin, lmax, plot=False):
    t_arr_min = t_arr[lmin]
    idx_min = []
    x_min = []
    y_min = []

    for i in range(len(dists_min)):
        if(dists_min[i] > th):
            idx_min.append(lmin[i])
            x_min.append(t_arr_min[i])
            y_min.append(dists_min[i])
    
    center_list_min = []
    cx_min = []
    iter = 0
    while((len(x_min) != 0) and (iter < len(y_min))):
        offset = 1
        avg_pos_arr = [(x_min[iter], y_min[iter], idx_min[iter])]
        while(((iter + offset) < len(y_min)) and (abs(x_min[iter] - x_min[iter+offset]) < x_th)):
            avg_pos_arr.append((x_min[iter+offset], y_min[iter+offset], idx_min[iter+offset]))
            offset += 1
        
        centers = []
        cx = []
        for xy in avg_pos_arr:
            x_min.remove(xy[0])
            y_min.remove(xy[1])
            idx_min.remove(xy[2])
            centers.append(xy[2])
            cx.append(xy[0])
        center_list_min.append(np.median(centers)) # can change this to be the mean
        cx_min.append(np.median(cx))

    t_arr_max = t_arr[lmax]
    idx_max = []
    x_max = []
    y_max = []

    for i in range(len(dists_max)):
        if(dists_max[i] > th):
            idx_max.append(lmax[i])
            x_max.append(t_arr_max[i])
            y_max.append(dists_max[i])
    
    center_list_max = []
    cx_max = []
    iter = 0
    while((len(x_max) != 0) and (iter < len(y_max))):
        offset = 1
        avg_pos_arr = [(x_max[iter], y_max[iter], idx_max[iter])]
        while(((iter + offset) < len(y_max)) and (abs(x_max[iter] - x_max[iter+offset]) < x_th)):
            avg_pos_arr.append((x_max[iter+offset], y_max[iter+offset], idx_max[iter+offset]))
            offset += 1
        
        centers = []
        cx = []
        for xy in avg_pos_arr:
            x_max.remove(xy[0])
            y_max.remove(xy[1])
            idx_max.remove(xy[2])
            centers.append(xy[2])
            cx.append(xy[0])
        center_list_max.append(np.median(centers)) # can change this to be the mean
        cx_max.append(np.median(cx))
    # print("Center List Max: ", center_list_max, '\n')
    # print("Center List Min: ", center_list_min, '\n')
    for i in range(len(center_list_max)):
        t = t_arr[int(center_list_max[i])]
        for j in range(len(center_list_min)):
            # print("t: ", t, "t_arr: ", t_arr[int(center_list_min[j])], '\n')
            # print(abs(t - t_arr[int(center_list_min[j])]), x_th, '\n')
            if((len(center_list_min) != 0) and (abs(t - t_arr[int(center_list_min[j])]) < x_th/30)):
                center_list_min.remove(center_list_min[j])
                cx_min.remove(cx_min[j])
                break
    center_list_max.extend(center_list_min)
    cx_max.extend(cx_min)

    if(plot == True):
        if(len(center_list_max) != 0):
            plt.scatter(cx_max, center_list_max)
            plt.title("center_list_max")
            plt.show()
        else:
            print("No movement detected")
    return center_list_max
    
def remove_peaks(center_list, sig, half_length=90):
    """
    Input: 
    center_list: list, indices of peaks
    sig: 1d-array, signal
    Output:
    sig: 1d-array, signal with peaks removed
    """
    signal_comps = []
    last_lower = -1
    for i in range(len(center_list)):
        cut_center = int(center_list[i])
        lower = max(0, cut_center-half_length)
        upper = min(len(sig), cut_center+half_length)
        # print("lower: ", lower, "upper: ", upper, '\n')
        if(i == 0):
            signal_comps.append([sig[:lower], [0, lower]])
            last_upper = upper
        if((i != (len(center_list) - 1)) and (i != 0)):
            signal_comps.append([sig[last_upper:lower], [last_upper, lower]])
            last_upper = upper
        if(i == (len(center_list) - 1)):
            signal_comps.append([sig[last_upper:lower], [last_upper, lower]])
            signal_comps.append([sig[upper:], [upper, len(sig)]])
    return signal_comps
################################################# DATA SORTING ################################################################
def get_patient_idxs(dataset, patient_ids=None):
    patient_idx_container = [ [] for _ in range(len(patient_ids)) ]

    for i in range(len(dataset.oversampling_idxs)):
        patient_id = dataset.trial_folders[dataset.oversampling_idxs[i][0]]
        for j in range(len(patient_ids)):
            if(patient_ids[j] in patient_id):
                patient_idx_container[j].append(i)
                break
    return patient_idx_container
################################################# SPECTOGRAM METHODS ##########################################################

from scipy import signal
from scipy.fft import fftshift
from scipy.fft import fft, fftfreq

def derivative(img):
    gx = img[...,:-1] - img[...,1:]
    return gx

def lowpass_filter(sig, fs=30, fc=0.5, order=2) -> np.ndarray:
    nyqs = 0.5 * fs
    normal_fc = fc / nyqs
    b,a = signal.butter(order, normal_fc, 'low', analog=False)
    filtered = signal.filtfilt(b,a,sig, axis=0)
    return filtered

def bandpass_filter(sig, fs=30, fc_low=5/60, fc_high=30/60, order=2) -> np.ndarray:
    nyqs = 0.5 * fs
    normal_fc_low = fc_low / nyqs
    normal_fc_high = fc_high / nyqs
    b,a = signal.butter(order, [normal_fc_low, normal_fc_high], 'band', analog=False)
    filtered = signal.filtfilt(b,a,sig, axis = 0)
    return filtered

# not sure if this gives the desired frequency
def get_strongest_freq(thermal, fs=30, N=1800):
    T = 1.0 / fs
    yf = fft(thermal)
    xf = fftfreq(N, T)
    plt.plot(xf[:N//2], 2.0/N * np.abs(yf[0:N//2])) #only plot positive frequencies since signal is real
    plt.show()
    return(xf[np.argmax(np.abs(yf[0:N//2]))])

def get_dominant_freq(Sxx, f):
    idx = np.argmax(np.sum(Sxx, axis=1))
    freq = f[idx]
    return freq

def get_nearby_freqs(Sxx, f_index, bin_len, discard=False):
    assert(bin_len % 2 == 1)
    half_len = (bin_len-1) // 2
    start = max(0, (f_index - half_len))
    assert(start >= 0)
    end = min(len(Sxx), (f_index + half_len))
    assert(end < len(Sxx))
    if(discard):
        temp = np.zeros((end-start, np.shape(Sxx)[1]))
        temp[:(f_index - start)] = Sxx[start:f_index, :]
        temp[(f_index - start):] = Sxx[(f_index+1):(end+1), :]
        return temp
    else:
        return Sxx[start:end+1, :]
    
def get_power_spec(thermal, fs=30, window_length=512, overlap=511):    
    f, t, Sxx = signal.spectrogram(thermal, fs=fs, window=signal.get_window('tukey', window_length), noverlap=overlap)
    offset = (1800 - Sxx.shape[1])//2
    f_arr = get_nearby_freqs(Sxx=Sxx, f_index=np.where(f == get_dominant_freq(Sxx, f))[0][0], bin_len=7)
    int_psd = np.mean(f_arr, axis=0)
    return(int_psd)


def no_apnea(psd_int, threshold=1.2):
    #  NOTE: THIS FUNCTION IS MODIFIED FROM ITS ORIGINAL COUNTERPART
    if(psd_int.all() > threshold):
        return(True)
    return(False)

def new_stats(pred, gt):
    tp = np.sum(pred * gt)
    fp = np.sum(pred * (1-gt))
    tn = np.sum((1-pred) * (1-gt))
    fn = np.sum((1-pred) * gt)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    accuracy = (tp + tn)/ (tp + tn + fp + fn)
    tpr = tp / (tp + fn)
    fpr = fp / (fp + tn)
    confusion_matrix = np.array([[tp, fn], [fp, tn]])
    return precision, recall, accuracy, confusion_matrix

def normalize(x):
    x_norm = (x-np.min(x))/(np.max(x)-np.min(x))
    return (x_norm*255).astype(np.uint8)
