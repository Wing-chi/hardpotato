import os
import numpy as np
import matplotlib.pyplot as plt
import softpotato as sp

from hardpotato.chi import *
from hardpotato.gamry import *
import hardpotato.load_data as load_data
import hardpotato.save_data as save_data
import hardpotato.emstatpico as emstatpico

import hardpotato.pico_instrument as pico_instrument
import hardpotato.pico_mscript as mscript
import hardpotato.pico_serial as serial

# Potentiostat models available: 
models_available = ['chi1205b', 'chi1242b', 'chi601e', 'chi620e', 'chi604d', 'chi760e', 'emstatpico', 'gam1010e']

# Global variables
folder_save = '.'
model_pstat = 'no pstat'
path_lib = '.'


class Test:
    """
    Class for testing
    """

    def __init__(self):
        print('Test from potentiostat module')


class Info:
    """
    Class for storing information about potentiostat and technique in use
    """

    def __init__(self, model):
        self.model = model
        if "chi" in model_pstat:
            self.info = ChiInfo(model=model)
        elif "gam" in model_pstat:
            self.info = GamInfo(model=model)
        elif model_pstat == 'emstatpico':
            self.info = emstatpico.Info()
        else:
            print('Potentiostat model ' + model + ' not available in the library.')
            print('Available models:', models_available)

    def specifications(self):
        self.info.specifications()


class Setup:
    """
    Class for setting up potentiostat and filing system
    """
    def __init__(self, model=0, path='.', folder='.', port=None, verbose=1):
        global folder_save
        folder_save = folder
        global model_pstat
        model_pstat = model
        global path_lib
        path_lib = path
        global port_
        port_ = port
        if verbose:
            self.info()

    def info(self):
        print('\n----------')
        print('Potentiostat model: ' + model_pstat)
        print('Potentiostat path: ' + path_lib)
        print('Save folder: ' + folder_save)
        print('----------\n')


class Technique:
    """
    Base class for operating chosen potentiostat technique
    """

    def __init__(self, text='', fileName='CV'):
        self.text = text  # text to write as macro
        self.fileName = fileName
        self.technique = 'Technique'
        self.bpot = False
        self.header = ""

    def writeToFile(self):
        if model_pstat[0:3] == 'chi':
            file = open(folder_save + '/' + self.fileName + '.mcr', 'wb')
            file.write(self.text.encode('ascii'))
            file.close()
        elif model_pstat == 'gam':
            file = open(folder_save + '/' + self.fileName + '.mcr', 'wb')
            file.write(self.text.encode('ascii'))
            file.close()
        elif model_pstat == 'emstatpico':
            file = open(folder_save + '/' + self.fileName + '.mscr', 'wb')
            file.write(self.text.encode('ascii'))
            file.close()

    def run(self):
        if model_pstat[0:3] == 'chi':
            self.message()
            # Write macro:
            self.writeToFile()
            # Run command:
            command = path_lib
            param = ' /runmacro:\"' + folder_save + '/' + self.fileName + '.mcr\"'
            print("Running Command: ", command + param)
            os.system(command + param)
            self.message(start=False)
            self.plot()
        elif model_pstat[0:3] == 'gam':
            self.message()
            # Write macro:
            self.writeToFile()
            # Run command:
            command = path_lib
            param = ' /runmacro:\"' + folder_save + '/' + self.fileName + '.mcr\"'
            print("Running Command: ", command + param)
            os.system(command + param)
            self.message(start=False)
            self.plot()
        elif model_pstat == 'emstatpico':
            self.message()
            self.writeToFile()
            if port_ is None:
                self.port = serial.auto_detect_port()
            with serial.Serial(self.port, 1) as comm:
                dev = pico_instrument.Instrument(comm)
                dev.send_script(folder_save + '/' + self.fileName + '.mscr')
                result = dev.readlines_until_end()
            self.data = mscript.parse_result_lines(result)
            fileName = folder_save + '/' + self.fileName + '.txt'
            save = save_data.Save(self.data, fileName, self.header, model_pstat,
                                  self.technique, bpot=self.bpot)
            self.message(start=False)
            self.plot()
        else:
            print('\nNo potentiostat selected. Aborting.')

    def plot(self):
        figNum = np.random.randint(100)  # To prevent rewriting the same plot
        if self.technique == 'CV':
            cv = load_data.CV(self.fileName + '.txt', folder_save, model_pstat)
            sp.plotting.plot(cv.E, cv.i, show=False, fig=figNum,
                             fileName=folder_save + '/' + self.fileName)
        elif self.technique == 'LSV':
            lsv = load_data.LSV(self.fileName + '.txt', folder_save, model_pstat)
            sp.plotting.plot(lsv.E, lsv.i, show=False, fig=figNum,
                             fileName=folder_save + '/' + self.fileName)
        elif self.technique == 'IT':
            ca = load_data.IT(self.fileName + '.txt', folder_save, model_pstat)
            sp.plotting.plot(ca.t, ca.i, show=False, fig=figNum,
                             xlab='$t$ / s', ylab='$i$ / A',
                             fileName=folder_save + '/' + self.fileName)
        elif self.technique == 'OCP':
            ocp = load_data.OCP(self.fileName + '.txt', folder_save, model_pstat)
            sp.plotting.plot(ocp.t, ocp.E, show=False, fig=figNum,
                             xlab='$t$ / s', ylab='$E$ / V',
                             fileName=folder_save + '/' + self.fileName)
        plt.close()

    def message(self, start=True):
        if start:
            print('----------\nStarting ' + self.technique)
            if self.bpot:
                print('Running in bipotentiostat mode')
        else:
            print(self.technique + ' finished\n----------\n')

    def bipot(self, E=-0.2, sens=1e-6):
        if self.technique != 'OCP' and self.technique != 'EIS':
            self.tech.bipot(E, sens)
            self.text = self.tech.text
            self.bpot = True
        else:
            print(self.technique + ' does not have bipotentiostat mode')


