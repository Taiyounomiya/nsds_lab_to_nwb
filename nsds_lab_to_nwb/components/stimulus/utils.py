import numpy as np
from scipy.io import wavfile


def read_wav(path):
    wav_fs, data = wavfile.read(path)
    rate = float(wav_fs)
    length = data.shape[0] / rate
    return data, rate, length


def detect_events(mark_data, mark_rate, mark_threshold, min_separation=None):
    mark_front_padded = np.concatenate((np.array([0.]), mark_data), axis=0)
    thresh_crossings = np.diff((mark_front_padded > mark_threshold).astype('int'),
                               axis=0)
    mark_events_idx = np.where(thresh_crossings > 0.5)[0]
    mark_events = mark_events_idx / mark_rate

    if min_separation is not None:
        # if two adjacent marks are too close, drop the latter one
        too_close = np.where((mark_events[1:] - mark_events[:-1])
                             < min_separation)[0] + 1
        mark_events = np.delete(mark_events, too_close)

    return mark_events
