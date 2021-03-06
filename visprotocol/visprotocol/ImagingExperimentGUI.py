#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 10:51:42 2018

@author: mhturner
"""
import sys
from functools import partial

from PyQt5.QtWidgets import (QPushButton, QWidget, QLabel, QTextEdit, QGridLayout, QApplication,
                             QComboBox, QLineEdit, QFormLayout, QDialog, QFileDialog, QInputDialog,
                             QMessageBox, QCheckBox, QSpinBox, QTabWidget, QVBoxLayout, QFrame,
                             QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem)
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import QThread
import PyQt5.QtGui as QtGui
from datetime import datetime
import os
from visanalysis import plugin

from visprotocol.clandinin_client import Client
from visprotocol import clandinin_data, util, protocol
from visprotocol.control import EpochRun
from visprotocol.protocol.clandinin_protocol import DuoProtocol

class ImagingExperimentGUI(QWidget):

    def __init__(self):
        super().__init__()
        self.noteText = ''
        self.run_parameter_input = {}
        self.protocol_parameter_input = {}
        self.ignoreWarnings = False

        # user input for user name and rig config
        dialog = QDialog()
        dialog.ui = InitializeRigGUI(parent=dialog)
        dialog.ui.setupUI(self, dialog)
        dialog.setFixedSize(200, 200)
        dialog.exec_()

        # load user and rig configurations
        self.user_configuration = util.getUserConfiguration(self.user_name)
        self.cfg = self.user_configuration.copy()
        self.cfg['user_name'] = self.user_name
        self.cfg['rig_name'] = self.rig_name

        # start a client
        self.client = Client(self.cfg)

        # get a protocol, just start with the base class until user selects one
        self.protocol_object = getattr(protocol, self.user_name + '_protocol').BaseProtocol(self.cfg)
        # get available protocol classes
        self.available_visual_protocols = getattr(protocol, self.user_name + '_protocol').BaseProtocol.__subclasses__()
        try:
            self.available_auditory_protocols = getattr(protocol, self.user_name + '_audio_protocol').BaseProtocol.__subclasses__()
        except:
            self.available_auditory_protocols = getattr(protocol, 'example_audio_protocol').BaseProtocol.__subclasses__()

        self.vprotocol = None
        self.aprotocol = None
        self.run_params_dict = [0,1,2,3]
        self.protocol_params_dict = [0,1,2,3]

            # start a data object
        if self.protocol_object.rig == 'AODscope':
            self.data = clandinin_data.AODscopeData(self.cfg)
        else:
            self.data = clandinin_data.Data(self.cfg)

        # get an epoch run control object
        self.epoch_run = EpochRun()

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        self.control_tab = QWidget()
        self.control_grid = QGridLayout()
        self.control_grid.setSpacing(10)

        self.protocol_tab = QWidget()
        self.protocol_grid = QGridLayout()
        self.protocol_grid.setSpacing(10)

        self.serial_tab = QWidget()
        self.serial_grid = QGridLayout()
        self.serial_grid.setSpacing(10)

        self.data_tab = QWidget()
        self.data_grid = QFormLayout()
        self.data_grid.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.data_grid.setLabelAlignment(QtCore.Qt.AlignCenter)

        self.file_tab = QWidget()
        self.file_grid = QFormLayout()
        self.file_grid.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.file_grid.setLabelAlignment(QtCore.Qt.AlignCenter)

        self.tabs.addTab(self.control_tab, "Main")
        self.tabs.addTab(self.protocol_tab, "Visual")
        self.tabs.addTab(self.serial_tab, "Audio")
        self.tabs.addTab(self.data_tab, "Fly")
        self.tabs.addTab(self.file_tab, "File")

        self.tabs.resize(450, 500)

        # # # TAB 0: MAIN controls, for selecting / playing stimuli
        self.main_tab_layout()


        # # # TAB 1: Visual controls, for selecting / playing visual stimuli
        # Protocol ID drop-down:
        self.protocol_tab_layout()


        # # # TAB 2: serial controls, for selecting / playing auditory or other stimuli
        self.serial_tab_layout()


        # # # TAB 3: Current FLY metadata information
        # # Fly info:
        # Load any existing fly metadata in this file
        self.fly_tab_layout()


        # # # TAB 4: FILE tab - init, load, close etc. h5 file
        # Data file info
        # Initialize new experiment button
        self.file_tab_layout()


        # Add all layouts to window and show
        self.layout.addWidget(self.tabs)
        self.control_tab.setLayout(self.control_grid)
        self.protocol_tab.setLayout(self.protocol_grid)
        self.serial_tab.setLayout(self.serial_grid)
        self.data_tab.setLayout(self.data_grid)
        self.file_tab.setLayout(self.file_grid)
        self.setWindowTitle('Visprotocol')
        self.show()

    def main_tab_layout(self):

        # DuoProtocol
        self.multistimCheckBox = QCheckBox('Multistim')
        self.multistimCheckBox.setChecked(False)
        self.control_grid.addWidget(self.multistimCheckBox, 3, 0)
        self.multistimCheckBox.toggled.connect(lambda: self.onToggleBox(self.multistimCheckBox))

        # View button:
        self.viewButton = QPushButton("View", self)
        self.viewButton.clicked.connect(self.onPressedButton)
        self.control_grid.addWidget(self.viewButton, 4, 0)

        # Record button:
        self.recordButton = QPushButton("Record", self)
        self.recordButton.clicked.connect(self.onPressedButton)
        self.control_grid.addWidget(self.recordButton, 4, 1)

        # Pause/resume button:
        self.pauseButton = QPushButton("Pause", self)
        self.pauseButton.clicked.connect(self.onPressedButton)
        self.control_grid.addWidget(self.pauseButton, 4, 2)

        # Stop button:
        stopButton = QPushButton("Stop", self)
        stopButton.clicked.connect(self.onPressedButton)
        self.control_grid.addWidget(stopButton, 4, 3)

        # Enter note button:
        noteButton = QPushButton("Enter note", self)
        noteButton.clicked.connect(self.onPressedButton)
        self.control_grid.addWidget(noteButton, 5, 0)

        # Notes field:
        self.notesEdit = QTextEdit()
        self.control_grid.addWidget(self.notesEdit, 5, 1, 1, 2)

        # Status window:
        newLabel = QLabel('Status:')
        self.control_grid.addWidget(newLabel, 3, 2)
        self.status_label = QLabel()
        self.status_label.setFrameShadow(QFrame.Shadow(1))
        self.control_grid.addWidget(self.status_label, 3, 3)
        self.status_label.setText('')


        # Current imaging series counter
        newLabel = QLabel('Series counter:')
        self.control_grid.addWidget(newLabel, 2, 2)
        self.series_counter_input = QSpinBox()
        self.series_counter_input.setMinimum(1)
        self.series_counter_input.setMaximum(1000)
        self.series_counter_input.setValue(1)
        self.series_counter_input.valueChanged.connect(self.onEnteredSeriesCount)
        self.control_grid.addWidget(self.series_counter_input, 2, 3)


    def protocol_tab_layout(self):
        comboBox = QComboBox(self)
        comboBox.addItem("(select a protocol to run)")
        for sub_class in self.available_visual_protocols:
            comboBox.addItem(sub_class.__name__)
        protocol_label = QLabel('Protocol:')
        comboBox.activated[str].connect(self.onSelectedProtocolID)
        self.protocol_grid.addWidget(protocol_label, 1, 0)
        self.protocol_grid.addWidget(comboBox, 1, 1, 1, 1)

        # Parameter preset drop-down:
        parameter_preset_label = QLabel('Parameter_preset:')
        self.protocol_grid.addWidget(parameter_preset_label, 2, 0)
        self.updateParameterPresetSelector(self.protocol_grid)

        # Save parameter preset button:
        savePresetButton = QPushButton("Save preset", self)
        savePresetButton.clicked.connect(self.onPressedButton)
        self.protocol_grid.addWidget(savePresetButton, 2, 2)

        # Run paramters input:
        self.updateRunParamtersInput(self.protocol_grid)
        '''
        # View button:
        self.viewButton = QPushButton("View", self)
        self.viewButton.clicked.connect(self.onPressedButton)
        self.protocol_grid.addWidget(self.viewButton, self.run_params_ct+4, 0)

        # Record button:
        self.recordButton = QPushButton("Record", self)
        self.recordButton.clicked.connect(self.onPressedButton)
        self.protocol_grid.addWidget(self.recordButton, self.run_params_ct+4, 1)

        # Pause/resume button:
        self.pauseButton = QPushButton("Pause", self)
        self.pauseButton.clicked.connect(self.onPressedButton)
        self.protocol_grid.addWidget(self.pauseButton, self.run_params_ct+4, 2)

        # Stop button:
        stopButton = QPushButton("Stop", self)
        stopButton.clicked.connect(self.onPressedButton)
        self.protocol_grid.addWidget(stopButton, self.run_params_ct+4, 3)
        '''
        # Enter note button:
        noteButton = QPushButton("Enter note", self)
        noteButton.clicked.connect(self.onPressedButton)
        self.protocol_grid.addWidget(noteButton, self.run_params_ct+5, 0)

        # Notes field:
        self.notesEdit = QTextEdit()
        self.protocol_grid.addWidget(self.notesEdit, self.run_params_ct+5, 1, 1, 2)

        # Status window:
        newLabel = QLabel('Status:')
        self.protocol_grid.addWidget(newLabel, 3, 2)
        self.status_label = QLabel()
        self.status_label.setFrameShadow(QFrame.Shadow(1))
        self.protocol_grid.addWidget(self.status_label, 3, 3)
        self.status_label.setText('')

        # Imaging type dropdown (if AODscope):
        if self.data.rig == 'AODscope':
            self.imagingTypeComboBox = QComboBox(self)
            self.imagingTypeComboBox.addItem("POI")
            self.imagingTypeComboBox.addItem("xyt series")
            self.imagingTypeComboBox.activated[str].connect(self.onChangedDataType)
            self.protocol_grid.addWidget(self.imagingTypeComboBox, 5, 2)

        # Current imaging series counter
        newLabel = QLabel('Series counter:')
        self.protocol_grid.addWidget(newLabel, self.run_params_ct+2, 2)
        self.series_counter_input = QSpinBox()
        self.series_counter_input.setMinimum(1)
        self.series_counter_input.setMaximum(1000)
        self.series_counter_input.setValue(1)
        self.series_counter_input.valueChanged.connect(self.onEnteredSeriesCount)
        self.protocol_grid.addWidget(self.series_counter_input, self.run_params_ct+2, 3)


    def serial_tab_layout(self):
        comboBox = QComboBox(self)
        comboBox.addItem("(select a protocol to run)")
        for sub_class in self.available_auditory_protocols:
            comboBox.addItem(sub_class.__name__)
        protocol_label = QLabel('Protocol:')
        comboBox.activated[str].connect(self.onSelectedAudioProtocolID)
        self.serial_grid.addWidget(protocol_label, 1, 0)
        self.serial_grid.addWidget(comboBox, 1, 1, 1, 1)

        # Parameter preset drop-down:
        parameter_preset_label = QLabel('Parameter_preset:')
        self.serial_grid.addWidget(parameter_preset_label, 2, 0)
        self.updateParameterPresetSelector(self.serial_grid)

        # Save parameter preset button:
        savePresetButton = QPushButton("Save preset", self)
        savePresetButton.clicked.connect(self.onPressedButton)
        self.serial_grid.addWidget(savePresetButton, 2, 2)

        # Run paramters input:
        self.updateRunParamtersInput(self.serial_grid)
        '''
        # View button:
        self.viewButton = QPushButton("View", self)
        self.viewButton.clicked.connect(self.onPressedButton)
        self.serial_grid.addWidget(self.viewButton, self.run_params_ct+4, 0)

        # Record button:
        self.recordButton = QPushButton("Record", self)
        self.recordButton.clicked.connect(self.onPressedButton)
        self.serial_grid.addWidget(self.recordButton, self.run_params_ct+4, 1)

        # Pause/resume button:
        self.pauseButton = QPushButton("Pause", self)
        self.pauseButton.clicked.connect(self.onPressedButton)
        self.serial_grid.addWidget(self.pauseButton, self.run_params_ct+4, 2)

        # Stop button:
        stopButton = QPushButton("Stop", self)
        stopButton.clicked.connect(self.onPressedButton)
        self.serial_grid.addWidget(stopButton, self.run_params_ct+4, 3)
        '''
        # Enter note button:
        noteButton = QPushButton("Enter note", self)
        noteButton.clicked.connect(self.onPressedButton)
        self.serial_grid.addWidget(noteButton, self.run_params_ct+5, 0)

        # Notes field:
        self.notesEdit = QTextEdit()
        self.serial_grid.addWidget(self.notesEdit, self.run_params_ct+5, 1, 1, 2)

        # Status window:
        newLabel = QLabel('Status:')
        self.serial_grid.addWidget(newLabel, 3, 2)
        self.status_label = QLabel()
        self.status_label.setFrameShadow(QFrame.Shadow(1))
        self.serial_grid.addWidget(self.status_label, 3, 3)
        self.status_label.setText('')

        # Imaging type dropdown (if AODscope):
        if self.data.rig == 'AODscope':
            self.imagingTypeComboBox = QComboBox(self)
            self.imagingTypeComboBox.addItem("POI")
            self.imagingTypeComboBox.addItem("xyt series")
            self.imagingTypeComboBox.activated[str].connect(self.onChangedDataType)
            self.serial_grid.addWidget(self.imagingTypeComboBox, 5, 2)

        # Current imaging series counter
        newLabel = QLabel('Series counter:')
        self.serial_grid.addWidget(newLabel, self.run_params_ct+2, 2)
        self.series_counter_input = QSpinBox()
        self.series_counter_input.setMinimum(1)
        self.series_counter_input.setMaximum(1000)
        self.series_counter_input.setValue(1)
        self.series_counter_input.valueChanged.connect(self.onEnteredSeriesCount)
        self.serial_grid.addWidget(self.series_counter_input, self.run_params_ct+2, 3)


    def fly_tab_layout(self):
        newLabel = QLabel('Load existing fly')
        self.existing_fly_input = QComboBox()
        self.existing_fly_input.activated[int].connect(self.onSelectedExistingFly)
        self.data_grid.addRow(newLabel, self.existing_fly_input)
        self.updateExistingFlyInput()

        newLabel = QLabel('Current fly info:')
        newLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.data_grid.addRow(newLabel)

        # Fly ID:
        newLabel = QLabel('Fly ID:')
        self.fly_id_input = QLineEdit()
        self.data_grid.addRow(newLabel, self.fly_id_input)
        # Sex:
        newLabel = QLabel('Sex:')
        self.fly_sex_input = QComboBox()
        self.fly_sex_input.addItems(['Female', 'Male'])
        self.data_grid.addRow(newLabel, self.fly_sex_input)
        # Age:
        newLabel = QLabel('Age:')
        self.fly_age_input = QSpinBox()
        self.fly_age_input.setMinimum(0)
        self.fly_age_input.setValue(1)
        self.data_grid.addRow(newLabel, self.fly_age_input)
        # Prep ID:
        newLabel = QLabel('Prep:')
        self.fly_prep_input = QComboBox()
        self.fly_prep_input.addItem("")
        for choiceID in self.data.prepChoices:
            self.fly_prep_input.addItem(choiceID)
        self.data_grid.addRow(newLabel, self.fly_prep_input)
        # Driver1:
        newLabel = QLabel('Driver_1:')
        self.fly_driver_1 = QComboBox()
        self.fly_driver_1.addItem("")
        for choiceID in self.data.driverChoices:
            self.fly_driver_1.addItem(choiceID)
        self.data_grid.addRow(newLabel, self.fly_driver_1)
        # Indicator1:
        newLabel = QLabel('Indicator_1:')
        self.fly_indicator_1 = QComboBox()
        self.fly_indicator_1.addItem("")
        for choiceID in self.data.indicatorChoices:
            self.fly_indicator_1.addItem(choiceID)
        self.data_grid.addRow(newLabel, self.fly_indicator_1)
        # Driver2:
        newLabel = QLabel('Driver_2:')
        self.fly_driver_2 = QComboBox()
        self.fly_driver_2.addItem("")
        for choiceID in self.data.driverChoices:
            self.fly_driver_2.addItem(choiceID)
        self.data_grid.addRow(newLabel, self.fly_driver_2)
        # Indicator2:
        newLabel = QLabel('Indicator_2:')
        self.fly_indicator_2 = QComboBox()
        self.fly_indicator_2.addItem("")
        for choiceID in self.data.indicatorChoices:
            self.fly_indicator_2.addItem(choiceID)
        self.data_grid.addRow(newLabel, self.fly_indicator_2)
        # Fly genotype:
        newLabel = QLabel('Genotype:')
        self.fly_genotype_input = QLineEdit()
        self.data_grid.addRow(newLabel, self.fly_genotype_input)

        # Create fly button
        new_separator_line = QFrame()
        new_separator_line.setFrameShape(new_separator_line.HLine)
        self.data_grid.addRow(new_separator_line)

        createFlyButton = QPushButton("Create fly", self)
        createFlyButton.clicked.connect(self.onCreatedFly)
        self.data_grid.addRow(createFlyButton)


    def file_tab_layout(self):
        initializeButton = QPushButton("Initialize experiment", self)
        initializeButton.clicked.connect(self.onPressedButton)
        newLabel = QLabel('Current data file:')
        self.file_grid.addRow(initializeButton, newLabel)
        # Load existing experiment button
        loadButton = QPushButton("Load experiment", self)
        loadButton.clicked.connect(self.onPressedButton)
        # Label with current expt file
        self.currentExperimentLabel = QLabel('')
        self.file_grid.addRow(loadButton, self.currentExperimentLabel)

        # # # # Data browser: # # # # # # # #
        self.groupTree = QTreeWidget(self)
        self.groupTree.setHeaderHidden(True)
        self.groupTree.itemClicked.connect(self.onTreeItemClicked)
        self.file_grid.addRow(self.groupTree)

        # Attribute table
        self.tableAttributes = QTableWidget()
        self.tableAttributes.setStyleSheet("")
        self.tableAttributes.setColumnCount(2)
        self.tableAttributes.setObjectName("tableAttributes")
        self.tableAttributes.setRowCount(0)
        item = QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(10)
        item.setFont(font)
        item.setBackground(QtGui.QColor(121, 121, 121))
        brush = QtGui.QBrush(QtGui.QColor(91, 91, 91))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.tableAttributes.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem()
        item.setBackground(QtGui.QColor(123, 123, 123))
        brush = QtGui.QBrush(QtGui.QColor(91, 91, 91))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.tableAttributes.setHorizontalHeaderItem(1, item)
        self.tableAttributes.horizontalHeader().setCascadingSectionResizes(True)
        self.tableAttributes.horizontalHeader().setDefaultSectionSize(200)
        self.tableAttributes.horizontalHeader().setHighlightSections(False)
        self.tableAttributes.horizontalHeader().setSortIndicatorShown(True)
        self.tableAttributes.horizontalHeader().setStretchLastSection(True)
        self.tableAttributes.verticalHeader().setVisible(False)
        self.tableAttributes.verticalHeader().setHighlightSections(False)
        self.tableAttributes.setMinimumSize(QtCore.QSize(200, 400))
        item = self.tableAttributes.horizontalHeaderItem(0)
        item.setText("Attribute")
        item = self.tableAttributes.horizontalHeaderItem(1)
        item.setText("Value")

        self.tableAttributes.itemChanged.connect(self.update_attrs_to_file)

        self.file_grid.addRow(self.tableAttributes)


    def onChangedDataType(self, text):
        if text == 'POI':
            self.data.poi_scan = True
        elif text == 'xyt series':
            self.data.poi_scan = False
        else:
            self.data.poi_scan = False

        self.series_counter_input.setValue(self.data.getSeriesCount())


    def onSelectedProtocolID(self, text):
        if text == "(select a protocol to run)":
            return
        # Clear old params list from grid
        self.resetLayout(self.protocol_grid)

        # initialize the selected protocol object
        prot_names = [x.__name__ for x in self.available_visual_protocols]
        self.protocol_object = self.available_visual_protocols[prot_names.index(text)](self.cfg)
        self.vprotocol = self.protocol_object

        # update display lists of run & protocol parameters
        self.protocol_object.loadParameterPresets()
        self.updateParameterPresetSelector(self.protocol_grid)
        self.updateProtocolParametersInput(self.protocol_grid)
        self.updateRunParamtersInput(self.protocol_grid)
        self.show()


    def onSelectedAudioProtocolID(self, text):
        if text == "(select a protocol to run)":
            return
        # Clear old params list from grid
        self.resetLayout(self.serial_grid)

        # initialize the selected protocol object
        prot_names = [x.__name__ for x in self.available_auditory_protocols]
        self.protocol_object = self.available_auditory_protocols[prot_names.index(text)](self.cfg)
        self.aprotocol = self.protocol_object

        # update display lists of run & protocol parameters
        self.protocol_object.loadParameterPresets()
        self.updateParameterPresetSelector(self.serial_grid)
        self.updateProtocolParametersInput(self.serial_grid)
        self.updateRunParamtersInput(self.serial_grid)
        self.show()


    def onPressedButton(self):
        sender = self.sender()
        if sender.text() == 'Record':
            if (self.data.experimentFileExists() and self.data.currentFlyExists()):
                self.sendRun(save_metadata_flag=True)
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("You have not initialized a data file and/or fly yet")
                msg.setInformativeText("You can show stimuli by clicking the View button, but no metadata will be saved")
                msg.setWindowTitle("No experiment file and/or fly")
                msg.setDetailedText("Initialize or load both an experiment file and a fly if you'd like to save your metadata")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        elif sender.text() == 'View':
            self.sendRun(save_metadata_flag=False)
            self.pauseButton.setText('Pause')

        elif sender.text() == 'Pause':
            self.epoch_run.pauseRun()
            self.pauseButton.setText('Resume')
            self.status_label.setText('Paused...')
            self.show()

        elif sender.text() == 'Resume':
            self.epoch_run.resumeRun()
            self.pauseButton.setText('Pause')
            self.status_label.setText('Viewing...')
            self.show()

        elif sender.text() == 'Stop':
            self.epoch_run.stopRun()
            self.pauseButton.setText('Pause')

        elif sender.text() == 'Enter note':
            self.noteText = self.notesEdit.toPlainText()
            if self.data.experimentFileExists():
                self.data.createNote(self.noteText)  # save note to expt file
                self.notesEdit.clear()  # clear notes box
            else:
                self.notesEdit.setTextColor(QtGui.QColor("Red"))

        elif sender.text() == 'Save preset':
            self.updateParametersFromFillableFields()  # get the state of the param input from GUI
            start_name = self.parameter_preset_comboBox.currentText()
            if start_name == 'Default':
                start_name = ''

            text, _ = QInputDialog.getText(self, "Save preset", "Preset Name:", QLineEdit.Normal, start_name)

            self.protocol_object.updateParameterPresets(text)

        elif sender.text() == 'Initialize experiment':
            dialog = QDialog()

            dialog.ui = InitializeExperimentGUI(parent=dialog)
            dialog.ui.setupUI(self, dialog)
            dialog.setFixedSize(300, 200)
            dialog.exec_()

            self.data.experiment_file_name = dialog.ui.le_FileName.text()
            self.data.data_directory = dialog.ui.le_DataDirectory.text()
            self.data.experimenter = dialog.ui.le_Experimenter.text()

            self.updateExistingFlyInput()
            self.populateGroups()

        elif sender.text() == 'Load experiment':
            filePath, _ = QFileDialog.getOpenFileName(self, "Open file")
            self.data.experiment_file_name = os.path.split(filePath)[1].split('.')[0]
            self.data.data_directory = os.path.split(filePath)[0]

            if self.data.experiment_file_name != '':
                self.currentExperimentLabel.setText(self.data.experiment_file_name)
                # update series count to reflect already-collected series
                self.data.reloadSeriesCount()
                self.series_counter_input.setValue(self.data.getHighestSeriesCount() + 1)
                self.updateExistingFlyInput()
                self.populateGroups()


    def onToggleBox(self, box):
        if box.text() == 'Multistim':
            if box.isChecked() == True:
                self.pre_protocol_project = self.protocol_object
                if self.aprotocol and self.vprotocol:
                    self.protocol_object = DuoProtocol(self.cfg, self.vprotocol, self.aprotocol)

            else:
                self.protocol_object = self.pre_protocol_project


    def onCreatedFly(self):
        # Populate fly metadata from fly data fields
        fly_metadata = {'fly_id': self.fly_id_input.text(),
                        'sex': self.fly_sex_input.currentText(),
                        'age': self.fly_age_input.value(),
                        'prep': self.fly_prep_input.currentText(),
                        'driver_1': self.fly_driver_1.currentText(),
                        'indicator_1': self.fly_indicator_1.currentText(),
                        'driver_2': self.fly_driver_2.currentText(),
                        'indicator_2': self.fly_indicator_2.currentText(),
                        'genotype': self.fly_genotype_input.text()}
        self.data.createFly(fly_metadata)  # creates new fly and selects it as the current fly
        self.updateExistingFlyInput()


    def resetLayout(self, grid):
        # TODO: the 6 here is hard coded, and corresponds to the 5 in updateProtocolParametersInput
        # TODO: need to change this ultimately
        space_ct = 6
        for ii in range(len(self.protocol_object.protocol_parameters.items())):
            item = grid.itemAtPosition(self.run_params_ct+space_ct+ii, 0)
            if item is not None:
                item.widget().deleteLater()
            item = grid.itemAtPosition(self.run_params_ct+space_ct+ii, 1)
            if item is not None:
                item.widget().deleteLater()
        self.show()


    def updateProtocolParametersInput(self, grid):
        # update display window to show parameters for this protocol
        #self.protocol_parameter_input = {}  # clear old input params dict
        self.protocol_params_dict[self.tabs.currentIndex()] = {}
        space_ct = 5
        ct = 0
        for key, value in self.protocol_object.protocol_parameters.items():
            ct += 1
            newLabel = QLabel(key + ':')
            grid.addWidget(newLabel, self.run_params_ct + space_ct + ct, 0)  # was +5

            if isinstance(value, bool):
                self.protocol_params_dict[self.tabs.currentIndex()][key] = QCheckBox()
                self.protocol_params_dict[self.tabs.currentIndex()][key].setChecked(value)
            else:
                self.protocol_params_dict[self.tabs.currentIndex()][key] = QLineEdit()
                if isinstance(value, int):
                    self.protocol_params_dict[self.tabs.currentIndex()][key].setValidator(QtGui.QIntValidator())
                elif isinstance(value, float):
                    self.protocol_params_dict[self.tabs.currentIndex()][key].setValidator(QtGui.QDoubleValidator())

                self.protocol_params_dict[self.tabs.currentIndex()][key].setText(str(value))  # set to default value
            grid.addWidget(self.protocol_params_dict[self.tabs.currentIndex()][key], self.run_params_ct + space_ct + ct, 1, 1, 2) # was +5

        self.protocol_parameter_input = self.protocol_params_dict[self.tabs.currentIndex()]



    def updateParameterPresetSelector(self, grid):
        self.parameter_preset_comboBox = QComboBox(self)
        self.parameter_preset_comboBox.addItem("Default")
        for name in self.protocol_object.parameter_presets.keys():
            self.parameter_preset_comboBox.addItem(name)
        self.parameter_preset_comboBox.activated[str].connect(partial(self.onSelectedParameterPreset, grid))
        grid.addWidget(self.parameter_preset_comboBox, 2, 1, 1, 1)


    def onSelectedParameterPreset(self, grid, text):
        self.protocol_object.selectProtocolPreset(text)
        self.resetLayout(grid)
        self.updateProtocolParametersInput(grid)
        self.updateRunParamtersInput(grid)
        self.show()


    def onSelectedExistingFly(self, index):
        fly_data = self.data.getExistingFlyData()
        self.populateFlyMetadataFields(fly_data[index])
        self.data.current_fly = fly_data[index].get('fly_id')


    def updateExistingFlyInput(self):
        self.existing_fly_input.clear()
        for fly_data in self.data.getExistingFlyData():
            self.existing_fly_input.addItem(fly_data['fly_id'])
        index = self.existing_fly_input.findText(self.data.current_fly)
        if index >= 0:
            self.existing_fly_input.setCurrentIndex(index)


    def populateFlyMetadataFields(self, fly_data_dict):
        self.fly_id_input.setText(fly_data_dict['fly_id'])
        self.fly_sex_input.setCurrentText(fly_data_dict['sex'])
        self.fly_age_input.setValue(fly_data_dict['age'])
        self.fly_driver_1.setCurrentText(fly_data_dict['driver_1'])
        self.fly_indicator_1.setCurrentText(fly_data_dict['indicator_1'])
        self.fly_driver_2.setCurrentText(fly_data_dict['driver_2'])
        self.fly_indicator_2.setCurrentText(fly_data_dict['indicator_2'])
        self.fly_genotype_input.setText(fly_data_dict['genotype'])


    def updateRunParamtersInput(self, grid):
        self.run_params_ct = 0
        # Run parameters list
        self.run_params_dict[self.tabs.currentIndex()] = {}
        for key, value in self.protocol_object.run_parameters.items():
            if key not in ['protocol_ID', 'run_start_time']:
                self.run_params_ct += 1
                # delete existing labels:
                item = grid.itemAtPosition(2 + self.run_params_ct, 0)
                if item is not None:
                    item.widget().deleteLater()

                # write new labels:
                newLabel = QLabel(key + ':')
                grid.addWidget(newLabel, 2 + self.run_params_ct, 0)

                self.run_params_dict[self.tabs.currentIndex()][key] = QLineEdit()
                if isinstance(value, int):
                    validator = QtGui.QIntValidator()
                    validator.setBottom(0)
                elif isinstance(value, float):
                    validator = QtGui.QDoubleValidator()
                    validator.setBottom(0)
                self.run_params_dict[self.tabs.currentIndex()][key].setValidator(validator)
                self.run_params_dict[self.tabs.currentIndex()][key].setText(str(value))
                grid.addWidget(self.run_params_dict[self.tabs.currentIndex()][key], 2 + self.run_params_ct, 1, 1, 1)

        self.run_parameter_input = self.run_params_dict[self.tabs.currentIndex()]


    def onEnteredSeriesCount(self):
        self.data.updateSeriesCount(self.series_counter_input.value())
        if self.data.experimentFileExists:
            if self.data.getSeriesCount() <= self.data.getHighestSeriesCount():
                self.series_counter_input.setStyleSheet("background-color: rgb(0, 255, 255);")
            else:
                self.series_counter_input.setStyleSheet("background-color: rgb(255, 255, 255);")


    def sendRun(self, save_metadata_flag=True):
        # check to make sure a protocol has been selected
        if self.protocol_object.run_parameters['protocol_ID'] == '':
                self.status_label.setText('Select a protocol')
                return  # no protocol exists, don't send anything

        # check to make sure the series count does not already exist
        if save_metadata_flag:
            self.data.updateSeriesCount(self.series_counter_input.value())
            if (self.data.getSeriesCount() in self.data.getExistingSeries()):
                self.series_counter_input.setStyleSheet("background-color: rgb(0, 255, 255);")
                return  # group already exists, don't send anything
            else:
                self.series_counter_input.setStyleSheet("background-color: rgb(255, 255, 255);")

        # Populate parameters from filled fields
        self.updateParametersFromFillableFields()

        # start the epoch run thread:
        self.runSeriesThread = runSeriesThread(self.epoch_run,
                                               self.protocol_object,
                                               self.data,
                                               self.client,
                                               save_metadata_flag)

        self.runSeriesThread.finished.connect(lambda: self.runFinished(save_metadata_flag))
        self.runSeriesThread.started.connect(lambda: self.runStarted(save_metadata_flag))

        self.runSeriesThread.start()


    def runStarted(self, save_metadata_flag):
        # Lock the view and run buttons to prevent spinning up multiple threads
        self.viewButton.setEnabled(False)
        self.recordButton.setEnabled(False)
        if save_metadata_flag:
            self.status_label.setText('Recording series ' + str(self.data.getSeriesCount()))
        else:
            self.status_label.setText('Viewing...')


    def runFinished(self, save_metadata_flag):
        # re-enable view/record buttons
        self.viewButton.setEnabled(True)
        self.recordButton.setEnabled(True)

        self.status_label.setText('Ready')
        self.pauseButton.setText('Pause')
        if save_metadata_flag:
            self.updateExistingFlyInput()
            # Advance the series_count:
            self.data.advanceSeriesCount()
            self.series_counter_input.setValue(self.data.getSeriesCount())
            self.populateGroups()


    def updateParametersFromFillableFields(self):

        if isinstance(self.protocol_object, DuoProtocol):
            self.protocol_object.run_parameters.update(self.runParamsSerializer(self.run_parameter_input))
            self.protocol_object.vprotocol.run_parameters.update(self.runParamsSerializer(self.run_params_dict[1]))
            self.protocol_object.aprotocol.run_parameters.update(self.runParamsSerializer(self.run_params_dict[2]))
            self.protocol_object.vprotocol.protocol_parameters.update(self.protocolParamsSerializer(self.protocol_params_dict[1]))
            self.protocol_object.aprotocol.protocol_parameters.update(self.protocolParamsSerializer(self.protocol_params_dict[2]))
            self.protocol_object.combineProtocolParams()
        else:
            self.protocol_object.run_parameters.update(self.runParamsSerializer(self.run_parameter_input))
            self.protocol_object.protocol_parameters.update(self.protocolParamsSerializer(self.protocol_parameter_input))


    def runParamsSerializer(self, run_params_input):
        run_params = {}
        for key, value in run_params_input.items():
            run_params[key] = float(value.text())

        return run_params


    def protocolParamsSerializer(self, protocol_params_input):
        protocol_params = {}
        for key, value in protocol_params_input.items():
            if isinstance(value, QCheckBox): #QCheckBox
                protocol_params[key] = value.isChecked()
            elif isinstance(value, str):
                protocol_params[key] = value.text() # Pass the string
            else:  # QLineEdit
                new_param_entry = value.text()

                if new_param_entry[0] == '[':  # User trying to enter a list of values
                    to_a_list = []
                    for x in new_param_entry[1:-1].split(','): to_a_list.append(float(x))
                    protocol_params[key] = to_a_list
                else:
                    protocol_params[key] = float(new_param_entry)

        return protocol_params


    def populateGroups(self):
        file_path = os.path.join(self.data.data_directory, self.data.experiment_file_name + '.hdf5')
        group_dset_dict = plugin.base.getHierarchy(file_path, additional_exclusions='rois')
        self._populateTree(self.groupTree, group_dset_dict)


    def _populateTree(self, widget, dict):
        widget.clear()
        self.fill_item(widget.invisibleRootItem(), dict)


    def fill_item(self, item, value):
        item.setExpanded(True)
        if type(value) is dict:
            for key, val in sorted(value.items()):
                child = QTreeWidgetItem()
                child.setText(0, key)
                item.addChild(child)
                self.fill_item(child, val)
        elif type(value) is list:
            for val in value:
                child = QTreeWidgetItem()
                item.addChild(child)
                if type(val) is dict:
                    child.setText(0, '[dict]')
                    self.fill_item(child, val)
                elif type(val) is list:
                    child.setText(0, '[list]')
                    self.fill_item(child, val)
                else:
                    child.setText(0, val)
                child.setExpanded(True)
        else:
            child = QTreeWidgetItem()
            child.setText(0, value)
            item.addChild(child)


    def onTreeItemClicked(self, item, column):
        file_path = os.path.join(self.data.data_directory, self.data.experiment_file_name + '.hdf5')
        group_path = plugin.base.getPathFromTreeItem(self.groupTree.selectedItems()[0])

        if group_path != '':
            attr_dict = plugin.base.getAttributesFromGroup(file_path, group_path)
            if 'series' in group_path.split('/')[-1]:
                editable_values = False  # don't let user edit epoch parameters
            else:
                editable_values = True
            self.populate_attrs(attr_dict = attr_dict, editable_values = editable_values)


    def populate_attrs(self, attr_dict=None, editable_values=False):
        """ Populate attribute for currently selected group """
        self.tableAttributes.blockSignals(True)  # block udpate signals for auto-filled forms
        self.tableAttributes.setRowCount(0)
        self.tableAttributes.setColumnCount(2)
        self.tableAttributes.setSortingEnabled(False)

        if attr_dict:
            for num, key in enumerate(attr_dict):
                self.tableAttributes.insertRow(self.tableAttributes.rowCount())
                key_item = QTableWidgetItem(key)
                key_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.tableAttributes.setItem(num, 0, key_item)

                val_item = QTableWidgetItem(str(attr_dict[key]))
                if editable_values:
                    val_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
                else:
                    val_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.tableAttributes.setItem(num, 1, val_item)

        self.tableAttributes.blockSignals(False)


    def update_attrs_to_file(self, item):
        file_path = os.path.join(self.data.data_directory, self.data.experiment_file_name + '.hdf5')
        group_path = plugin.base.getPathFromTreeItem(self.groupTree.selectedItems()[0])

        attr_key = self.tableAttributes.item(item.row(), 0).text()
        attr_val = item.text()

        # update attr in file
        plugin.base.changeAttribute(file_path, group_path, attr_key, attr_val)
        print('Changed attr {} to = {}'.format(attr_key, attr_val))

# # # Other accessory classes. For data file initialization and threading # # # #


class InitializeExperimentGUI(QWidget):
    def setupUI(self, experimentGuiObject, parent=None):
        super(InitializeExperimentGUI, self).__init__(parent)
        self.parent = parent
        self.experimentGuiObject = experimentGuiObject
        layout = QFormLayout()

        label_FileName = QLabel('File Name:')
        init_now = datetime.now()
        defaultName = init_now.isoformat()[:-16]
        self.le_FileName = QLineEdit(defaultName)
        layout.addRow(label_FileName, self.le_FileName)

        button_SelectDirectory = QPushButton("Select Directory...", self)
        button_SelectDirectory.clicked.connect(self.onPressedDirectoryButton)
        self.le_DataDirectory = QLineEdit(self.experimentGuiObject.data.data_directory)
        layout.addRow(button_SelectDirectory, self.le_DataDirectory)

        label_Experimenter = QLabel('Experimenter:')
        self.le_Experimenter = QLineEdit(self.experimentGuiObject.data.experimenter)
        layout.addRow(label_Experimenter, self.le_Experimenter)

        self.label_status = QLabel('Enter experiment info')
        layout.addRow(self.label_status)

        enterButton = QPushButton("Enter", self)
        enterButton.clicked.connect(self.onPressedEnterButton)
        layout.addRow(enterButton)

        self.setLayout(layout)

    def onPressedEnterButton(self):
        self.experimentGuiObject.data.experiment_file_name = self.le_FileName.text()
        self.experimentGuiObject.data.data_directory = self.le_DataDirectory.text()
        self.experimentGuiObject.data.experimenter = self.le_Experimenter.text()

        if os.path.isfile(os.path.join(self.experimentGuiObject.data.data_directory, self.experimentGuiObject.data.experiment_file_name) + '.hdf5'):
           self.label_status.setText('Experiment file already exists!')
        elif not os.path.isdir(self.experimentGuiObject.data.data_directory):
            self.label_status.setText('Data directory does not exist!')
        else:
            self.label_status.setText('Data entered')
            self.experimentGuiObject.currentExperimentLabel.setText(self.experimentGuiObject.data.experiment_file_name)
            self.experimentGuiObject.data.initializeExperimentFile()
            self.experimentGuiObject.series_counter_input.setValue(1)
            self.close()
            self.parent.close()

    def onPressedDirectoryButton(self):
        filePath = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.le_DataDirectory.setText(filePath)

class InitializeRigGUI(QWidget):
    def setupUI(self, experimentGuiObject, parent=None):
        super(InitializeRigGUI, self).__init__(parent)
        self.parent = parent
        self.experimentGuiObject = experimentGuiObject
        self.user_name = None
        self.available_rig_configs = []

        self.layout = QFormLayout()
        self.resize(200, 400)

        label_UserName = QLabel('User Name:')
        self.UserComboBox = QComboBox()
        self.UserComboBox.activated[str].connect(self.onSelectedUserName)
        for choiceID in util.getAvailableUserNames():
            self.UserComboBox.addItem(choiceID)
        self.layout.addRow(label_UserName, self.UserComboBox)

        label_RigName = QLabel('Rig Config:')
        self.RigComboBox = QComboBox()
        self.RigComboBox.activated[str].connect(self.onSelectedRig)
        self.layout.addRow(label_RigName, self.RigComboBox)
        self.updateAvailableRigs()

        self.setLayout(self.layout)
        self.show()

    def updateAvailableRigs(self):
        self.RigComboBox.clear()
        for choiceID in self.available_rig_configs:
            self.RigComboBox.addItem(choiceID)

    def onSelectedUserName(self, text):
        self.user_name = text
        self.available_rig_configs = util.getAvailableRigConfigs(self.user_name)
        self.updateAvailableRigs()
        self.show()

    def onSelectedRig(self, text):
        self.rig_name = text
        self.experimentGuiObject.user_name = self.user_name
        self.experimentGuiObject.rig_name = self.rig_name
        self.close()
        self.parent.close()


class runSeriesThread(QThread):
    # https://nikolak.com/pyqt-threading-tutorial/
    # https://stackoverflow.com/questions/41848769/pyqt5-object-has-no-attribute-connect
    def __init__(self, epoch_run, protocol_object, data, client, save_metadata_flag):
        QThread.__init__(self)
        self.epoch_run = epoch_run
        self.protocol_object = protocol_object
        self.data = data
        self.client = client
        self.save_metadata_flag = save_metadata_flag

    def __del__(self):
        self.wait()

    def _sendRun(self):
        self.epoch_run.startRun(self.protocol_object, self.data, self.client, save_metadata_flag=self.save_metadata_flag)

    def run(self):
        self._sendRun()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImagingExperimentGUI()
    sys.exit(app.exec_())
