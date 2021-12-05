from time import sleep

import flyrpc.multicall

from visprotocol.protocol import clandinin_protocol


class DuoProtocol(clandinin_protocol.BaseProtocol):
    '''
    Todo:
    1, combine the parameters of the vprotocol and aprotocol for saving the epoch data
    2, use multicall or not, to send the load or start command
    '''
    def __init__(self, cfg, vprotocol, aprotocol):
        super().__init__(cfg)
        self.vprotocol = vprotocol
        self.aprotocol = aprotocol


    def loadStimuli(self, client):
        pass


    def startStimuli(self, client, append_stim_frames=False, print_profile=True):
        pass



class BaseProtocol(clandinin_protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def setBackground(self, client):
        pass

    def loadStimuli(self, client):
        passedParameters = self.epoch_parameters.copy()
        client.manager.load_stim(**passedParameters, device='speaker')


    def startStimuli(self, client, append_stim_frames=False, print_profile=True):
        sleep(self.run_parameters['pre_time'])
        client.manager.start_stim(device='speaker')
        sleep(self.run_parameters['stim_time'])

        # tail time
        client.manager.stop_stim(device='speaker')

        sleep(self.run_parameters['tail_time'])


class SineSongProtocol(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']

        frequency = self.protocol_parameters['frequency']
        current_frequency = self.selectParametersFromLists(frequency, randomize_order=self.protocol_parameters['randomize_order'])

        self.epoch_parameters = {'name': 'sine_song',
                                 'volume': self.protocol_parameters['volume'],
                                 'duration': stim_time,
                                 'freq': current_frequency}

        self.convenience_parameters = {'freq': current_frequency}  # what does this do?

    def getParameterDefaults(self):
        self.protocol_parameters = {'volume': 1.0,
                                    'frequency': [225.0, 120.0, 450.0, 900.0],
                                    'randomize_order': True}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'SineSong',
                               'num_epochs': 50,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.}



class PulseSongProtocol(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.getRunParameterDefaults()
        self.getParameterDefaults()

    def getEpochParameters(self):
        stim_time = self.run_parameters['stim_time']

        frequency = self.protocol_parameters['frequency']
        current_frequency = self.selectParametersFromLists(frequency, randomize_order=self.protocol_parameters['randomize_order'])

        # volume=1.0, duration=1.0, freq=125.0, pcycle=0.016, ncycle=0.020
        self.epoch_parameters = {'name': 'pulse_song',
                                 'volume': self.protocol_parameters['volume'],
                                 'duration': stim_time,
                                 'freq': current_frequency,
                                 'pcycle': self.protocol_parameters['pcycle'],
                                 'ncycle': self.protocol_parameters['ncycle']}

        self.convenience_parameters = {'freq': current_frequency}

    def getParameterDefaults(self):
        self.protocol_parameters = {'volume': 1.0,
                                    'frequency': [225.0, 120.0],
                                    'randomize_order': False,
                                    'pcycle': 0.016,
                                    'ncycle': 0.020}

    def getRunParameterDefaults(self):
        self.run_parameters = {'protocol_ID': 'PulseSong',
                               'num_epochs': 50,
                               'pre_time': 0.5,
                               'stim_time': 1.0,
                               'tail_time': 1.0,
                               'idle_color': 0.}