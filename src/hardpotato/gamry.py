
class GamInfo:
    """
    Class for storing information about potentiostat and technique in use for Gamry potentiostats.
    To add capabilities for another Gamry potentiostat, simply add an "elif model == <model_name>:" statement and then
    specify the potentiostat model parameters.

    Pending:
        * Calculate dE, sr, dt, ttot, mins and max
    """

    def __init__(self, model):
        if model == "gam1010e":
            self.name = "Gamry Interface 1010E (gam1010e)"
            self.file_tag = "c\x02\0\0"
            self.tech = ['CV', 'CA', 'LSV', 'OCP', 'CP', 'DP', 'SWV', 'EIS']
            self.options = [
                'Resistance in ohms (resistance)'
            ]
            self.bipot = True
            self.resistance_opt = True

            self.E_min = -12
            self.E_max = 12
            self.sr_min = 0.000001
            self.sr_max = 10000
            self.freq_min = 0.00001
            self.freq_max = 2000000
    
        else:
            raise Exception(f"Gamry model {model} not available in hardpotato.")

    @staticmethod
    def limits(val, low, high, label, units):
        if val < low or val > high:
            raise Exception(label + ' should be between ' + str(low) + ' ' +
                            units + ' and ' + str(high) + ' ' + units +
                            '. Received ' + str(val) + ' ' + units)

    def specifications(self):
        print('Model: ', self.name)
        print('Techniques available:', self.tech)
        print('Options available:', self.options)


class GamBase:
    """
        **kwargs:
            resistance # ohms, solution resistance
    """
    def __init__(self, **kwargs):
        self.info = GamInfo(kwargs.get('model', ""))
        self.fileName = kwargs.get('fileName', "")
        self.folder = kwargs.get('folder', "")
        self.header = kwargs.get('header', "")
        self.head = f'{self.info.file_tag}\nfolder: {self.folder}\nfileoverride\nheader: {self.header}\n\n'
        self.body = ''
        self.foot = '\n forcequit: yesiamsure\n'

        # self.qt = kwargs.get('qt', 2)
        self.resistance = kwargs.get('resistance', 0)
        if self.resistance and self.info.resistance_opt:  # In case IR compensation is required
            self.end_body = f'\nmir={self.resistance}\nircompon\nrun\nircompoff\n' \
                         f'save:{self.fileName}\ntsave:{self.fileName}'
        else:
            self.end_body = f'\nrun\nsave:{self.fileName}\ntsave:{self.fileName}'

    @property
    def text(self):
        return self.head + self.body + self.end_body + self.foot

    @staticmethod
    def correct_volts(Ev1, Ev2):
        """
        Correct voltage parameters
        :param Ev1: first voltage
        :param Ev2: second voltage
        :return: array, [eh, el, pn]
        """
        if Ev1 > Ev2:
            eh = Ev1
            el = Ev2
            pn = 'p'
        else:
            eh = Ev2
            el = Ev1
            pn = 'n'
        return eh, el, pn

    def bipot(self, E, sens):
        if not self.info.bipot:
            raise Exception(self.info.name, " does not have bipot abilities.")

        # Validate bipot:
        self.info.limits(E, self.info.E_min, self.info.E_max, 'E2', 'V')

        self.body += '\ne2=' + str(E) + '\nsens2=' + str(sens) + '\ni2on' + \
                     '\nrun\nsave:' + self.fileName + '\ntsave:' + self.fileName


class GamCV(GamBase):
    def __init__(self, Eini, Ev1, Ev2, Efin, sr, dE, nSweeps, sens, **kwargs):
        super().__init__(**kwargs)

        self.validate(Eini, Ev1, Ev2, Efin, sr, dE, nSweeps, sens)
        eh, el, pn = self.correct_volts(Ev1, Ev2)

        self.body = f'tech=cv\nei={Eini}\neh={eh}\nel={el}\npn={pn}\ncl={nSweeps+1}' \
                    f'\nefon\nef={Efin}\nsi={dE}\nv={sr}\nsens={sens}'

    def validate(self, Eini, Ev1, Ev2, Efin, sr, dE, nSweeps, sens):
        self.info.limits(Eini, self.info.E_min, self.info.E_max, 'Eini', 'V')
        self.info.limits(Ev1, self.info.E_min, self.info.E_max, 'Ev1', 'V')
        self.info.limits(Ev2, self.info.E_min, self.info.E_max, 'Ev2', 'V')
        self.info.limits(Efin, self.info.E_min, self.info.E_max, 'Efin', 'V')
        self.info.limits(sr, self.info.sr_min, self.info.sr_max, 'sr', 'V/s')


