"""
Created as part of ISU C-CHANGE Foresite system on 6 Jan 2020

@author: Matt Nowatzke
@email: mnowatz@iastate.edu
"""

import subprocess
import sys
import threading
import traceback
from multiprocessing import cpu_count
from glob import glob
from os import getcwd
from tqdm import tqdm #progress bar
from time import time
from queue import Queue

def find_apsim_exe():
    """
    Finds the most recent [-1] version of APSIM 7.XX installed on the system (if installed in default Windows location) to get Apsim.exe path.

    Returns:
        [str] -- [Path to the APSIM 7.XX exe]
    """
    try:
        #find all installed Apsim.exe at default installation location and return the most recent (last).
        apsim_exes = glob("C:\\Program Files (x86)\\APSIM7*\\Model\\Apsim.exe")
        current_apsim_exe = apsim_exes[-1]
        return current_apsim_exe
    except:
        print("No APSIM 7.XX executable found.")

def find_to_sim_exe():
    """
    Finds the most recent [-1] version of APSIM 7.XX installed on the system (if installed in default Windows location) to get the ApsimToSim.exe path.
    
    Keyword Arguments:
        to_sim_path {str} -- [Path for APSIM to sim executable if one isn't found.] (default: {None})
    
    Returns:
        [str] -- [Path to the APSIM 7.XX exe]
    """
    try:
        #find all installed ApsimToSim.exe at default installation location and return the most recent (last[-1]).
        sim_exes = glob("C:\\Program Files (x86)\\APSIM7*\\Model\\ApsimToSim.exe")
        current_to_sim_exe = sim_exes[-1]
        return current_to_sim_exe
    except:
        print("No APSIM 7.XX to sim executable found.")

def convert_apsim_to_sim(apsim_filename, lock):
    '''Converts an .apsim file to .sim files.'''
    apsim_to_sim_exe = find_to_sim_exe()
    startupinfo = None
    if 'win' in sys.platform:
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.STARTF_USESHOWWINDOW
        #si.wShowWindow = 6 # SW_MINIMIZE
        si.wShowWindow = 0 # SW_HIDE - hides cmd windows
        startupinfo=si
    apsim_tmp_filename = apsim_filename.replace('.apsim','.tmp')
    with open(apsim_tmp_filename, 'w') as tmp_file:
        subprocess.call([apsim_to_sim_exe, apsim_filename], startupinfo=startupinfo, stdout=tmp_file, stderr=tmp_file)

def worker_apsim(queue, lock):
    '''Process files from the queue.'''
    for args in iter(queue.get, None):
        try:
            convert_apsim_to_sim(args, lock)
        except Exception as e: # catch exceptions to avoid exiting the thread prematurely
            print(f'{args} failed: {e}')#, file=sys.stderr

def convert_all_apsim_to_sim(apsim_filename_list, num_cores=None):
    '''Converts .apsim files to .sim files.'''
    if num_cores == None:
        num_cores = cpu_count() - 2
    apsim_file_total = len(apsim_filename_list)
    print(f'Converting {apsim_file_total} .apsim files to .sim files.')
    
    # add .apsim files to Queue
    q = Queue()
    for apsim_filename in tqdm(apsim_filename_list):
        q.put_nowait(apsim_filename)
        
    # run .apsim files and start threads to convert
    lock = threading.RLock()
    threads = [threading.Thread(target=worker_apsim, args=(q,lock)) for _ in range(num_cores)]
    for t in threads:
        t.daemon = False # program quits when threads die
        t.start()
    for _ in threads: q.put_nowait(None) # signal no more files
    for t in threads: t.join() # wait for completion

def run_a_sim(sim_filename, lock):
    '''Runs a .sim file in APSIM.'''
    apsim_exe = find_apsim_exe()
    tmp_filename = sim_filename.replace('.sim','.tmp')
    startupinfo = None
    if 'win' in sys.platform:
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.STARTF_USESHOWWINDOW
        #si.wShowWindow = 6 # SW_MINIMIZE
        si.wShowWindow = 0 # SW_HIDE - hides cmd windows
        startupinfo = si
    with open(tmp_filename, 'w') as tmp_file:
        #TODO make sure the os.remove file is working correctly
        if subprocess.call([apsim_exe, sim_filename], stdout=tmp_file, stderr=tmp_file, startupinfo=startupinfo) == 0:
            os.remove(tmp_file)


def worker_sim(queue, lock):
    '''Process files from the queue.'''
    for args in iter(queue.get, None):
        try:
            run_a_sim(args, lock)
        except Exception as e: # catch exceptions to avoid exiting the thread prematurely
            print(f'{args} failed: {e}')#, file=sys.stderr


def run_many_sims(sim_filename_list, num_cores=None):
    '''Runs apsim in parallel for every .sim file in sim_filename_list.'''
    print(f'Running Apsim for {len(sim_filename_list)} .sim files...')
    if num_cores == None:
        num_cores = cpu_count() - 2
    # Add .sim files to Queue
    q = Queue()
    for sim_filename in tqdm(sim_filename_list):
        q.put_nowait(sim_filename)
        
    # Run .sim files and start threads
    lock = threading.RLock()
    threads = [threading.Thread(target=worker_sim, args=(q,lock)) for _ in range(num_cores)]
    for t in threads:
        t.daemon = False # program quits when threads die
        t.start()
    for _ in threads: q.put_nowait(None) # signal no more files
    for t in threads: t.join() # wait for completion
    print('Runs completed.')


def run_all_simulations (apsim_files_path="apsim_files\\Accola\\*.apsim", sim_files_path="apsim_files\\Accola\\*.sim", n_cores=None):
    """
    Converts all .apsim files to .sim files and runs all .sim files in targeted folder.

    Keyword Arguments:
        apsim {str} -- System path to Apsim.exe
        apsim_files_path {str} -- Path to .apsim files
        sim_files_path {str} -- Path to .sim files
        n_cores {int} -- number of cores to allocate to runs

    Returns: None
    """
    #get system number of cores if not specified
    if n_cores == None:
        n_cores = cpu_count() - 2
    print(f'Running on {n_cores} cores')

    #combine working dir and apsim file paths to create complete file paths
    wd = getcwd()
    apsim_files = glob(apsim_files_path)
    complete_apsim_paths = [wd + f'\\{apsim_file}' for apsim_file in apsim_files]
    #convert list of .apsim files to .sim files
    convert_all_apsim_to_sim(complete_apsim_paths, num_cores=n_cores)
    
    #get list of all converted .sim files and create their full paths
    sim_files = glob(sim_files_path)
    complete_sim_paths = [wd + f'\\{sim_file}' for sim_file in sim_files]
    #run .sim files
    run_many_sims(complete_sim_paths, num_cores=n_cores)

def main():
    """
    Main function for when running script as standalone. Will run all .apsim files in directory.
    """
    try:
        run_all_simulations()
    except Exception:
        traceback.print_exc()

#run if executed as standalone program
if __name__ == "__main__":
    main()