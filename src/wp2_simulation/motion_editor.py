import pandas as pd
import numpy as np

def get_sec(time_str:str) -> int:
    """Converts a timestep string to milliseconds 

    Args:
        time_str (str): str of format mm:ss:kkk

    Returns:
        int: number of milliseconds from 00:00:000
    """
    # split the string into mins, secs, and ms
    m, s, ms = time_str.split(":")
    
    # convert to ms
    return int(m) * 60000 + int(s) * 1000 + int(ms)


def get_time_string(Nms:int) -> str:
    """Converts milliseconds to timestep string

    Args:
        Nms (int): number of milliseconds from 00:00:000

    Returns:
        str: str of format mm:ss:kkk
    """
    # get number of mins, s, and ms
    m = Nms//60000
    s = (Nms - m * 60000)//1000
    ms = (Nms - m * 60000 - s*1000)
    
    # reformat into mm:ss:kkk 
    sec_str = f"{m:02d}:{s:02d}:{ms:03d}"
    
    return sec_str


if __name__ == "__main__":
    # path to motion file which is being modified
    path_to_motion = "webots_simulation/motions/Forwards.motion"
    # load the file
    motion_df = pd.read_csv(path_to_motion)
    
    # speed multiplier
    v_factor = 2
    
    # extract time
    time_arr = motion_df["#WEBOTS_MOTION"].to_numpy()
    new_time_arr = np.empty_like(time_arr)
    
    # change the time value by a sepcified factor to change speed of movement.
    for n, time in enumerate(time_arr):
        time_in_ms = get_sec(time)
        new_time = time_in_ms * v_factor 
        new_time_in_str = get_time_string(int(new_time))
        new_time_arr[n] = new_time_in_str
    out_df = motion_df.copy()
    out_df["#WEBOTS_MOTION"] = new_time_arr
    
    # save the result
    save_str = f"webots_simulation/motions/variable_speed_forwards/forward-motion_vfactor-{v_factor}"
    out_df.to_csv(save_str, header=True, index=False)
    