class GamLSV(GamBase):
    def __init__(self, Eini, Efin, sr, dE, sens, **kwargs):
        super().__init__(**kwargs)

        self.validate(Eini, Efin, sr, dE, sens)
        self.body = f'tech=lsv\nei={Eini}\nef={Efin}\nv={sr}\nsi={dE}\nsens={sens}'

    def bipot(self, E, sens):
        if not self.info.bipot:
            raise Exception(self.info.name, " does not have bipot abilities.")

        # Validate bipot:
        self.info.limits(E, self.info.E_min, self.info.E_max, 'E2', 'V')

        self.body += '\ne2=' + str(E) + '\nsens2=' + str(sens) + '\ni2on' + \
                     '\nrun\nsave:' + self.fileName + '\ntsave:' + self.fileName
        
    def validate(self, Eini, Efin, sr, dE, sens):
        self.info.limits(Eini, self.info.E_min, self.info.E_max, 'Eini', 'V')
        self.info.limits(Efin, self.info.E_min, self.info.E_max, 'Efin', 'V')
        self.info.limits(sr, self.info.sr_min, self.info.sr_max, 'sr', 'V/s')

# class GamCP(GamBase):
#     def __init__(self, Eini, Ev1, Ev2, dE, nSweeps, pw, sens, **kwargs):
#         super().__init__(**kwargs)

#         self.validate(Eini, Ev1, Ev2)
#         eh, el, pn = self.correct_volts(Ev1, Ev2)
#         self.body = f'tech=ca\nei={Eini}\neh={eh}\nel={el}\npn={pn}\n' \
#                     f'cl={nSweeps}\npw={pw}\nsi={dE}\nqt={self.qt}\nsens={sens}'

#     def validate(self, Eini, Ev1, Ev2):
#         self.info.limits(Eini, self.info.E_min, self.info.E_max, 'Eini', 'V')
#         self.info.limits(Ev1, self.info.E_min, self.info.E_max, 'Ev1', 'V')
#         self.info.limits(Ev2, self.info.E_min, self.info.E_max, 'Ev2', 'V')
# class GamDP(GamBase):
#     def __init__(self, Eini, Ev1, Ev2, dE, nSweeps, pw, sens, **kwargs):
#         super().__init__(**kwargs)

#         self.validate(Eini, Ev1, Ev2)
#         eh, el, pn = self.correct_volts(Ev1, Ev2)
#         self.body = f'tech=ca\nei={Eini}\neh={eh}\nel={el}\npn={pn}\n' \
#                     f'cl={nSweeps}\npw={pw}\nsi={dE}\nqt={self.qt}\nsens={sens}'

#     def validate(self, Eini, Ev1, Ev2):
#         self.info.limits(Eini, self.info.E_min, self.info.E_max, 'Eini', 'V')
#         self.info.limits(Ev1, self.info.E_min, self.info.E_max, 'Ev1', 'V')
#         self.info.limits(Ev2, self.info.E_min, self.info.E_max, 'Ev2', 'V')
# class GamSWV(GamBase):
#     def __init__(self, Eini, Ev1, Ev2, dE, nSweeps, pw, sens, **kwargs):
#         super().__init__(**kwargs)

#         self.validate(Eini, Ev1, Ev2)
#         eh, el, pn = self.correct_volts(Ev1, Ev2)
#         self.body = f'tech=ca\nei={Eini}\neh={eh}\nel={el}\npn={pn}\n' \
#                     f'cl={nSweeps}\npw={pw}\nsi={dE}\nqt={self.qt}\nsens={sens}'

#     def validate(self, Eini, Ev1, Ev2):
#         self.info.limits(Eini, self.info.E_min, self.info.E_max, 'Eini', 'V')
#         self.info.limits(Ev1, self.info.E_min, self.info.E_max, 'Ev1', 'V')
#         self.info.limits(Ev2, self.info.E_min, self.info.E_max, 'Ev2', 'V')
    

