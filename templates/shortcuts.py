"""
Created: 2021/05/27
Updated: 2022/12/28

Shortcuts around nextnanopy used in the example 'InterbandTunneling_Duboz2019_nnp.py'.
See https://github.com/Chikuwaq/nextnanopy-wrapper for the comprehensive and up-to-date nextnanopy wrappers.

@author: takuma.sato@nextnano.com
"""

import os
import nextnanopy as nn

# fundamental physical constants https://physics.nist.gov/cgi-bin/cuu
hbar = 1.054571817E-34   # Planck constant / 2Pi in [J.s]
electron_mass = 9.1093837015E-31   # in [kg]
elementary_charge  = 1.602176634*10**(-19)   # [C] elementary charge

scale1ToKilo = 1e-3
scale1ToCenti = 1e2
scale1ToMilli = 1e3
scale1ToMicro = 1e6
scale1ToNano = 1e9

scale_Angstrom_to_nm = 0.1
scale_eV_to_J = elementary_charge


class NextnanoInputFileError(Exception):
    """ Exception when the user's nextnano input file contains issue """
    pass


# -------------------------------------------------------
# Simulation preprocessing
# -------------------------------------------------------

def separateFileExtension(filename):
    """
    Separate file extension from file name.
    Returns the original filename and empty string if extension is absent.
    """
    filename = os.path.split(filename)[1]   # remove paths if present
    filename_no_extension, extension = os.path.splitext(filename)

    if extension not in ['', '.in', '.xml', '.negf']: 
        raise RuntimeError(f"File extension {extension} is not supported by nextnano.")

    return filename_no_extension, extension



def detect_software_new(inputfile):
    """
    Detect software from nextnanopy.InputFile() object.
    The return value software will be needed for the argument of nextnanopy.DataFile() and sweep output folder names.

    This function is more compact than detect_software() because it makes use of the attributes of nextnanopy.InputFile() object.
    If the object is not executed in the script, it does not have execute_info attributes.
    In that case, you have to explicitly give the output folder name to load output data.
    Therefore, THIS METHOD DOES NOT WORK IF YOU RUN SIMULATIONS WITH nextnanopy.Sweep()!
    """
    try:
        with open(inputfile.fullpath, 'r') as file:
            for line in file:
                if 'simulation-flow-control' in line:
                    software = 'nextnano3'
                    extension = '.in'
                    break
                elif 'run{' in line:
                    software = 'nextnano++'
                    extension = '.in'
                    break
                elif '<nextnano.NEGF' in line:
                    software = 'nextnano.NEGF'
                    extension = '.xml'
                    break
                elif 'nextnano.NEGF{' in line:
                    software = 'nextnano.NEGF++'
                    extension = '.negf'
                elif '<nextnano.MSB' in line:
                    software = 'nextnano.MSB'
                    extension = '.xml'
                elif 'nextnano.MSB{' in line:
                    software = 'nextnano.MSB'
                    extension = '.negf'
    except FileNotFoundError:
        raise FileNotFoundError(f'Input file {inputfile.fullpath} not found!')

    if not software:   # if the variable is empty
        raise NextnanoInputFileError('Software cannot be detected! Please check your input file.')
    else:
        print('\nSoftware detected: ', software)

    return software, extension




# -------------------------------------------------------
# Access to output data
# -------------------------------------------------------

def getSweepOutputFolderName(filename, *args):
    """
    nextnanopy.sweep.execute_sweep() generates output folder with this name

    INPUT:
        filename
        args = SweepVariableString1, SweepVariableString2, ...

    RETURN:
        string of sweep output folder name

    """
    filename_no_extension = separateFileExtension(filename)[0]
    output_folderName = filename_no_extension + '_sweep'

    for sweepVar in args:
        if not isinstance(sweepVar, str):
            raise TypeError(f'Argument {sweepVar} must be a string!')
        output_folderName += '__' + sweepVar

    return output_folderName


def getSweepOutputFolderPath(filename, software, *args):
    """
    Get the output folder path generated by nextnanopy.sweep.execute_sweep().

    Parameters
    ----------
    filename : str
        input file name (may include absolute/relative paths)
    software : str
        nextnano solver
    *args : str
        SweepVariableString1, SweepVariableString2, ...

    Raises
    ------
    base.NextnanopyScriptError
        If any of the arguments are invalid.

    Returns
    -------
    output_folder_path : str
        sweep output folder path

    """
    filename_no_extension = separateFileExtension(filename)[0]
    output_folder_path = os.path.join(nn.config.get(software, 'outputdirectory'), filename_no_extension + '_sweep')

    if len(args) == 0: raise ValueError("Sweep variable string is missing in the argument!")

    for sweepVar in args:
        if not isinstance(sweepVar, str):
            raise TypeError(f'Argument {sweepVar} must be a string!')
        output_folder_path += '__' + sweepVar

    return output_folder_path


