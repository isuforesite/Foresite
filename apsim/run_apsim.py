"""
Created as part of ISU C-CHANGE Foresite system on 6 Jan 2020

@author: Matt Nowatzke
@email: mnowatz@iastate.edu
"""
from glob import glob
from os import getcwd
from subprocess import call

def find_apsim (exe_path=None):
    """
    Finds the most recent [-1] version of APSIM 7.XX installed on the system to get exe path.
    If APSIM is not installed in default directory will ned to specify with exe_path argument.
    
    Keyword Arguments:
        exe_path {str} -- [Path for APSIM executable if one isn't found.] (default: {None})
    
    Returns:
        [str] -- [Path to the APSIM 7.XX exe]
    """
    try:
        #find all installed Apsim.exe at default installation location and return the most recent (last).
        apsim_exes = glob("C:\\Program Files (x86)\\APSIM7*\\Model\\Apsim.exe")
        current_apsim_exe = apsim_exes[-1]
        return current_apsim_exe
    except:
        print("No APSIM 7.XX executable found. Try running again with exe_path argument.")
        return exe_path


def run_sims (apsim):
    """Will execute Apsim.exe to run all .sim files in targeted folder.
    
    Arguments:
        executable {str} -- [Path to Apsim.exe]
    """
    wd = getcwd()
    sims = glob("apsim_files/*.apsim")
    complete_file_paths = list()
    total_sims = len(sims)
    sims_count = 0
    for i in sims:
        #combine cwd and apsim file paths to give Apsim.exe a complete path.
        complete_file_paths.append(f'{wd}\{i}')
    for i in complete_file_paths:
        #run exe on each .apsim file
        call([apsim, i])
        sims_count += 1
        if sims_count % 10 == 0:
            print(f"Executing simulation {sims_count} of {total_sims}")

def main():
    """
    Main func for when running script as standalone. Will run all .apsim files in directory.
    """
    try:
        exe = find_apsim()
        print(f'Apsim exe located at {exe}.')
        print('Running simulations...')
        run_sims(exe)
    except:
        print('Something went wrong.')

#run if executed as standalone program
if __name__ == "__main__":
    main()