class GamCA(GamBase):

    def __init__(self, Eini, Ev1, Ev2, dE, nSweeps, pw, sens, **kwargs):
        super().__init__(**kwargs)

        self.validate(Eini, Ev1, Ev2)
        eh, el, pn = self.correct_volts(Ev1, Ev2)
        self.body = f'tech=ca\nei={Eini}\neh={eh}\nel={el}\npn={pn}\n' \
                    f'cl={nSweeps}\npw={pw}\nsi={dE}\nsens={sens}'
   
    def bipot(self, E, sens):
        if not self.info.bipot:
            raise Exception(self.info.name, " does not have bipot abilities.")

        # Validate bipot:
        self.info.limits(E, self.info.E_min, self.info.E_max, 'E2', 'V')

        self.body += '\ne2=' + str(E) + '\nsens2=' + str(sens) + '\ni2on' + \
                     '\nrun\nsave:' + self.fileName + '\ntsave:' + self.fileName
        
    def validate(self, Eini, Ev1, Ev2):
        self.info.limits(Eini, self.info.E_min, self.info.E_max, 'Eini', 'V')
        self.info.limits(Ev1, self.info.E_min, self.info.E_max, 'Ev1', 'V')
        self.info.limits(Ev2, self.info.E_min, self.info.E_max, 'Ev2', 'V')


class GamOCP(GamBase):
    """
        Pending:
        * Validate parameters
    """

    def __init__(self, ttot, dt, **kwargs):
        super().__init__(**kwargs)

        self.body = f'tech=ocpt\nst={ttot}\neh=10\nel=-10\nsi={dt}'

    # def __init__(self, ttot, dt, folder, fileName, header, path_lib, **kwargs):
    #     self.fileName = fileName
    #     self.folder = folder
    #     self.text = ''

    #     if 'qt' in kwargs:
    #         qt = kwargs.get('qt')
    #     else:
    #         qt = 2
    #     if 'resistance' in kwargs:
    #         resistance = kwargs.get('resistance')
    #     else:
    #         resistance = 0 

    #     self.head = 'C\x02\0\0\nfolder: ' + folder + '\nfileoverride\n' + \
    #                 'header: ' + header + '\n\n'
    #     self.body = 'tech=ocpt\nst=' + str(ttot) + '\neh=10' + \
    #                 '\nel=-10' + '\nsi=' + str(dt) + '\nqt=' + str(qt) +\
    #                 '\nrun\nsave:' + self.fileName + '\ntsave:' + self.fileName 
    #     self.foot = '\nforcequit: yesiamsure\n'
    #     self.text = self.head + self.body + self.foot

    #     self.validate(ttot, dt)

    # def validate(self, ttot, dt):
    #     info = Info()
    #     #info.limits(dt, info.dt_min, info.dt_max, 'dt', 's')
    #     #info.limits(ttot, info.ttot_min, info.ttot_max, 'ttot', 's')

class GamEIS(GamBase):
    """
        Pending:
        * Validate parameters
    """

    def __init__(self, Eini, low_freq, high_freq, amplitude, sens, **kwargs):
        super().__init__(**kwargs)

        print('EIS technique is still in development. Use with caution.')
        self.body = f'tech=imp\nei={Eini}\nfl={low_freq}\nfh={high_freq}\namp={amplitude}\nsens={sens}'
    # def __init__(self, Eini, low_freq, high_freq, amplitude, sens, folder, 
    #              fileName, header, path_lib, **kwargs):
    #     print('EIS technique is still in development. Use with caution.')
    #     self.fileName = fileName
    #     self.folder = folder
    #     self.text = ''

    #     if 'qt' in kwargs:
    #         qt = kwargs.get('qt')
    #     else:
    #         qt = 2 

    #     self.head = 'C\x02\0\0\nfolder: ' + folder + '\nfileoverride\n' + \
    #                 'header: ' + header + '\n\n'
    #     self.body = 'tech=imp\nei=' + str(Eini) + '\nfl=' + str(low_freq) + \
    #                 '\nfh=' + str(high_freq) + '\namp=' + str(amplitude) + \
    #                 '\nsens=' + str(sens) + '\nqt=' + str(qt) + \
    #                 '\nrun\nsave:' + self.fileName + '\ntsave:' + self.fileName 
    #     self.foot = '\nforcequit: yesiamsure\n'
    #     self.text = self.head + self.body + self.foot