def get_output_subfolder_path(sweep_output_folder_path, input_file_name):
    """
    Return output folder path corresponding to the input file

    Parameters
    ----------
    input_file_name : str
        input file name or path

    Returns
    -------
    str
        path to output folder

    """
    subfolder_name = separateFileExtension(input_file_name)[0]
    return os.path.join(sweep_output_folder_path, subfolder_name)


def getSweepOutputSubfolderName(filename, sweepCoordinates):
    """
    nextnanopy.sweep.execute_sweep() generates output subfolders with this name

    INPUT:
        filename
        {sweepVariable1: value1, sweepVariable2: value2, ...}

    RETURN:
        string of sweep output subfolder name

    """
    filename_no_extension = separateFileExtension(filename)[0]
    output_subfolderName = filename_no_extension + '__'

    for sweepVar, value in sweepCoordinates.items():
        if not isinstance(sweepVar, str):
            raise TypeError('key must be a string!')
        try:
            val = str(value)
        except ValueError:
            print('value cannot be converted to string!')
            raise
        else:
            output_subfolderName +=  sweepVar + '_' + val + '_'

    return output_subfolderName



def getDataFile(keywords, name, software):
    """
    Get single nextnanopy.DataFile of output data in the directory matching name with the given string keyword.

    Parameters
    ----------
    keywords : str or list of str
        Find output data file with the names containing single keyword or multiple keywords (AND search)
    name : str
        input file name (= output subfolder name). May contain extensions and/or fullpath.
    software : str
        nextnano solver.

    Returns
    -------
    nextnanopy.DataFile object of the simulation data

    """
    outputFolder = nn.config.get(software, 'outputdirectory')
    filename_no_extension = separateFileExtension(name)[0]
    outputSubfolder = os.path.join(outputFolder, filename_no_extension)

    return getDataFile_in_folder(keywords, outputSubfolder, software)


def getDataFile_in_folder(keywords, folder_path, software):
    """
    Get single nextnanopy.DataFile of output data with the given string keyword(s) in the specified folder.

    Parameters
    ----------
    keywords : str or list of str
        Find output data file with the names containing single keyword or multiple keywords (AND search)
    folder_path : str
        absolute path of output folder in which the datafile should be sought
    software : str
        nextnano solver.

    Returns
    -------
    nextnanopy.DataFile object of the simulation data

    """
    print(f'\nSearching for output data with keyword(s) {keywords}...')

    # Search output data using nn.DataFolder.find(). If multiple keywords are provided, find the intersection of files found with each keyword.
    if isinstance(keywords, str):
        list_of_files = nn.DataFolder(folder_path).find(keywords, deep=True)
    elif isinstance(keywords, list):
        list_of_sets = [set(nn.DataFolder(folder_path).find(keyword, deep=True)) for keyword in keywords]
        candidates = list_of_sets[0]
        for s in list_of_sets:
            candidates = s.intersection(candidates)
        list_of_files = list(candidates)
    else:
        raise TypeError("Argument 'keywords' must be either str or list")

    # validate the search result
    if len(list_of_files) == 0:
        raise FileNotFoundError(f"No output file found with keyword(s) '{keywords}'!")
    elif len(list_of_files) == 1:
        file = list_of_files[0]
    else:
        print(f"More than one output files found with keyword(s) '{keywords}'!")
        for count, file in enumerate(list_of_files):
            filename = os.path.split(file)[1]
            print(f"Choice {count}: {filename}")
        determined = False
        while not determined:
            choice = input('Enter the index of data you need: ')
            if choice == 'q':
                raise RuntimeError('Nextnanopy terminated.') from None
            try:
                choice = int(choice)
            except ValueError:
                print("Invalid input. (Type 'q' to quit)")
                continue
            else:
                if choice < 0 or choice >= len(list_of_files):
                    print("Index out of bounds. Type 'q' to quit")
                    continue
                else:
                    determined = True
        file = list_of_files[choice]

    if __debug__: print("Found:\n", file)

    try:
        return nn.DataFile(file, product=software)
    except NotImplementedError:
        raise NotImplementedError(f'Nextnanopy does not support datafile for {file}')



# -------------------------------------------------------
# Data postprocessing
# -------------------------------------------------------

def convert_grid(arr, old_grid, new_grid):
    """
    Convert grid of an array.
    Needed if two physical quantities that you want to overlay are on a different grid.

    Parameters
    ----------
    arr : array-like
        array to be converted
    old_grid : array-like
        grid points on which arr is defined
    new_grid : array-like
        grid points on which new arr should sit

    Returns
    -------
    arr_new : array-like
        array on the new grid

    Requires
    --------
    SciPy
    """

    from scipy.interpolate import splev, splrep

    spl = splrep(old_grid, arr)     # interpolate
    arr_new = splev(new_grid, spl)  # map to new grid
    return arr_new




# -------------------------------------------------------
# Plotting
# -------------------------------------------------------
# See https://github.com/Chikuwaq/nextnanopy-wrapper