class CV(Technique):
    """
    Class for running CV Technique
    """

    def __init__(self, Eini=-0.2, Ev1=0.2, Ev2=-0.2, Efin=-0.2, sr=0.1,
                 dE=0.001, nSweeps=2, sens=1e-6,
                 fileName='CV', header='CV', **kwargs):
        self.header = header
        self.technique = 'CV'
        if "chi" in model_pstat:
            self.tech = ChiCV(Eini, Ev1, Ev2, Efin, sr, dE, nSweeps, sens, fileName=fileName, header=header,
                              folder=folder_save, model=model_pstat, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
        elif "gam" in model_pstat:
            self.tech = GamCV(Eini, Ev1, Ev2, Efin, sr, dE, nSweeps, sens, fileName=fileName, header=header,
                              folder=folder_save, model=model_pstat, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
        elif model_pstat == 'emstatpico':
            self.tech = emstatpico.CV(Eini=Eini, Ev1=Ev1, Ev2=Ev2, Efin=Efin, sr=sr, dE=dE, nSweeps=nSweeps, sens=sens,
                                      folder_save=folder_save, fileName=fileName, header=header, path_lib='',
                                      **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
        else:
            print('Potentiostat model ' + model_pstat + ' does not have CV.')


class LSV(Technique):
    """
    Class for running LSV Technique
    """

    def __init__(self, Eini=-0.2, Efin=0.2, sr=0.1, dE=0.001, sens=1e-6,
                 fileName='LSV', header='LSV', **kwargs):
        self.header = header
        if "chi" in model_pstat:
            self.tech = ChiLSV(Eini, Efin, sr, dE, sens, fileName=fileName, model=model_pstat, folder=folder_save, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'LSV'
        elif "gam" in model_pstat:
            self.tech = GamLSV(Eini, Efin, sr, dE, sens, fileName=fileName, model=model_pstat, folder=folder_save, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'LSV'
        elif model_pstat == 'emstatpico':
            self.tech = emstatpico.LSV(Eini=Eini, Efin=Efin, sr=sr, dE=dE, sens=sens, folder_save=folder_save,
                                       fileName=fileName, header=header, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'LSV'
        else:
            print('Potentiostat model ' + model_pstat + ' does not have LSV.')


class IT(Technique):
    """
    Class for running IT Technique
    """

    def __init__(self, Estep=0.2, dt=0.001, ttot=2, sens=1e-6,
                 fileName='IT', header='IT', **kwargs):
        self.header = header
        if "chi" in model_pstat:
            self.tech = ChiIT(Estep, dt, ttot, sens, fileName=fileName, model=model_pstat, folder=folder_save, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'IT'
        elif "gam" in model_pstat:
            self.tech = GamIT(Estep, dt, ttot, sens, fileName=fileName, model=model_pstat, folder=folder_save, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'IT'
        elif model_pstat == 'emstatpico':
            self.tech = emstatpico.IT(Estep=Estep, dt=dt, ttot=ttot, sens=sens, folder_save=folder_save,
                                      fileName=fileName, header=header, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'IT'
        else:
            print('Potentiostat model ' + model_pstat + ' does not have IT.')


class CA(Technique):
    """
    Class for running CA experiment to determine conductivity
    """

    def __init__(self, Eini=-0.025, Ev1=0.025, Ev2=-0.025,  dE=1e-6, nSweeps=200, pw=1e-4, sens=1e-4,
                 fileName='CA', header='CA', **kwargs):
        self.header = header
        if "chi" in model_pstat:
            self.tech = ChiCA(Eini=Eini, Ev1=Ev1, Ev2=Ev2, dE=dE, nSweeps=nSweeps, pw=pw, sens=sens,
                              header=header, fileName=fileName, model=model_pstat, folder=folder_save, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'CA'
        elif "gam" in model_pstat:
            self.tech = GamCA(Eini=Eini, Ev1=Ev1, Ev2=Ev2, dE=dE, nSweeps=nSweeps, pw=pw, sens=sens,
                              header=header, fileName=fileName, model=model_pstat, folder=folder_save, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'CA'
        # elif model_pstat == 'emstatpico':
        #     self.tech = emstatpico.CA(Estep, dt, ttot, sens, folder_save, fileName,
        #                               header, **kwargs)
        #     Technique.__init__(self, text=self.tech.text, fileName=fileName)
        #     self.technique = 'IT'
        else:
            print('Potentiostat model ' + model_pstat + ' does not have IT.')


class OCP(Technique):
    """
    Class for running OCP Technique
    """

    def __init__(self, ttot=2, dt=0.01, fileName='OCP', header='OCP', **kwargs):
        self.header = header
        if "chi" in model_pstat:
            self.tech = ChiOCP(ttot, dt, header=header, fileName=fileName, folder=folder_save,
                               model=model_pstat, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'OCP'
        elif "gam" in model_pstat:
            self.tech = GamOCP(ttot, dt, header=header, fileName=fileName, folder=folder_save,
                               model=model_pstat, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'OCP'
        elif model_pstat == 'emstatpico':
            self.tech = emstatpico.OCP(ttot=ttot, dt=dt, folder_save=folder_save, fileName=fileName, header=header,
                                       **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'OCP'
        else:
            print('Potentiostat model ' + model_pstat + ' does not have OCP.')


class NPV(Technique):
    """
    Class for running NPV Technique
    """

    def __init__(self, Eini=0.5, Efin=-0.5, dE=0.01, tsample=0.1, twidth=0.05,
                 tperiod=10, sens=1e-6,
                 fileName='NPV', header='NPV performed with CHI760', **kwargs):
        if "chi" in model_pstat:
            self.tech = ChiNPV(Eini=Eini, Efin=Efin, dE=dE, tsample=tsample, twidth=twidth, tperiod=tperiod, sens=sens,
                               header=header, fileName=fileName, model=model_pstat, folder=folder_save, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'NPV'
        else:
            print('Potentiostat model ' + model_pstat + ' does not have NPV.')


class EIS(Technique):
    """
    Class for running ESI Technique for determining solution resistance
    """

    def __init__(self, Eini=0, low_freq=1, high_freq=1000, amplitude=0.01, sens=1e-6,
                 fileName='EIS', header='EIS', **kwargs):
        self.header = header
        if "chi" in model_pstat:
            self.tech = ChiEIS(Eini=Eini, low_freq=low_freq, high_freq=high_freq, amplitude=amplitude, sens=sens,
                               header=header, fileName=fileName, model=model_pstat, folder=folder_save, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'EIS'
        elif "gam" in model_pstat:
            self.tech = GamEIS(Eini=Eini, low_freq=low_freq, high_freq=high_freq, amplitude=amplitude, sens=sens,
                               header=header, fileName=fileName, model=model_pstat, folder=folder_save, **kwargs)
            Technique.__init__(self, text=self.tech.text, fileName=fileName)
            self.technique = 'EIS'
        else:
            print('Potentiostat model ' + model_pstat + ' does not have EIS.')
