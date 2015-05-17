#!/usr/bin/env python
"""
Formant Editor, Version 0.8.2d
Copyright (C) 2014, Marton Soskuthy

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

Last modified: 17/05/2015
"""
from __future__ import division
from Tkinter import *
from random import shuffle
from operator import itemgetter
import os
import inspect
import shutil
import codecs
import platform
import subprocess
import cProfile
import pickle
import tkFileDialog
import sys
import pdb
import re
import ast
from time import time
from math import log
from copy import copy


script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
if script_dir not in sys.path:
    sys.path.append(script_dir)

from custom_python.csv_custom import readCSV, writeCSV
from custom_python import tkSimpleDialog
from custom_snack import tkSnack



class formantMonitor:

    ##################
    #                #
    # INITIALISATION #
    #                #
    ##################
    
    def __init__ (self, master, script_dir):

        # figure out OS

        self.platform = platform.system()
        self.os_release = platform.release()

        # set up directories

        self.master = master
        self.script_dir = script_dir

        # set up status bar parameters

        self.status_bar_location_size = 30
        self.status_fade_time = 10000

        # set up zoom/movement parameters

        self.dpi = 150
        self.zoom_amount = 0.5
        self.scroll_amount = 0.25

        # set up selection variables

        self.selected_boundaries = []
        self.selected_points = []
        self.drag_data = {"x": 0, "y": 0, "item_id": None}
        self.select_anchor_x = -1
        self.select_anchor_y = -1

        # set up display parameters

        self.boundary_colour = "blue"
        self.boundary_selected_colour = "darkblue"
        self.tag_colour = "#%02x%02x%02x" % (255, 0, 0)
        self.tag_selected_colour = "#%02x%02x%02x" % (160, 0, 0)
        self.trajectory_colour = "#29f"
        self.regular_from = (18, 84, 238)
        self.regular_to = (176, 226, 255) 
        self.selected_from = (self.regular_from[0] * 0.6, self.regular_from[1] * 0.6, self.regular_from[2] * 0.6)
        self.selected_to = (self.regular_to[0] * 0.6, self.regular_to[1] * 0.6, self.regular_to[2] * 0.6) 
        self.boundary_text_colour = "#%02x%02x%02x" % self.regular_from
        
        self.boundary_width = 6
        self.trajectory_width = 10
        self.formant_outline_width = 2

        self.formant_line_colour = "red"
        self.formant_line_width = 1

        # set up play parameters
        
        self.play_cursor_width = 2
        self.play_cursor_colour = "red"
        self.play_cursor_delay = 25 # ms
        self.sound = tkSnack.Sound()
        self.play_selection_start_x = -1
        self.play_selection_end_x = -1
        self.play_selection_on = False
        
        # set up formant/spectrogram parameters

        self.analysis_parameter_list = ["spectrogram_window_length",
                                        "spectrogram_max_freq",
                                        "spectrogram_brightness",
                                        "formant_window_length",
                                        "formant_pre_emph",
                                        "formant_max_freq",
                                        "formant_number_of_formants",
                                        "formant_use_number"]
        self.formant_parameters = ["formant_window_length",
                                   "formant_pre_emph",
                                   "formant_max_freq",
                                   "formant_number_of_formants"]
        self.display_parameters = ["spectrogram_window_length",
                                   "spectrogram_max_freq",
                                   "spectrogram_brightness",
                                   "formant_use_number"]
        self.spectrogram_window_length = 0.005
        self.spectrogram_max_freq = 5000
        self.spectrogram_brightness = 0
        self.formant_window_length = 0.025
        self.formant_pre_emph = 50
        self.formant_max_freq = 5000
        self.formant_number_of_measurements = 11
        self.formant_number_of_formants = 5
        self.formant_use_number = 3
        self.formant_minimum_separation = 100

        self.spectrogram_brightening_amount = 50
        
        self.available_formants = 0

        # to avoid problems with key debouncing

        self.afterId = None

        # initialisation parameters

        self.spectrogram_initialised = False
        self.frd = ""
        self.current_csv = ""
        self.filter_expression = ""

        # export parameters

        self.export_format = "measurements"
        self.export_number_of_formants = self.formant_use_number
        
        # set up GUI

        self.current_redrawn_formant = 0
        self.hide_measurements = False
        
        self.maximise()
        self.outer_frame = Frame(master)
        self.outer_frame.pack(fill=BOTH, expand=1,pady=20,padx=20)
        self.createCoords()
        self.createMenu()
        self.createFileList()
        self.createImage()
        self.createFormantBox()
        self.createButtonBox()
        self.createMetadataViewer()

        # read/create config file

        self.readConfig()

        self.prepTempDir()

    def readConfig (self):
        config_path = os.path.join(self.script_dir, "init.cfg")
        if os.path.exists(config_path):
            f = codecs.open(config_path, 'rb')
            parameters = pickle.load(f)
            f.close()
            for parameter in parameters:
                vars(self)[parameter] = parameters[parameter]
            self.configTest()
        else:
            parameters = {"program_folder":self.script_dir, "temporary_folder":os.path.join(self.script_dir, 'tmp'), "praat_path":''}
            self.config(parameters)

    def configWrapper (self):
        self.config({"program_folder":self.program_folder, "temporary_folder":self.temporary_folder, "praat_path":self.praat_path})

    def config (self, parameters):
        new_parameters = ConfigWindow(self.master, title="Configuration settings", parameters=parameters).output
        for parameter in new_parameters:
            vars(self)[parameter] = parameters[parameter]
        self.config_works = self.configTest()
        if self.config_works:
            config_path = os.path.join(self.script_dir, "init.cfg")
            f = codecs.open(config_path, 'wb')
            pickle.dump(parameters, f)
            f.close()
        

    def configTest (self):
        for i in [0,4]:
            self.filemenu.entryconfig(i, state=DISABLED)
        if not os.path.exists(os.path.join(self.program_folder, "praat")):
            self.updateStatusFading("Invalid program folder.")
            return False
        if not os.path.exists(self.temporary_folder):
            self.updateStatusFading("Invalid temporary folder.")
            return False
        if not self.praatRunScript("praat_test.praat", []):
            self.updateStatusFading("Praat unavailable (try changing the preferences).")
            return False
        for i in [0,4]:
            self.filemenu.entryconfig(i, state=NORMAL)
        return True
        
    ##################
    #                #
    #      GUI       #
    #                #
    ##################

        
    def maximise (self):
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        self.master.geometry("%dx%d+%d+%d" % (w * 0.9, h * 0.9, w * 0.05, h * 0.05))

    def createMenu (self):
        # items that should only be active when an FRD file is loaded
        self.filemenu_only_when_loaded = [1,2,5]
        self.filemenu_numbers = [0,1,2,4,5,7,8]
        self.menubar = Menu(self.master)
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Open...", command=self.open)
        self.filemenu.add_command(label="Save", command=self.save, state=DISABLED)
        self.filemenu.add_command(label="Save as...", command=self.saveAs, state=DISABLED)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Import CSV...", command=self.importCSV)
        self.filemenu.add_command(label="Export CSV...", command=self.exportCSV, state=DISABLED)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Preferences...", command=self.configWrapper)
        self.filemenu.add_command(label="Exit", command=self.master.destroy)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.master.config(menu=self.menubar)

    def createCoords (self):
        self.vertical_main_divider = 0.75
        self.horizontal_main_divider = 0.8

    def createFileList (self):
        self.file_list = Listbox(self.outer_frame, selectmode=SINGLE, exportselection=0)
        self.file_list_scrollbar = Scrollbar(self.outer_frame, orient=VERTICAL)
        self.file_list_scrollbar.place(relx=1,rely=0,relheight=0.45,anchor=NE)
        self.master.update()
        self.file_list.place(relx=self.horizontal_main_divider, rely=0, relwidth=1 - self.horizontal_main_divider - (self.file_list_scrollbar.winfo_width() / self.outer_frame.winfo_width()), relheight=0.45, anchor=NW)
        self.master.update()
        file_list_bottom = self.file_list.winfo_height() / self.outer_frame.winfo_height()
        self.file_list_button_box = Frame(self.outer_frame)
        self.file_list_button_box.place(relx=self.horizontal_main_divider, rely=file_list_bottom, relwidth=1 - self.horizontal_main_divider, relheight=0.1, anchor=NW)
        self.discard_button = Button(self.file_list_button_box, text="Discard", command=self.discard)
        self.filter_button = Button(self.file_list_button_box, text="Filter", command=self.filter)
        self.file_list_progress_label = Label(self.file_list_button_box, text="")
        self.discard_button.pack(side=LEFT)
        self.filter_button.pack(side=LEFT)
        self.file_list_progress_label.pack(side=LEFT)
        self.file_list.bind("<<ListboxSelect>>", self.chooseFile)
        self.file_list.bind("<Button-1>", self.fileListButtonDown)
        self.file_list.bind("<Up>", self.fileListUp)
        self.file_list.bind("<Down>", self.fileListDown)
        self.file_list.bind("a", self.playWhole)
        self.file_list.bind("i", self.playSelection)
        self.file_list.config(yscrollcommand=self.file_list_scrollbar.set)
        self.file_list_scrollbar.config(command=self.file_list.yview)

    def createMetadataViewer (self):
        self.master.update()
        file_list_button_box_bottom = (self.file_list_button_box.winfo_y() + self.file_list_button_box.winfo_height()) / self.outer_frame.winfo_height()
        self.metadata_viewer_box = Frame(self.outer_frame)
        self.metadata_viewer_box.place(relx=1, rely=file_list_button_box_bottom, relheight=1-file_list_button_box_bottom, relwidth=1-self.horizontal_main_divider, anchor=NE)
        self.metadata_viewer = Listbox(self.metadata_viewer_box, state=DISABLED, selectmode=SINGLE, exportselection=0)
        self.metadata_viewer_scrollbar = Scrollbar(self.metadata_viewer_box, orient=VERTICAL)
        self.metadata_viewer_add_button = Button(self.metadata_viewer_box, text="Add", command=self.addMetadataField)
        self.metadata_viewer_remove_button = Button(self.metadata_viewer_box, text="Remove", command=self.removeMetadataField)
        self.metadata_viewer_up_button = Button(self.metadata_viewer_box, text=u"\u2191", command=self.upMetadataField)
        self.metadata_viewer_down_button = Button(self.metadata_viewer_box, text=u"\u2193", command=self.downMetadataField)
        self.metadata_viewer_add_button.place(relx=0,rely=1,anchor=SW)
        self.master.update()
        self.metadata_viewer_remove_button.place(relx=self.metadata_viewer_add_button.winfo_width()/self.metadata_viewer_box.winfo_width(),rely=1,anchor=SW)
        self.master.update()
        self.metadata_viewer_up_button.place(relx=(self.metadata_viewer_add_button.winfo_width()+self.metadata_viewer_remove_button.winfo_width())/self.metadata_viewer_box.winfo_width(),rely=1,anchor=SW)
        self.master.update()
        self.metadata_viewer_down_button.place(relx=(self.metadata_viewer_add_button.winfo_width()+self.metadata_viewer_remove_button.winfo_width()+self.metadata_viewer_up_button.winfo_width())/self.metadata_viewer_box.winfo_width(),rely=1,anchor=SW)
        self.metadata_viewer_scrollbar.place(relx=1,rely=0,relheight=1-(self.metadata_viewer_add_button.winfo_height()/self.metadata_viewer_box.winfo_height()),anchor=NE)
        self.master.update()
        self.metadata_viewer.place(relx=0, rely=0, relwidth=1 - (self.metadata_viewer_scrollbar.winfo_width() / self.metadata_viewer_box.winfo_width()),relheight=1-(self.metadata_viewer_add_button.winfo_height()/self.metadata_viewer_box.winfo_height()),anchor=NW)
        self.metadata_viewer.config(yscrollcommand=self.metadata_viewer_scrollbar.set)
        self.metadata_viewer_scrollbar.config(command=self.metadata_viewer.yview)
        # binding for double click
        self.metadata_viewer.bind("<Double-Button-1>", self.doubleClickMetadataViewer)
        

    def createImage (self):
        self.image_frame = Frame(self.outer_frame)
        self.image_frame.place(relx=0, rely=0, relwidth=self.horizontal_main_divider - 0.025,
                               relheight=self.vertical_main_divider)
        self.waveform = Canvas(self.image_frame)
        self.spectrogram = Canvas(self.image_frame)
        self.status_bar = Label(self.image_frame, anchor=W)
        self.status_bar.place(relx=0, rely=1, relwidth=1, anchor=SW)
        self.master.update()
        top_of_horizontal_scroll = 1 - (self.status_bar.winfo_height() / self.image_frame.winfo_height())
        bottom_of_waveform = top_of_horizontal_scroll * (1/3)
        self.waveform.place(relx=0,rely=0,relwidth=1,relheight=bottom_of_waveform)
        self.spectrogram.place(relx=0,rely=bottom_of_waveform,relwidth=1,relheight=top_of_horizontal_scroll - bottom_of_waveform)

        # binding for jump from file list
    
        self.file_list.bind("<Tab>", self.moveFocusToSpectrogram)

        # create bindings for drag & drop, selection, draw
        
        self.spectrogram.bind("<Key>", self.keyDown)
        #self.spectrogram.bind("<KeyRelease>", self.keyUp)
        self.spectrogram.bind("<B1-Motion>", self.spectrogramButtonMotion)
        self.spectrogram.bind("<ButtonRelease-1>", self.spectrogramButtonUp)
        self.spectrogram.tag_bind("boundary", "<ButtonPress-1>", self.boundaryDown)
        self.spectrogram.tag_bind("boundary", "<ButtonRelease-1>", self.boundaryUp)
        self.spectrogram.tag_bind("boundary", "<B1-Motion>", self.boundaryMotion)
        self.spectrogram.tag_bind("boundary", "<Shift-ButtonPress-1>", self.Pass)
        self.spectrogram.tag_bind("boundary", "<Shift-ButtonRelease-1>", self.Pass)
        self.spectrogram.tag_bind("boundary", "<Shift-B1-Motion>", self.Pass)
        self.spectrogram.tag_bind("formant", "<ButtonPress-1>", self.formantDown)
        self.spectrogram.tag_bind("formant", "<Shift-ButtonPress-1>", self.shiftFormantDown)
        self.spectrogram.tag_bind("formant", "<ButtonRelease-1>", self.formantUp)
        self.spectrogram.tag_bind("formant", "<Shift-ButtonRelease-1>", self.shiftFormantUp)
        self.spectrogram.tag_bind("formant", "<B1-Motion>", self.formantMotion)
        self.spectrogram.tag_bind("formant", "<Shift-B1-Motion>", self.Pass)
        self.spectrogram.tag_bind("formant_label", "<ButtonPress-1>", self.formantDown)
        self.spectrogram.tag_bind("formant_label", "<Shift-ButtonPress-1>", self.shiftFormantDown)
        self.spectrogram.tag_bind("formant_label", "<ButtonRelease-1>", self.formantUp)
        self.spectrogram.tag_bind("formant_label", "<Shift-ButtonRelease-1>", self.shiftFormantUp)
        self.spectrogram.tag_bind("formant_label", "<B1-Motion>", self.formantMotion)
        self.spectrogram.tag_bind("formant_label", "<Shift-B1-Motion>", self.Pass)
        self.spectrogram.bind("<Shift-ButtonPress-1>", self.selectOn)
        self.spectrogram.bind("<Shift-B1-Motion>", self.selectMotion)
        self.spectrogram.bind("<Shift-ButtonRelease-1>", self.selectOff)
        

        # create bindings for zoom & move

        self.spectrogram.bind("h", self.hide)
        self.spectrogram.bind("x", self.hideThirdFormant)
        self.spectrogram.bind("t", self.tag)
        self.spectrogram.bind("<Up>", self.xZoomIn)
        self.spectrogram.bind("<Down>", self.xZoomOut)
        self.spectrogram.bind("n", self.xZoomToSelection)
        self.spectrogram.bind("r", self.refreshMeasurements)
        self.spectrogram.bind("<Left>", self.xScrollLeft)
        self.spectrogram.bind("<Right>", self.xScrollRight)
        self.spectrogram.bind("<Button-1>", self.spectrogramButtonDown)

        # create bindings for brightness

        self.spectrogram.bind("b", self.brightenSpectrogram)
        self.spectrogram.bind("d", self.darkenSpectrogram)

        # create bindings for playback

        self.spectrogram.bind("a", self.playWhole)
        self.spectrogram.bind("<Tab>", self.playCursor)
        self.spectrogram.bind("i", self.playSelection)

        # create bindings for status bar

        self.spectrogram.bind("<Motion>", self.displayLocation)


    def moveFocusToSpectrogram (self, event=None):
        self.spectrogram.focus_set()
        return "break"

    def createFormantBox (self):
        self.formant_box_outer = Frame(self.outer_frame, relief=RIDGE, borderwidth=2)
        
        self.formant_box_outer.place(relx=0, rely=self.vertical_main_divider + (0.01), relwidth=self.horizontal_main_divider * 0.7, relheight=1-self.vertical_main_divider - 0.01)
        self.formant_box = Frame(self.formant_box_outer)
        self.formant_box.place(relx = 0.5, rely=0.5, anchor="c")
        self.label_formant_max_freq = Label(self.formant_box, text="Max. formant (Hz)")
        self.entry_formant_max_freq = Entry(self.formant_box, width=8)
        self.entry_formant_max_freq.insert(0, self.formant_max_freq)
        self.entry_formant_max_freq.bind("<Return>", self.entryMaxFreqSet)
        self.entry_formant_max_freq.bind("<FocusOut>", self.entryMaxFreqSet)
        
        self.label_formant_number_of_formants = Label(self.formant_box, text="No. of expected formants")
        self.entry_formant_number_of_formants = Entry(self.formant_box, width=8)
        self.entry_formant_number_of_formants.insert(0, self.formant_number_of_formants)
        self.entry_formant_number_of_formants.bind("<Return>", self.entryFormantExpNoSet)
        self.entry_formant_number_of_formants.bind("<FocusOut>", self.entryFormantExpNoSet)
        
        self.label_formant_window_length = Label(self.formant_box, text="Window length (s)")
        self.entry_formant_window_length = Entry(self.formant_box, width=8)
        self.entry_formant_window_length.insert(0, self.formant_window_length)
        self.entry_formant_window_length.bind("<Return>", self.entryWindowLengthSet)
        self.entry_formant_window_length.bind("<FocusOut>", self.entryWindowLengthSet)
        
        self.label_formant_pre_emph = Label(self.formant_box, text="Pre-emphasis from (Hz)")
        self.entry_formant_pre_emph = Entry(self.formant_box, width=8)
        self.entry_formant_pre_emph.insert(0, self.formant_pre_emph)
        self.entry_formant_pre_emph.bind("<Return>", self.entryPreEmphSet)
        self.entry_formant_pre_emph.bind("<FocusOut>", self.entryPreEmphSet)
        
        self.label_formant_use_number = Label(self.formant_box, text="No. of measured formants")
        self.entry_formant_use_number = Entry(self.formant_box, width=4)
        self.entry_formant_use_number.insert(0, self.formant_use_number)
        self.entry_formant_use_number.bind("<Return>", self.entryFormantUseNoSet)
        self.entry_formant_use_number.bind("<FocusOut>", self.entryFormantUseNoSet)
        self.label_available_formants = Label(self.formant_box, text="/ " + str(self.available_formants))

        self.label_spectrogram_max_freq = Label(self.formant_box, text="Max. frequency (Hz)")
        self.entry_spectrogram_max_freq = Entry(self.formant_box, width=8)
        self.entry_spectrogram_max_freq.insert(0, self.spectrogram_max_freq)
        self.entry_spectrogram_max_freq.bind("<Return>", self.entrySpecMaxFreqSet)
        self.entry_spectrogram_max_freq.bind("<FocusOut>", self.entrySpecMaxFreqSet)
                
        self.label_spectrogram_window_length = Label(self.formant_box, text="Window length (s)")
        self.entry_spectrogram_window_length = Entry(self.formant_box, width=8)
        self.entry_spectrogram_window_length.insert(0, self.spectrogram_window_length)
        self.entry_spectrogram_window_length.bind("<Return>", self.entrySpecWindowLengthSet)
        self.entry_spectrogram_window_length.bind("<FocusOut>", self.entrySpecWindowLengthSet)
                
        self.label_spectrogram_brightness = Label(self.formant_box, text="Brightness")
        self.entry_spectrogram_brightness = Entry(self.formant_box, width=8)
        self.entry_spectrogram_brightness.insert(0, self.spectrogram_brightness)
        self.entry_spectrogram_brightness.bind("<Return>", self.entrySpecBrightnessSet)
        self.entry_spectrogram_brightness.bind("<FocusOut>", self.entrySpecBrightnessSet)

        self.check_formant_fixed_on = IntVar()
        self.check_formant_fixed = Checkbutton(self.formant_box, text="Keep constant", variable=self.check_formant_fixed_on, command=self.checkFormantFixedMessage)

        self.check_display_fixed_on = IntVar()
        self.check_display_fixed = Checkbutton(self.formant_box, text="Keep constant", variable=self.check_display_fixed_on, command=self.checkDisplayFixedMessage)

        self.label_formant = Label(self.formant_box, text="Formant measurements:")
        self.label_spectrogram = Label(self.formant_box, text="Display settings:")
        self.label_formant.grid(row=0,column=0, columnspan=2)
        self.label_formant_max_freq.grid(row=1, column=0, sticky=E)
        self.entry_formant_max_freq.grid(row=1, column=1, padx=20)
        self.label_formant_number_of_formants.grid(row=2, column=0, sticky=E)
        self.entry_formant_number_of_formants.grid(row=2, column=1, padx=20)
        self.label_formant_window_length.grid(row=3, column=0, sticky=E)
        self.entry_formant_window_length.grid(row=3, column=1, padx=20)
        self.label_formant_pre_emph.grid(row=4, column=0, sticky=E)
        self.entry_formant_pre_emph.grid(row=4, column=1, padx=20)
        self.check_formant_fixed.grid(row=5, column=0, sticky=E)
        

        self.label_spectrogram.grid(row=0,column=2, columnspan=3)
        self.label_spectrogram_max_freq.grid(row=1, column=2, sticky=E, padx=20)
        self.entry_spectrogram_max_freq.grid(row=1, column=3, columnspan=2)
        self.label_spectrogram_window_length.grid(row=2, column=2, sticky=E, padx=20)
        self.entry_spectrogram_window_length.grid(row=2, column=3, columnspan=2)
        self.label_spectrogram_brightness.grid(row=3, column=2, sticky=E, padx=20)
        self.entry_spectrogram_brightness.grid(row=3, column=3, columnspan=2)
        self.label_formant_use_number.grid(row=4, column=2, sticky=E, padx=20)
        self.entry_formant_use_number.grid(row=4, column=3)
        self.label_available_formants.grid(row=4, column=4)
        self.check_display_fixed.grid(row=5, column=2, sticky=E, padx=20)


    def createButtonBox (self):
        self.button_box_outer = Frame(self.outer_frame)
        self.button_box_outer.place(relx=self.horizontal_main_divider * 0.71, rely=self.vertical_main_divider + 0.01, relwidth=self.horizontal_main_divider * 0.28, relheight=1-self.vertical_main_divider - 0.01)
        self.button_box = Frame(self.button_box_outer)
        self.button_box.place(anchor='c', relx=0.5, rely=0.5)
        self.tag_label = Label(self.button_box, text="Tags:")
        self.tags_outer = Frame(self.button_box)
        self.tag_button_1 = Button(self.tags_outer, text="1", command=lambda: self.tag(1))
        self.tag_button_2 = Button(self.tags_outer, text="2", command=lambda: self.tag(2))
        self.tag_button_3 = Button(self.tags_outer, text="3", command=lambda: self.tag(3))
        self.zoom_in_button = Button(self.button_box, text=u"+ (\u2191)", command=self.xZoomIn)
        self.zoom_out_button = Button(self.button_box, text=u"- (\u2193)", command=self.xZoomOut)
        self.zoom_selection_button = Button(self.button_box, text="sel (n)", command=self.xZoomToSelection)
        self.refresh_formant_button = Button(self.button_box, text="Refresh Formants (r)", command=self.refreshMeasurements)
        self.play_label = Label(self.button_box, text="Play...")
        self.play_whole_button = Button(self.button_box, text="all (a)", command=self.playWhole)
        self.play_view_button = Button(self.button_box, text="cur (tab)", command=self.playCursor)
        self.play_selection_button = Button(self.button_box, text="int (i)", command=self.playSelection)
        self.tag_label.grid(row=0,column=0)
        self.tags_outer.grid(row=0,column=1,columnspan=2)
        self.tag_button_1.grid(row=0,column=0)
        self.tag_button_2.grid(row=0,column=1)
        self.tag_button_3.grid(row=0,column=2)
        self.zoom_in_button.grid(row=1,column=0,sticky=E)
        self.zoom_out_button.grid(row=1,column=1)
        self.zoom_selection_button.grid(row=1,column=2,sticky=W)
        self.refresh_formant_button.grid(row=2,column=0,columnspan=3)
        self.play_label.grid(row=3, column=0, columnspan=3)
        self.play_whole_button.grid(row=4,column=0)
        self.play_view_button.grid(row=4,column=1)
        self.play_selection_button.grid(row=4,column=2)

    def entryMaxFreqSet (self, event=None):
        try:
            v = int(self.entry_formant_max_freq.get())
            if v != self.formant_max_freq:
                self.formant_max_freq = int(self.entry_formant_max_freq.get())
                self.updateStatusFading("Maximum frequency for formant estimation set to " + str(self.formant_max_freq) + ".")
                self.refreshMeasurements()
                if event.char != "??":
                    self.moveFocusToSpectrogram()
        except:
            self.entry_formant_max_freq.delete(0, END)
            self.entry_formant_max_freq.insert(0, self.formant_max_freq)
            self.moveFocusToSpectrogram()

    def entrySpecMaxFreqSet (self, event=None):
        try:
            v = int(self.entry_spectrogram_max_freq.get())
            if v > self.current_sample_rate / 2:
                v = int(self.current_sample_rate / 2)
            if v != self.spectrogram_max_freq:
                self.spectrogram_max_freq = v
                self.updateStatusFading("Maximum frequency for spectrogram set to " + str(self.spectrogram_max_freq) + ".")
                self.yzoom_end = self.spectrogram_max_freq
                self.displaySpectrogram()
            self.entry_spectrogram_max_freq.delete(0, END)
            self.entry_spectrogram_max_freq.insert(0, self.spectrogram_max_freq)
            if event.char != "??":
                self.moveFocusToSpectrogram()
        except:
            self.entry_spectrogram_max_freq.delete(0, END)
            self.entry_spectrogram_max_freq.insert(0, self.spectrogram_max_freq)


    def entryFormantExpNoSet (self, event=None):
        try:
            v = float(self.entry_formant_number_of_formants.get())
            v = ((v + 0.25) // 0.5) * 0.5
            if v != self.formant_number_of_formants:
                self.formant_number_of_formants = v
                self.updateStatusFading("Expected number of formants (i.e. LPC order * 0.5) set to " + str(self.formant_number_of_formants) + ".")
                self.refreshMeasurements()
            self.entry_formant_number_of_formants.delete(0, END)
            self.entry_formant_number_of_formants.insert(0, self.formant_number_of_formants)
            if event.char != "??":
                self.moveFocusToSpectrogram()
        except:
            self.entry_formant_number_of_formants.delete(0, END)
            self.entry_formant_number_of_formants.insert(0, self.formant_number_of_formants)

    def entryWindowLengthSet (self, event=None):
        try:
            v = float(self.entry_formant_window_length.get())
            if v != self.formant_window_length:
                self.formant_window_length = v
                self.updateStatusFading("Window length for formant estimation set to " + str(self.formant_window_length) + ".")
                self.refreshMeasurements()
                if event.char != "??":
                    self.moveFocusToSpectrogram()
        except:
            self.entry_formant_window_length.delete(0, END)
            self.entry_formant_window_length.insert(0, self.formant_window_length)

    def entrySpecWindowLengthSet (self, event=None):
        try:
            v = float(self.entry_spectrogram_window_length.get())
            if v!= self.spectrogram_window_length:
                self.spectrogram_window_length = v
                self.updateStatusFading("Window length for spectrogram set to " + str(self.spectrogram_window_length) + ".")
                self.displaySpectrogram()
                if event.char != "??":
                    self.moveFocusToSpectrogram()
        except:
            self.entry_spectrogram_window_length.delete(0, END)
            self.entry_spectrogram_window_length.insert(0, self.spectrogram_window_length)

    def entryPreEmphSet (self, event=None):
        try:
            v = int(self.entry_formant_pre_emph.get())
            if v != self.formant_pre_emph:
                self.formant_pre_emph = v
                self.updateStatusFading("Pre-emphasis for formant estimation set to " + str(self.formant_pre_emph) + ".")
                self.refreshMeasurements()
                if event.char != "??":
                    self.moveFocusToSpectrogram()
        except:
            self.entry_formant_pre_emph.delete(0, END)
            self.entry_formant_pre_emph.insert(0, self.formant_pre_emph)

    def entryFormantUseNoSet (self, event=None):
        try:
            v = int(self.entry_formant_use_number.get())
            if v != self.formant_use_number:
                self.formant_use_number = v
                self.updateStatusFading("Number of formants set to " + str(self.formant_use_number) + ".")
                self.displaySpectrogram()
                if event.char != "??":
                    self.moveFocusToSpectrogram()
                self.clearSelection()
        except:
            self.entry_formant_use_number.delete(0, END)
            self.entry_formant_use_number.insert(0, self.formant_use_number)

    def entrySpecBrightnessSet (self, event=None):
        try:
            b = float(self.entry_spectrogram_brightness.get())
            if b < -100:
                b = -100
                self.entry_spectrogram_brightness.delete(0, END)
                self.entry_spectrogram_brightness.insert(0, b)
            elif b > 100:
                b = 100
                self.entry_spectrogram_brightness.delete(0, END)
                self.entry_spectrogram_brightness.insert(0, b)
            if b != self.spectrogram_brightness:
                self.spectrogram_brightness = b
                self.updateStatusFading("Spectrogram brightness set to " + str(self.spectrogram_brightness) + ".")
                self.displaySpectrogram()
                if event.char != "??":
                    self.moveFocusToSpectrogram()
        except:
            self.entry_spectrogram_brightness.delete(0, END)
            self.entry_spectrogram_brightness.insert(0, self.spectrogram_brightness)

    def refreshSettings (self):
        index = self.db.wav_dic[self.current_wav]
        for parameter in self.analysis_parameter_list:
            if not (parameter in self.formant_parameters and self.check_formant_fixed_on.get()) and not (parameter in self.display_parameters and self.check_display_fixed_on.get()):
                vars(self)[parameter] = self.db.settings_table[index][self.db.settings_header[parameter]]
                vars(self)["entry_" + parameter].delete(0, END)
                vars(self)["entry_" + parameter].insert(0, vars(self)[parameter])

    def checkDisplayFixedMessage (self):
        if self.check_display_fixed_on.get():
            self.updateStatusFading("Same display settings used for opened items. Previous settings overridden.")
        else:
            self.updateStatusFading("Saved display settings are used.")

    def checkFormantFixedMessage (self):
        if self.check_formant_fixed_on.get():
            self.updateStatusFading("Same formant settings used for opened items. WARNING: This overrides saved formant values.")
        else:
            self.updateStatusFading("Saved formant settings are used. No automatic formant reestimation.")

    def resizeImages (self, event):
        """
        Automatically resize images when window size changes
        """
        self.displayWaveform()
        self.displaySpectrogram()
        
    ##################
    #                #
    # FILE HANDLING  #
    #                #
    ##################

    def prepTempDir (self):
        if not os.path.exists(self.temporary_folder):
            try:
                os.makedirs(self.temporary_folder)
            except:
                raise ValueError("Could not create temporary dictionary. Try changing the path.")

    def createSettings (self):
        settings_header = dict([(self.analysis_parameter_list[i], i) for i in range(len(self.analysis_parameter_list))])
        settings = [vars(self)[parameter] for parameter in self.analysis_parameter_list]
        return(settings_header, settings)

    def importCSV (self):
        if self.importCSVDialogues():
            try:
                self.frd = ""
                csv = readCSV(self.current_csv)
                settings_header, settings = self.createSettings()
                settings_table = [list(settings) for x in range(len(csv[1]))]
                self.db = Database(self.current_wav_column, self.current_master_folder, csv, (settings_header, settings_table), self.current_files)
                self.db.measurements = self.createMeasurements()
                self.onNewCurrent()
                self.updateStatusFading(os.path.split(self.current_csv)[1] + " successfully imported.")
            except:
                self.frd = ""
                self.db = None
                self.updateStatusFading("Import CSV failed.")

    def exportCSV (self):
        self.chooseFile()
        if self.file_list.size() < 1:
            self.updateStatusFading("Nothing to export.")
            return False
        export_path = tkFileDialog.asksaveasfilename(title="Export CSV file...")
        if not export_path:
            self.updateStatusFading("Export CSV aborted.")
            return False
        formant_export_no = selectFormantNo(self.master, "Number of formants to write out").no
        if self.export_format == "measurements":
            try:
                table = []
                tags_exist = False
                for wav in self.db.wav_list:
                    index = self.db.wav_dic[wav]
                    start = self.db.measurements[index][0][1]
                    end = self.db.measurements[index][0][2]
                    metadata = self.db.metadata_table[index] + [end - start]
                    max_formant = self.db.settings_table[index][self.db.settings_header["formant_use_number"]]
                    for m in range(len(self.db.measurements[index][1][0])):
                        formants = []
                        tags = []
                        for t in range(formant_export_no):
                            if t > len(self.db.measurements[index][1]) - 1:
                                formants.append(None)
                            elif len(self.db.measurements[index][1][t]) < len(self.db.measurements[index][1][0]):
                                formants.append(None)
                            elif t >= max_formant:
                                formants.append(None)
                            else:
                                formants.append(self.db.measurements[index][1][t][m])
                            if (t,m) in self.db.measurements[index][-1]:
                                tags_exist = True
                                tags.append("".join(sorted([str(x) for x in self.db.measurements[index][-1][(t,m)]])))
                            else:
                                tags.append("")
                        table.append(metadata + [m] + formants + tags)
                header = map(itemgetter(0), sorted(self.db.metadata_header.items(), key=itemgetter(1))) + ['duration', 'measurement_no'] + ['f' + str(n) for n in range(1, formant_export_no + 1)]
                if not tags_exist:
                    table = [x[:-formant_export_no] for x in table]
                else:
                    header += ['f' + str(n) + ".tag" for n in range(1, formant_export_no + 1)]
                writeCSV(export_path, header, table)
                self.updateStatusFading("File exported as " + export_path + ".")
            except:
                self.updateStatusFading("Export CSV failed.")
        elif self.export_format == "slices":
            pass
        
            
    def importCSVDialogues (self):
        self.current_csv = tkFileDialog.askopenfilename(title="Import CSV file...")
        if not self.current_csv:
            return False
        self.current_wav_column, self.formant_number_of_measurements = selectColumn(self.master, "Import settings").output
        if not self.current_wav_column:
            return False
        self.current_master_folder = os.path.dirname(self.current_csv)
        self.getFileList()
        return True

    def getFileList (self):
        self.current_files = {}
        for dirpath, dirs, files in os.walk(self.current_master_folder):
            for f in files:
                self.current_files[f.lower()] = os.path.join(dirpath, f)


    def openWav (self, wav):

        #try:
            self.spectrogram_initialised = True
            self.clearSelectionList()

            self.current_wav = wav
            self.db.current_wav = wav
            self.current_path = self.current_files[wav]
            index = self.db.wav_dic[wav]
            self.sound.read(self.current_path)
            self.current_sample_rate = self.sound["frequency"]


            self.refreshSettings()

            self.boundaryMeasurementsToBoundaries(*self.db.measurements[index][0])
            self.xzoom_start = 0
            self.xzoom_end = self.current_dur
            self.yzoom_start = 0
            self.yzoom_end = self.spectrogram_max_freq
            self.play_cursor_x = 0
            self.play_selection_start_x = -1
            self.play_selection_end_x = -1
            self.redraw = 0

            self.formantListToTrajectory(self.db.measurements[index][1], self.db.measurements[index][-1])
            self.createPlayCursor()
            self.createPlaySel()

            self.displayWaveform()
            if self.check_formant_fixed_on.get():
                self.refreshMeasurements()
            else:
                self.displaySpectrogram()
            self.exitDrawMode()
            self.image_frame.bind('<Configure>', self.resizeImages)
            self.displayMetadata()
            self.updateStatusFading("Opened " + self.current_wav + " with a sampling rate of " + str(self.current_sample_rate) + ".")
       # except:
       #     self.onNewCurrent(failed_to_open_wav=True)
       #     self.updateStatusFading("WAV file could not be opened. Perhaps does not exist anymore?")
        

    def chooseFile (self, event=None):
        if int(self.file_list.size()) > 0 and len(self.file_list.curselection()) > 0:
            wav = self.file_list.get(self.file_list.curselection())
            if self.spectrogram_initialised:
                self.db.measurements[self.db.wav_dic[self.current_wav]] = [[self.current_dur, self.boundaries[self.left_boundary].ms, self.boundaries[self.right_boundary].ms], self.trajectoryToFormantList(), self.writeTags()]
                for parameter in self.analysis_parameter_list:
                    self.db.settings_table[self.db.wav_dic[self.current_wav]][self.db.settings_header[parameter]] = vars(self)[parameter]
            if wav != self.current_wav:
                self.openWav(wav)
            self.updateProgressLabel()

    def open (self):
        frds = tkFileDialog.askopenfilename(title="Open single/multiple FRD file(s)...", multiple=True)
        if self.platform == 'Windows' and self.os_release=="7": #and 'PROGRAMFILES(X86)' not in os.environ:
            if "{" in frds:
                frds = re.findall("{(.*?)}", frds)
            else:
                frds = frds.split(" ")
        settings_header_message = ""
        try:
            if frds != [""] and frds != "": # works on windows - mac os x?
                self.current_master_folder = os.path.dirname(frds[0])
                self.getFileList()
                for frd_ind in range(len(frds)):
                    frd = frds[frd_ind]
                    print(frd)
                    try:
                        f = codecs.open(frd, 'rb')
                        self.db_temp = pickle.load(f)
                        f.close()
                        settings_header_message = self.db_temp.checkSettingsHeader(*self.createSettings())
                    except:
                        self.updateStatusFading("Could not open " + os.path.split(frd)[1] + ".")
                        raise ValueError ("Could not open " + os.path.split(frd)[1] + ".")
                    if frd_ind == 0:
                        self.db = self.db_temp
                        self.formant_number_of_measurements = len(self.db.measurements[0][1][0])
                    else:
                        try:
                            self.db.join(self.db_temp)
                        except:
                            self.updateStatusFading("Could not add " + os.path.split(frd)[1] + ". Check metadata!")
                            raise ValueError ("Could not add " + os.path.split(frd)[1] + ". Check metadata!")
                if len(frds) == 1:
                    self.frd = frd
                else:
                    self.frd = ""
                self.filter_expression = ""
                self.onNewCurrent()
                self.updateStatusFading("File opened." + settings_header_message)
        except:
            pass
            

    def onNewCurrent (self, failed_to_open_wav=False):
        """
        This method has two main purposes:
        1) cleaning the current GUI when a new FRD is loaded,
           and initialising a fresh GUI
        2) cleaning the current GUI when there are no files
           left in the @file_list
        """
        self.spectrogram_initialised = False
        self.current_wav = None
        if len(self.db.wav_list) < 1:
            self.db.current_wav = None
        else:
            if self.frd:
                self.master.wm_title("Formant Editor - " + os.path.splitext(os.path.split(self.frd)[1])[0])
            elif self.current_csv:
                self.master.wm_title("Formant Editor - " + os.path.splitext(os.path.split(self.current_csv)[1])[0])
            else:
                self.master.wm_title("Formant Editor - Joined FRD files")
        # compatibility:
        if "current_wav" not in vars(self.db):
            self.db.current_wav = None
        self.current_path = None
        self.xzoom_start = None
        self.yzoom_start = None
        self.xzoom_end = None
        self.yzoom_end = None
        self.boundaries = None
        self.trajectories_list = None
        self.trajectories_dic = None
        self.current_dur = None
        self.play_cursor_x = None
        self.play_selection_start_x = -1
        self.play_selection_end_x = -1
        self.spectrogram.delete(ALL)
        self.waveform.delete(ALL)
        self.file_list.delete(0, END)
        self.emptyMetadataViewer()
        self.exitDrawMode()
        self.file_list_progress_label["text"] = ""
        self.populateFileList()
        for i in self.filemenu_only_when_loaded:
            if self.file_list.size() > 0:
                self.filemenu.entryconfig(i, state=NORMAL)
            else:
                self.filemenu.entryconfig(i, state=DISABLED)
        # opening the sound file that was last edited
        if not failed_to_open_wav:
            if self.db.current_wav:
                self.file_list.selection_set(self.db.wav_dic[self.db.current_wav])
                self.file_list.see(self.db.wav_dic[self.db.current_wav])
                self.chooseFile()

    def save (self):
        if not self.frd:
            self.saveAs()
        else:
            self.chooseFile()
            f = codecs.open(self.frd, 'wb')
            pickle.dump(self.db, f)
            f.close()
            self.updateStatusFading("File saved.")

    def saveAs (self):
        self.chooseFile()
        self.frd = tkFileDialog.asksaveasfilename(title="Save FRD file...")
        if self.frd:
            f = codecs.open(self.frd, 'wb')
            pickle.dump(self.db, f)
            f.close()
            self.master.wm_title("Formant Editor - " + os.path.splitext(os.path.split(self.frd)[1])[0])
            self.updateStatusFading("File saved as " + self.frd + ".")

    ##################
    #                #
    #   FILE LIST    #
    #                #
    ##################

    def populateFileList (self):
        if self.filter_expression == "":
            for wav in self.db.wav_list:
                self.file_list.insert(END, wav)
        else:
            try:
                filter_tree = ast.parse(self.filter_expression, mode="eval")
                filter_tree = RewriteName().visit(filter_tree)
                for wav in self.db.wav_list:
                    index = self.db.wav_dic[wav]
                    if eval(compile(filter_tree, "<ast>", mode="eval")):
                        self.file_list.insert(END, wav)
            except:
                self.updateStatusFading("Could not apply filter to the current project. Check filter syntax!")
                self.file_list.delete(0, END)
                for wav in self.db.wav_list:
                    self.file_list.insert(END, wav)

            
    def updateProgressLabel (self):
        try:
            self.file_list_progress_label["text"] = "   " + str(int(self.file_list.curselection()[0]) + 1) + " / " + str(self.file_list.size())
        except:
            pass


    def fileListButtonDown (self, event):
        if self.file_list.cget("state") != DISABLED:
            self.file_list.focus_set()

    def fileListDown (self, event=None):
        i = self.file_list.curselection()
        if len(i) == 1:
            index = int(i[0])
            if index < (int(self.file_list.size()) - 1):
                self.file_list.selection_clear(index)
                self.file_list.selection_set(index + 1)
                self.file_list.see(index + 1)
                self.chooseFile()

    def fileListUp (self, event=None):
        i = self.file_list.curselection()
        if len(i) == 1:
            index = int(i[0])
            if index > 0:
                self.file_list.selection_clear(index)
                self.file_list.selection_set(index - 1)
                self.file_list.see(index - 1)
                self.chooseFile()

    def discard (self):
        if int(self.file_list.size()) > 0:
            wav = self.file_list.get(self.file_list.curselection())
            index = self.db.wav_dic[wav]
            file_list_index = self.file_list.curselection()
            if int(file_list_index[0]) < (int(self.file_list.size()) - 1):
                self.fileListDown()
            elif int(self.file_list.size()) > 1:
                self.fileListUp()
            self.file_list.delete(file_list_index)
            self.db.metadata_table.pop(index)
            self.db.settings_table.pop(index)
            self.db.measurements.pop(index)
            self.db.wav_list.pop(index)
            self.db.refreshWavDic()
            if int(self.file_list.size()) < 1:
                self.onNewCurrent()
            else:
                self.updateProgressLabel()
                
    def filter (self):
        self.filter_expression = selectFilterExpression(self.master, "Filter expression", parameters=self.filter_expression).output
        self.onNewCurrent()
        

    ##################
    #                #
    #     PRAAT      #
    #                #
    ##################

    def praatRunScript (self, script_name, options):
        output_path = self.temporary_folder + os.sep + "praat.tmp"
        script_path = self.program_folder + os.sep + "praat" + os.sep + script_name
        if self.platform == 'Windows':
            cmd_list = [self.praat_path, "-a", script_path] + options
            cmd = ' '.join(['"' + str(item) + '"' for item in cmd_list]) + ">" + '"' + output_path + '"'
        else:
            cmd_list = [self.praat_path, script_path] + options
            cmd = ' '.join([str(item).replace(' ', r'\ ') for item in cmd_list + [">",  output_path]])
        subprocess.call(cmd, shell=True)
        if os.path.exists(output_path):
            f = codecs.open(output_path, 'r')
            text = f.read()
            f.close()
            os.remove(output_path)
            return text
        else:
            return ''

    ##################
    #                #
    #    METADATA    #
    #                #
    ##################

    def emptyMetadataViewer (self):
        self.metadata_viewer.config(state=NORMAL)
        self.metadata_viewer.delete(0, END)
        self.metadata_viewer.config(state=DISABLED)

    def displayMetadata (self):
        self.metadata_viewer.config(state=NORMAL)
        yview = self.metadata_viewer.yview()
        self.metadata_viewer.delete(0, END)
        for attr in map(itemgetter(0), sorted(self.db.metadata_header.items(), key=itemgetter(1))):
            index = self.db.wav_dic[self.current_wav]
            line = attr + ": " + str(self.db.metadata_table[index][self.db.metadata_header[attr]])
            self.metadata_viewer.insert(END, line)
        if self.metadata_viewer.size():
            self.metadata_viewer.yview('moveto', yview[0])
            
    def addMetadataField (self):
        attr_name, default_value = selectAttrName(self.master, "Attribute name").output
        if attr_name:
            if len(self.metadata_viewer.curselection()) > 0:
                sel_attr_name = self.metadata_viewer.get(self.metadata_viewer.curselection()).split(':')[0]
            else:
                sel_attr_name = self.metadata_viewer.get(0).split(':')[0]
            self.db.addAttribute(attr_name, sel_attr_name, default_value=default_value)
            self.updateStatusFading("New metadata attribute added.")
            self.displayMetadata()
            
    def removeMetadataField (self):
        if int(self.metadata_viewer.size()) > 0 and len(self.metadata_viewer.curselection()) > 0:
            attr_name = self.metadata_viewer.get(self.metadata_viewer.curselection()).split(':')[0]
            if attr_name in self.db.metadata_header:
                self.db.removeAttribute(attr_name)
                self.updateStatusFading('Metadata attribute "' + attr_name + '" removed.')
                self.displayMetadata()
    
    def upMetadataField (self):
        if int(self.metadata_viewer.size()) > 0 and len(self.metadata_viewer.curselection()) > 0:
            sel = int(self.metadata_viewer.curselection()[0])
            if sel != 0:
                attr_name = self.metadata_viewer.get(self.metadata_viewer.curselection()).split(':')[0]
                self.db.upAttribute(attr_name)
                self.updateStatusFading('Metadata attribute "' + attr_name + '" moved up.')
                self.displayMetadata()
                self.metadata_viewer.select_set(sel - 1)
                self.metadata_viewer.activate(sel - 1)
    
    def downMetadataField (self):
        if int(self.metadata_viewer.size()) > 0 and len(self.metadata_viewer.curselection()) > 0:
            sel = int(self.metadata_viewer.curselection()[0])
            if sel != (self.metadata_viewer.size() - 1):
                attr_name = self.metadata_viewer.get(self.metadata_viewer.curselection()).split(':')[0]
                self.db.downAttribute(attr_name)
                self.updateStatusFading('Metadata attribute "' + attr_name + '" moved down.')
                self.displayMetadata()
                self.metadata_viewer.select_set(sel + 1)
                self.metadata_viewer.activate(sel + 1)
                
    def doubleClickMetadataViewer (self, event=None):
        if int(self.metadata_viewer.size()) > 0 and len(self.metadata_viewer.curselection()) > 0:
            self.metadata_field_entry = Entry(self.metadata_viewer, borderwidth=0)
            bbox = self.metadata_viewer.bbox(self.metadata_viewer.curselection())
            self.metadata_field_entry.place(x=bbox[0], y=bbox[1]-2, width=self.metadata_viewer.winfo_width()-2, height=bbox[3]+4)
            self.metadata_field_entry.bind("<Return>", self.setMetadataFieldValue)
            self.metadata_field_entry.bind("<FocusOut>", self.setMetadataFieldValue)
            self.metadata_field_entry.insert(0, self.metadata_viewer.get(self.metadata_viewer.curselection()).split(':')[1][1:])
            self.metadata_field_entry_attr_name = self.metadata_viewer.get(self.metadata_viewer.curselection()).split(':')[0]
            self.metadata_field_entry.focus()
            self.file_list.configure(state=DISABLED)
            self.menubar.entryconfig(0, state=DISABLED)
            
    def setMetadataFieldValue (self, event=None):
        new_value = self.metadata_field_entry.get()
        if self.metadata_field_entry_attr_name in self.db.metadata_header:
            self.db.put(self.current_wav, self.metadata_field_entry_attr_name, new_value)
            self.displayMetadata()
        self.metadata_field_entry.destroy()
        self.file_list.configure(state=NORMAL)
        self.menubar.entryconfig(0, state=NORMAL)
        for i in self.filemenu_numbers:
            self.filemenu.entryconfig(i, state=NORMAL) 
        
            


    ##################
    #                #
    #     PLAY       #
    #                #
    ##################

    def play (self, start, end):
        self.movePlayCursor((start, end, time()))
        self.sound.play(start=int(self.current_sample_rate * start), end=int(self.current_sample_rate * end))

    def movePlayCursor (self, (start, end, start_time)):
        new_time = start + (time() - start_time)
        self.placePlayCursor(new_time)
        if new_time < end:
            self.master.after(self.play_cursor_delay, self.movePlayCursor, (start, end, start_time))
        else:
            self.placePlayCursor(self.play_cursor_x)

    def createPlayCursor (self):
        self.spectrogram.delete("play_cursor")
        self.play_cursor = self.spectrogram.create_line(0,0,0,0, fill=self.play_cursor_colour, width=self.play_cursor_width, tags="play_cursor")
        self.play_cursor_text = self.spectrogram.create_text(0,0,text="",tags="play_cursor", anchor=NW,fill=self.play_cursor_colour)

    def createPlaySel (self):
        self.spectrogram.delete("sel_cursor")
        self.play_selection_start = self.spectrogram.create_line(0,0,0,0, fill=self.play_cursor_colour, width=self.play_cursor_width, dash=[10], tags="sel_cursor")
        self.play_selection_end = self.spectrogram.create_line(0,0,0,0, fill=self.play_cursor_colour, width=self.play_cursor_width, dash=[10], tags="sel_cursor")
        self.play_selection_start_text = self.spectrogram.create_text(0,0,text="", tags="sel_cursor",anchor=NW,fill=self.play_cursor_colour)
        self.play_selection_end_text = self.spectrogram.create_text(0,0,text="", tags="sel_cursor",anchor=NE,fill=self.play_cursor_colour)
        self.play_selection_dur_text = self.spectrogram.create_text(0,0,text="", tags="sel_cursor",anchor=N,fill=self.play_cursor_colour)

    def clickPlayCursor (self, event):
        x = self.xzoom_start + ((event.x / self.spectrogram.winfo_width()) * (self.xzoom_end - self.xzoom_start))
        self.play_cursor_x = x
        self.placePlayCursor(x)

    def placePlayCursor (self, x):
        x_pixel = ((x - self.xzoom_start) / (self.xzoom_end - self.xzoom_start)) * self.spectrogram.winfo_width()
        self.spectrogram.coords(self.play_cursor, (x_pixel, 0, x_pixel, self.spectrogram.winfo_height()))
        self.spectrogram.coords(self.play_cursor_text, x_pixel + 3, 5)
        self.spectrogram.itemconfig(self.play_cursor_text, text="%.3f" % x)
        self.spectrogram.lift("play_cursor")

    def placePlaySel (self):
        x_start = ((self.play_selection_start_x - self.xzoom_start) / (self.xzoom_end - self.xzoom_start)) * self.spectrogram.winfo_width()
        x_end = ((self.play_selection_end_x - self.xzoom_start) / (self.xzoom_end - self.xzoom_start)) * self.spectrogram.winfo_width()
        self.spectrogram.coords(self.play_selection_start, (x_start, 0, x_start, self.spectrogram.winfo_height()))
        self.spectrogram.coords(self.play_selection_end, (x_end, 0, x_end, self.spectrogram.winfo_height()))
        self.spectrogram.coords(self.play_selection_start_text, x_start + 3, 5)
        self.spectrogram.itemconfig(self.play_selection_start_text, text="%.3f" % self.play_selection_start_x)
        self.spectrogram.coords(self.play_selection_dur_text, x_start + ((x_end - x_start) / 2), 5)
        self.spectrogram.itemconfig(self.play_selection_dur_text, text="%.3f" % (self.play_selection_end_x - self.play_selection_start_x))
        self.spectrogram.coords(self.play_selection_end_text, x_end - 3, 5)
        self.spectrogram.itemconfig(self.play_selection_end_text, text="%.3f" % self.play_selection_end_x)
        self.spectrogram.lift("sel_cursor")
    
    def playWhole (self, event=None):
        if self.spectrogram_initialised:
            self.play(0, self.current_dur)

    def playCursor (self, event=None):
        if self.spectrogram_initialised:
            if self.play_selection_start_x != -1:
                self.play(self.play_selection_start_x, self.play_selection_end_x)
            else:
                self.play(self.play_cursor_x, self.xzoom_end)
            return 'break'

    def playSelection (self, event=None):
        if self.spectrogram_initialised:
            self.play(self.boundaries[self.left_boundary].ms, self.boundaries[self.right_boundary].ms)
            
    ##################
    #                #
    # IMAGE HANDLING #
    #                #
    ##################

    def displayWaveform (self):
        if self.spectrogram_initialised:
            self.waveform.delete("waveform")
            self.master.update()
            width = self.waveform.winfo_width()
            height = self.waveform.winfo_height()
            pps = width / (self.xzoom_end - self.xzoom_start)
            start = int(self.current_sample_rate * self.xzoom_start)
            end = int(self.current_sample_rate * self.xzoom_end)
            self.waveform_image = tkSnack.createWaveform(self.waveform, 0, 0, pixelspersecond=pps, height=height, tags="waveform", sound=self.sound, start=start, end=end)
    
    def displaySpectrogram (self):
        if self.spectrogram_initialised:
            self.spectrogram.delete("spectrogram")
            self.yzoom_end = self.spectrogram_max_freq
            self.master.update()
            width = self.spectrogram.winfo_width()
            height = self.spectrogram.winfo_height()
            pps = width / (self.xzoom_end - self.xzoom_start)
            start = int(self.current_sample_rate * self.xzoom_start)
            end = int(self.current_sample_rate * self.xzoom_end)
            winlength = int(self.spectrogram_window_length * self.current_sample_rate)
            fftlength = 2 ** (int(log(winlength, 2)) + 1)
            self.spectrogram_image = tkSnack.createSpectrogram(self.spectrogram, 0, 0, pixelspersecond=pps, height=height, tags="spectrogram", sound=self.sound, start=start, end=end, winlength=winlength, fftlength=fftlength, topfrequency=self.spectrogram_max_freq, brightness=self.spectrogram_brightness)
            self.drawMeasurements()
            self.placePlayCursor(self.play_cursor_x)
            self.placePlaySel()

    def darkenSpectrogram (self, event=None):
        if self.spectrogram_brightness >= -100 + self.spectrogram_brightening_amount:
            self.spectrogram_brightness -= self.spectrogram_brightening_amount
            self.entry_spectrogram_brightness.delete(0, END)
            self.entry_spectrogram_brightness.insert(0, str(self.spectrogram_brightness))
            self.displaySpectrogram()
    
    def brightenSpectrogram (self, event=None):
        if self.spectrogram_brightness <= 100 - self.spectrogram_brightening_amount:
            self.spectrogram_brightness += self.spectrogram_brightening_amount
            self.entry_spectrogram_brightness.delete(0, END)
            self.entry_spectrogram_brightness.insert(0, str(self.spectrogram_brightness))
            self.displaySpectrogram()


    ##################
    #                #
    #   STATUS BAR   #
    #                #
    ##################

    def displayLocation (self, event):
        if self.spectrogram_initialised:
            s = self.xzoom_start + (event.x / self.spectrogram.winfo_width()) * (self.xzoom_end - self.xzoom_start)
            hz = self.yzoom_start + (1 - (event.y / self.spectrogram.winfo_height())) * (self.yzoom_end - self.yzoom_start)
            self.updateLocation(s, hz)

    def displayLocationDrag (self, x, y):
        if self.spectrogram_initialised:
            s = self.xzoom_start + (x / self.spectrogram.winfo_width()) * (self.xzoom_end - self.xzoom_start)
            hz = self.yzoom_start + (1 - (y / self.spectrogram.winfo_height())) * (self.yzoom_end - self.yzoom_start)
            self.updateLocation(s, hz)


    def updateLocation (self, s, hz):
        status_text = self.status_bar.cget("text")
        status = status_text[self.status_bar_location_size:]
        location = "%7.3f s, %5d Hz;" % (s, hz)
        location += " " * (self.status_bar_location_size - len(location))
        self.status_bar.config(text=location+status)

    def updateStatus (self, status):
        status_text = self.status_bar.cget("text")
        location = status_text[:self.status_bar_location_size]
        location += " " * (self.status_bar_location_size - len(location))
        self.status_bar.config(text=location+status)

    def updateStatusFading (self, status):
        self.updateStatus(status)
        self.master.after(self.status_fade_time, self.deleteStatus, status)

    def deleteStatus (self, status):
        status_text = self.status_bar.cget("text")
        status_curr = status_text[self.status_bar_location_size:]
        if status_curr == status:
            location = status_text[:self.status_bar_location_size]
            location += " " * (self.status_bar_location_size - len(location))
            self.status_bar.config(text=location)
            

    ##################
    #                #
    #  MEASUREMENTS  #
    #                #
    ##################

    def createMeasurements (self):
        """
        Establishes boundaries and creates formant measurements for a list
        of files (specified in @db, which is a @Database).
        """
        output = []
        c = 0
        maxx = len(self.db.wav_list)
        for w in self.db.wav_list:
            wav = self.current_files[w]
            textgrid = os.path.splitext(wav)[0] + ".TextGrid"
            dur, left, right = self.createBoundaryMeasurements(textgrid)
            formant_list = self.createFormantList(wav, left, right)
            output.append([[dur, left, right], formant_list, {}])
            c += 1
            self.updateStatus(str(c) + " of " + str(maxx) + " files processed.")
            self.master.update()
        return output
    
    def createBoundaryMeasurements (self, textgrid):
        boundaries = [float(x) for x in self.praatRunScript("get_times.praat", [textgrid]).strip().split('\t')]
        if len(boundaries) != 4:
            raise ValueError("Invalid TextGrid.")
        dur = boundaries[-1] - boundaries[0]
        sel_start = boundaries[1]
        sel_end = boundaries[-2]
        return dur, sel_start, sel_end
    
    def boundaryMeasurementsToBoundaries (self, dur, l, r):
        self.spectrogram.delete("boundary")
        left = Boundary(l,
                     self.spectrogram.create_line(0, 0, 0, 0, fill=self.boundary_colour, width=self.boundary_width, tags="boundary"),
                     None)
        right = Boundary(r,
                      self.spectrogram.create_line(0, 0, 0, 0, fill=self.boundary_colour, width=self.boundary_width, tags="boundary"),
                      left.id)
        self.left_boundary_text = self.spectrogram.create_text(0,0,text="",fill=self.boundary_text_colour,tags="boundary",anchor=SE,activefill="red")
        self.right_boundary_text = self.spectrogram.create_text(0,0,text="",fill=self.boundary_text_colour,tags="boundary",anchor=SW,activefill="red")
        self.mid_boundary_text = self.spectrogram.create_text(0,0,text="",fill=self.boundary_text_colour,tags="boundary",anchor=N,activefill="red")
        left.other = right.id
        self.boundaries = {left.id:left, right.id:right}
        self.current_dur = dur
        self.left_boundary = left.id
        self.right_boundary = right.id

    def boundariesToBoundaryMeasurements (self):
        return self.dur, self.boundaries[self.left_boundary].ms, self.boundaries[self.right_boundary].ms
        
    def createFormantList (self, wav, left, right):
        options = [wav, left, right,
                   self.formant_number_of_measurements, self.formant_number_of_formants,
                   self.formant_max_freq, self.formant_window_length,
                   self.formant_pre_emph]
        txt = self.praatRunScript("get_formant_trajectory.praat", options)
        lines = [x.split() for x in txt.strip().split("\n")]
        output = []
        for p in range(len(lines)):
            line = lines[p]
            for f in range(len(line)):
                if p == 0:
                    output.append([])
                if line[f] == "--undefined--":
                    output[f].append(None)
                else:
                    output[f].append(float(line[f]))
        return self.repairFormantMeasurements(output)
    
    def createColours (self):
        self.regular_range = []
        self.selected_range = []
        self.regular_range = ["#%02x%02x%02x" % (self.regular_from[0] + ((self.regular_to[0] - self.regular_from[0]) / (self.formant_use_number - 1)) * i, self.regular_from[1] + ((self.regular_to[1] - self.regular_from[1]) / (self.formant_use_number - 1)) * i, self.regular_from[2] + ((self.regular_to[2] - self.regular_from[2]) / (self.formant_use_number - 1)) * i) for i in range(self.formant_use_number)]
        self.selected_range = ["#%02x%02x%02x" % (self.selected_from[0] + ((self.selected_to[0] - self.selected_from[0]) / (self.formant_use_number - 1)) * i, self.selected_from[1] + ((self.selected_to[1] - self.selected_from[1]) / (self.formant_use_number - 1)) * i, self.selected_from[2] + ((self.selected_to[2] - self.selected_from[2]) / (self.formant_use_number - 1)) * i) for i in range(self.formant_use_number)]
        self.trajectory_fill_colours = []
        self.trajectory_outline_colours = []
        for f in range(len(self.trajectories_list)):
            current_trajectory = self.trajectories_list[f]
            current_trajectory_fill_colours = []
            current_trajectory_outline_colours = []
            for p in current_trajectory:
                if f >= self.formant_use_number:
                    current_trajectory_fill_colours.append("")
                    current_trajectory_outline_colours.append("")
                else:
                    if p in self.selected_points:
                        current_trajectory_fill_colours.append(self.selected_range[f])
                        if self.trajectories_dic[p].tags:
                            current_trajectory_outline_colours.append(self.tag_selected_colour)
                        else:
                            current_trajectory_outline_colours.append(self.regular_range[f])
                    else:
                        current_trajectory_fill_colours.append(self.regular_range[f])
                        if self.trajectories_dic[p].tags:
                            current_trajectory_outline_colours.append(self.tag_colour)
                        else:
                            current_trajectory_outline_colours.append(self.regular_range[f])
            self.trajectory_fill_colours.append(current_trajectory_fill_colours)
            self.trajectory_outline_colours.append(current_trajectory_outline_colours)
    
    def getNumberOfAvailableFormants (self, formant_list):
        if [] in formant_list:
            self.available_formants = formant_list.index([])
        else:
            self.available_formants = len(formant_list)
        if self.available_formants < self.formant_use_number:
            self.formant_use_number = self.available_formants
            self.entry_formant_use_number.delete(0, END)
            self.entry_formant_use_number.insert(0, self.formant_use_number)
        self.label_available_formants["text"] = "/ " + str(self.available_formants)
        
                       
    def formantListToTrajectory (self, formant_list, tags=None):
        self.clearSelectionList()
        self.spectrogram.delete("formant")
        self.trajectories_dic = {}
        self.trajectories_list = []
        self.getNumberOfAvailableFormants(formant_list)
        for f in range(len(formant_list)):
            line = formant_list[f]
            self.trajectories_list.append([])
            for p in range(len(line)):
                idd = self.spectrogram.create_oval(0,0,0,0, fill="", outline="", tags="formant", width=self.formant_outline_width)
                idd_2 = self.spectrogram.create_text(0,0,text="",fill="red",anchor=CENTER, font="Helvetica 8", tags="formant_label")
                self.trajectories_list[f].append(idd)
                self.trajectories_dic[idd] = Point(line[p], idd, f)
                self.trajectories_dic[idd].tag_id = idd_2
        for f in range(len(self.trajectories_list)):
            for p in range(len(self.trajectories_list[f])):
                if f == 0:
                    below = None
                else:
                    below = self.trajectories_list[f - 1][p]
                if f == len(self.trajectories_list) - 1 or not self.trajectories_list[f + 1]:
                    above = None
                else:
                    above = self.trajectories_list[f + 1][p]
                if p == 0:
                    previous = None
                else:
                    previous = self.trajectories_list[f][p - 1]
                if p == len(self.trajectories_list[f]) - 1:
                    following = None
                else:
                    following = self.trajectories_list[f][p + 1]
                self.trajectories_dic[self.trajectories_list[f][p]].below = below
                self.trajectories_dic[self.trajectories_list[f][p]].above = above
                self.trajectories_dic[self.trajectories_list[f][p]].previous = previous
                self.trajectories_dic[self.trajectories_list[f][p]].following = following
                if tags:
                    if (f,p) in tags:
                        self.trajectories_dic[self.trajectories_list[f][p]].tags = tags[(f,p)]
                        tag_text = ""
                        self.spectrogram.itemconfig(self.trajectories_dic[self.trajectories_list[f][p]].tag_id, text=tag_text)

    def trajectoryToFormantList (self):
        """
        Trajectories are the structures used by the program to represent the current
        formant trajectories. They include pointers to graphical objects.
        Formant lists store the same data in a much simpler format without pointers
        to graphical objects.
        """
        output = []
        for trajectory in self.trajectories_list:
            output.append([])
            for measurement in trajectory:
                output[-1].append(self.trajectories_dic[measurement].hz)
        return output

    def repairFormantMeasurements (self, trajectories_list):
        """
        Praat sometimes skips a formant measurement and returns
        --undefined--; this method fills in the gaps left by
        such undefined values
        """
        for t in range(len(trajectories_list)):
            trajectory = trajectories_list[t]
            lastt = None
            nextt = None
            move_on = False
            for p in range(len(trajectory)):
                none_counter = 0
                value = trajectory[p]
                if value == None and p == len(trajectory) - 1:
                    trajectory[p] = lastt
                elif value == None:
                    for p2 in range(p + 1, len(trajectory)):
                        value2 = trajectory[p2]
                        if value2 != None:
                            nextt = value2
                            none_counter = p2 - p
                            break
                        elif p2 == len(trajectory) - 1:
                            if lastt != None:
                                nextt = lastt
                                none_counter = p2 - p
                                break
                            else:
                                trajectories_list[t] = []
                                move_on = True
                                break
                    if not move_on:
                        if lastt == None:
                            lastt = nextt
                        start = lastt
                        incr = (nextt - lastt) / (none_counter + 1)
                        for p2 in range(p, p + none_counter):
                            trajectory[p2] = start + incr * (p2 - p + 1)
                    else:
                        break
                else:
                    lastt = value
                # check if smaller than prev formants
                if t > 0:
                    if len(trajectories_list[t - 1]) > 0:
                        if trajectories_list[t][p] < trajectories_list[t-1][p] + self.formant_minimum_separation:
                            trajectories_list[t][p] = trajectories_list[t-1][p] + self.formant_minimum_separation
        return trajectories_list

    def refreshMeasurements (self, event=None):
        if self.spectrogram_initialised:
            formant_list = self.createFormantList(self.current_path, self.boundaries[self.left_boundary].ms, self.boundaries[self.right_boundary].ms)
            self.formantListToTrajectory(formant_list)
            self.displaySpectrogram()

            
    ##################
    #                #
    #    DRAWING     #
    #                #
    ##################

    def drawMeasurements (self):
    	if self.current_redrawn_formant:
        	self.exitDrawMode()
        for b in self.boundaries:
            boundary = self.boundaries[b]
            x1 = ((boundary.ms - self.xzoom_start) / (self.xzoom_end - self.xzoom_start)) * self.spectrogram.winfo_width()
            x2 = x1
            y1 = 0
            y2 = self.spectrogram.winfo_height()
            self.spectrogram.coords(boundary.id, x1, y1, x2, y2)
        self.placeBoundaryText()
        self.spectrogram.tag_raise("boundary")
        self.createColours()
        for t in range(len(self.trajectories_list)):
            trajectory = self.trajectories_list[t]
            for p in range(len(trajectory)):
                fill_colour = self.trajectory_fill_colours[t][p]
                outline_colour = self.trajectory_outline_colours[t][p]
                point = self.trajectories_dic[trajectory[p]]
                #self.spectrogram.itemconfig(point.id, outline=outline_colour)
                self.spectrogram.itemconfig(point.id, fill=fill_colour)
                self.spectrogram.itemconfig(self.trajectories_dic[point.id].tag_id, text=self.createTagText(point.id))    
                x_time = self.boundaries[self.left_boundary].ms + p * ((self.boundaries[self.right_boundary].ms - self.boundaries[self.left_boundary].ms) / (len(trajectory) - 1))
                x1 = (((x_time - self.xzoom_start) / (self.xzoom_end - self.xzoom_start)) * self.spectrogram.winfo_width()) - (self.trajectory_width / 2)
                x2 = x1 + self.trajectory_width
                y1 = ((1 - ((point.hz - self.yzoom_start) / (self.yzoom_end - self.yzoom_start))) * self.spectrogram.winfo_height()) - (self.trajectory_width / 2)
                y2 = y1 + self.trajectory_width
                self.spectrogram.coords(point.id, x1, y1, x2, y2)
                self.spectrogram.coords(self.trajectories_dic[point.id].tag_id, (x1 + x2)/2, (y1 + y2)/2)
                self.spectrogram.lift(point.id)
                self.spectrogram.lift(self.trajectories_dic[point.id].tag_id)
                if t >= self.formant_use_number:
                    self.spectrogram.itemconfig(point.id, state=HIDDEN)
                    self.spectrogram.itemconfig(self.trajectories_dic[point.id].tag_id, state=HIDDEN)
                else:
                    self.spectrogram.itemconfig(point.id, state=NORMAL)
                    self.spectrogram.itemconfig(self.trajectories_dic[point.id].tag_id, state=NORMAL)
                    

    def placeBoundaryText (self):
        yloc = self.spectrogram.winfo_height() - 5
        x_left = self.spectrogram.coords(self.left_boundary)[0]
        x_right = self.spectrogram.coords(self.right_boundary)[0]
        ms_left = self.boundaries[self.left_boundary].ms
        ms_right = self.boundaries[self.right_boundary].ms
        self.spectrogram.itemconfig(self.left_boundary_text, text="%.3f" % ms_left)
        self.spectrogram.coords(self.left_boundary_text, x_left - 5, yloc)
        self.spectrogram.itemconfig(self.right_boundary_text, text="%.3f" % ms_right)
        self.spectrogram.coords(self.right_boundary_text, x_right + 5, yloc)
        self.spectrogram.itemconfig(self.mid_boundary_text, text="dur=%.3f" % (ms_right - ms_left))
        self.spectrogram.coords(self.mid_boundary_text, x_left + ((x_right - x_left) / 2), 5)

    def hide (self, event=None):
        if self.hide_measurements:
            self.hideOff()
        else:
            self.hideOn()
    
    def hideOn (self):
        self.hide_measurements = True
        self.spectrogram.itemconfig("boundary", state=HIDDEN)
        self.spectrogram.itemconfig("formant", state=HIDDEN)

    def hideOff (self):
        self.hide_measurements = False
        self.spectrogram.itemconfig("boundary", state=NORMAL)
        self.spectrogram.itemconfig("formant", state=NORMAL)
        

    def hideThirdFormant (self, event=None):
        if self.formant_use_number > 2:
            self.formant_use_number = 2
            self.entry_formant_use_number.delete(0, END)
            self.entry_formant_use_number.insert(0, str(self.formant_use_number))
            self.displaySpectrogram()

    ##################
    #                #
    # SEL,FOCUS,DRAW #
    #                #
    ##################

    def spectrogramButtonDown (self, event=None):
        if self.spectrogram_initialised:
            self.spectrogram.focus_set()
            closest = self.spectrogram.find_overlapping(event.x - 3, event.y - 3, event.x + 3, event.y + 3)
            if not self.current_redrawn_formant:
                for item in list(closest):
                    if item in self.boundaries or item in self.trajectories_dic:
                        return
                self.clearSelection()
            if self.current_redrawn_formant and not self.hide_measurements:
                self.redraw = self.current_redrawn_formant
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
            elif not self.current_redrawn_formant:
                self.clickPlayCursor(event)
                self.play_selection_start_x = -1
                self.play_selection_end_x = -1
                self.play_selection_on = True

    def clearSelectionList (self, event=None):
        self.selected_points = []
        
        

    def clearSelection (self, event=None):
        self.clearSelectionList()
        self.drawMeasurements()
        
    def selectOn (self, event=None):
        if self.spectrogram_initialised:
            self.spectrogram.focus_set()
            if not self.current_redrawn_formant:
                self.mouse_has_moved = False
                self.select_anchor_x = event.x
                self.select_anchor_y = event.y
                self.selection_box = self.spectrogram.create_rectangle(event.x, event.y, event.x, event.y, fill="", outline="darkgreen", width=self.play_cursor_width)
            

    def selectMotion (self, event=None):
        if self.spectrogram_initialised and self.select_anchor_x != -1:
            self.mouse_has_moved = True
            self.spectrogram.coords(self.selection_box, self.select_anchor_x, self.select_anchor_y, event.x, event.y)

    def selectOff (self, event=None):
        if self.spectrogram_initialised and not self.current_redrawn_formant and self.mouse_has_moved:
            inside_rectangle = self.spectrogram.find_overlapping(self.select_anchor_x, self.select_anchor_y, event.x, event.y)
            for item in list(inside_rectangle):
                if item in self.trajectories_dic:
                    if item not in self.selected_points:
                        self.selected_points.append(item)
            self.drawMeasurements()
        self.spectrogram.delete(self.selection_box)
        self.selection_box = -1
        self.select_anchor_x = -1
        self.select_anchor_y = -1
            
            

    ##################
    #                #
    # REDRAW,PLAYSEL #
    #                #
    ##################

    # this is a bit complicated -- to avoid issues with key debouncing


    def keyDown (self, event):
        print event.keysym
        if event.keysym in map(str, range(1, self.formant_use_number + 1)) and not self.play_selection_on:
            # in case another formant is already being redrawn...
            if self.current_redrawn_formant:
            	if self.current_redrawn_formant != int(event.keysym):
            		self.exitDrawMode()
            		self.drawMeasurements()
            		self.current_redrawn_formant = int(event.keysym)
            		self.circlesToLines(self.current_redrawn_formant)
            	else:
            		self.exitDrawMode()
            		self.drawMeasurements()
            else:
            	self.clearSelection()
            	self.current_redrawn_formant = int(event.keysym)
            	self.circlesToLines(self.current_redrawn_formant)
        else:
        	self.exitDrawMode()
        	self.drawMeasurements()
    # old code using key hold instead of key press

            #if self.platform == 'Windows':
            #    if not self.current_redrawn_formant:
            #		self.current_redrawn_formant = int(event.keysym)
            #		self.circlesToLines(self.current_redrawn_formant)
            #else:
            #    if self.afterId:
            #        self.master.after_cancel(self.afterId)
            #        self.afterId = None
            #    else:
            #        self.current_redrawn_formant = int(event.keysym)
            #        self.circlesToLines(self.current_redrawn_formant)
                    
    #def keyUp (self, event):
    #    if event.keysym in map(str, range(1, self.formant_use_number + 1)) and not self.play_selection_on:
            #if self.current_redrawn_formant:
            #    if self.platform == 'Windows':
            #        self.exitDrawMode(event.keysym)
            #    else:
            #        self.afterId = self.master.after(300, self.exitDrawMode, event.keysym)

    def exitDrawMode (self):
        if self.current_redrawn_formant:
            self.deleteFormantLine()        	
            self.redraw = 0
            self.current_redrawn_formant = 0
			#self.afterId = None
			
            
            
    def circlesToLines (self, formant_no):
        self.formant_line_coordinates = []
        for point in self.trajectories_list[formant_no - 1]:
            xy = self.spectrogram.coords(point)
            x = xy[0] + (self.trajectory_width / 2)
            y = xy[1] + (self.trajectory_width / 2)
            self.formant_line_coordinates.append((x,y))
            self.spectrogram.itemconfig(point, state=HIDDEN)
            self.spectrogram.itemconfig(self.trajectories_dic[point].tag_id, state=HIDDEN)
        self.formant_line = self.spectrogram.create_line(self.formant_line_coordinates, fill=self.formant_line_colour, width=self.formant_line_width)

    def deleteFormantLine (self):
        self.spectrogram.delete(self.formant_line)
        self.formant_line_coordinates = []
        #for point in self.trajectories_list[self.current_redrawn_formant - 1]:
        #    self.spectrogram.itemconfig(point, state=NORMAL)
        #    self.spectrogram.itemconfig(self.trajectories_dic[point].tag_id, state=NORMAL)
        #    self.spectrogram.lift(point)
        #    self.spectrogram.lift(self.trajectories_dic[point].tag_id)
        

    def updateFormantLine (self, point_no):
        xy = self.spectrogram.coords(self.trajectories_list[self.current_redrawn_formant - 1][point_no])
        x = xy[0] + (self.trajectory_width / 2)
        y = xy[1] + (self.trajectory_width / 2)
        self.formant_line_coordinates[point_no] = (x, y)
        c = []
        map(c.extend, self.formant_line_coordinates)
        self.spectrogram.coords(self.formant_line, *c)

    def spectrogramButtonMotion (self, event):
        if self.spectrogram_initialised:
            if self.select_anchor_x != -1:
                self.selectMotion(event)
                return
            if self.redraw and (self.redraw - 1) < len(self.trajectories_list):
                self.displayLocation(event)
                trajectory = self.trajectories_list[self.redraw - 1]
                for p in range(len(trajectory)):
                    point_id = trajectory[p]
                    point_x = self.spectrogram.coords(point_id)[0] + (self.trajectory_width / 2)
                    if (event.x > point_x and self.drag_data["x"] <= point_x) or (event.x < point_x and self.drag_data["x"] >= point_x):
                        interpolated_y = self.drag_data["y"] + ((point_x - self.drag_data["x"]) / (event.x - self.drag_data["x"])) * (event.y - self.drag_data["y"])
                        below_id = self.trajectories_dic[point_id].below
                        above_id = self.trajectories_dic[point_id].above
                        if above_id == None:
                            above = 0
                        else:
                            above = self.spectrogram.coords(above_id)[3]
                        if below_id == None:
                            below = self.spectrogram.winfo_height()
                        else:
                            below = self.spectrogram.coords(below_id)[1]
                        if (interpolated_y + (self.trajectory_width / 2) < below) and (interpolated_y - (self.trajectory_width / 2) > above):
                            self.spectrogram.coords(point_id, (point_x - (self.trajectory_width / 2), interpolated_y - (self.trajectory_width / 2), point_x + (self.trajectory_width / 2), interpolated_y + (self.trajectory_width / 2)))
                            self.updateFormantLine(p)
                            new_hz = self.yzoom_start + (1 - (interpolated_y / self.spectrogram.winfo_height())) * (self.yzoom_end - self.yzoom_start)
                            self.trajectories_dic[point_id].hz = new_hz
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
            elif self.play_selection_on:
                self.displayLocation(event)
                if event.x >= 0 and event.x <= self.spectrogram.winfo_width():
                    self.placePlayCursor(-1)
                    cursor_x = self.xzoom_start + ((event.x / self.spectrogram.winfo_width()) * (self.xzoom_end - self.xzoom_start))
                    if cursor_x >= self.play_cursor_x:
                        self.play_selection_start_x = self.play_cursor_x
                        self.play_selection_end_x = cursor_x
                    else:
                        self.play_selection_start_x = cursor_x
                        self.play_selection_end_x = self.play_cursor_x
                    self.placePlaySel()

    def spectrogramButtonUp (self, event):
        if self.spectrogram_initialised:
            if self.select_anchor_x != -1:
                self.selectOff(event)
                return
            self.drag_data["x"] = 0
            self.drag_data["y"] = 0
            #if self.redraw: 
            #    self.redraw = 0
            #    self.drawMeasurements()
            self.play_selection_on = False
            if self.play_selection_start_x == self.play_selection_end_x:
                self.play_selection_start_x = -1
                self.play_selection_end_x = -1
                self.placePlaySel()
                self.placePlayCursor(self.play_cursor_x)
            else:
                self.play_cursor_x = -1
            

    def tag (self, tag_number, event=None):
        if self.selected_points:
            print sum([self.trajectories_dic[i].tags for i in self.selected_points], [])
            tagged = sum([self.trajectories_dic[i].tags for i in self.selected_points], []).count(tag_number)
            for i in self.selected_points:
                if tagged < len(self.selected_points):
                    if tag_number not in self.trajectories_dic[i].tags:
                        self.trajectories_dic[i].tags.append(tag_number)
                else:
                    if tag_number in self.trajectories_dic[i].tags:
                        self.trajectories_dic[i].tags.remove(tag_number)
            self.drawMeasurements()
            
    def createTagText (self, point_id):
        return "".join([str(x) for x in sorted(self.trajectories_dic[point_id].tags)])

    def writeTags (self):
        output = {}
        for f in range(len(self.trajectories_list)):
            trajectory = self.trajectories_list[f]
            for p in range(len(trajectory)):
                point = trajectory[p]
                if self.trajectories_dic[point].tags:
                    output[(f,p)] = self.trajectories_dic[point].tags
        return output

    ##################
    #                #
    #  DRAG & DROP   #
    #                #
    ##################

    def boundaryDown (self, event):
        self.boundary_has_changed = False
        closest = self.spectrogram.find_overlapping(event.x - 3, event.y - 3, event.x + 3, event.y + 3)
        for item in list(closest):
            if item in self.boundaries:
                if not self.current_redrawn_formant:
                    self.drag_data["item_id"] = item
                    self.drag_data["x"] = event.x
                    self.drag_data["y"] = event.y
                    return

    def boundaryUp (self, event):
        self.drag_data["item_id"] = None
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0
        if self.boundary_has_changed:
            self.refreshMeasurements()

    def boundaryMotion (self, event):
        delta_x = event.x - self.drag_data["x"]
        if not self.current_redrawn_formant and self.drag_data["item_id"]:
            self.boundary_has_changed = True
            xmin = self.spectrogram.coords(self.drag_data["item_id"])[0]
            xmax = self.spectrogram.coords(self.drag_data["item_id"])[0]
            if not (xmin + delta_x < self.boundary_width or xmax + delta_x > self.spectrogram.winfo_width() - self.boundary_width):
                move = True
                old_x = self.spectrogram.coords(self.drag_data["item_id"])[0]
                new_x = old_x + delta_x
                other_x = self.spectrogram.coords(self.boundaries[self.drag_data["item_id"]].other)[0]
                if (old_x - other_x) / abs(old_x - other_x) != (new_x - other_x) / abs(new_x - other_x):
                    move = False
                if move: 
                    self.spectrogram.move(self.drag_data["item_id"], delta_x, 0)
                    canvas_x = self.spectrogram.coords(self.drag_data["item_id"])[0]
                    new_ms = self.xzoom_start + (canvas_x / self.spectrogram.winfo_width()) * (self.xzoom_end - self.xzoom_start)
                    self.boundaries[self.drag_data["item_id"]].ms = new_ms
                display_x = self.spectrogram.coords(self.drag_data["item_id"])[0]
                display_y = event.y
                self.displayLocationDrag(display_x, display_y)
                self.placeBoundaryText()
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def formantDown (self, event):
        closest = self.spectrogram.find_overlapping(event.x - 3, event.y - 3, event.x + 3, event.y + 3)
        print closest
        for item in list(closest):
            if item in self.trajectories_dic:
                if not self.current_redrawn_formant:
                    if item not in self.selected_points:
                        self.clearSelection()
                        self.current_dragged_point = [item]
                    else:
                        self.current_dragged_point = []
                    self.drag_data["item_id"] = item
                    self.drag_data["x"] = event.x
                    self.drag_data["y"] = event.y
    
    def shiftFormantDown (self, event):
        closest = self.spectrogram.find_overlapping(event.x - 3, event.y - 3, event.x + 3, event.y + 3)
        for item in list(closest):
            if item in self.trajectories_dic:
                if not self.current_redrawn_formant:
                    if item not in self.selected_points:
                        self.selected_points.append(item)
                    else:
                        self.selected_points.remove(item)
                    self.drawMeasurements()
                    return


    def formantUp (self, event):
        self.drag_data["item_id"] = None
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0
        self.current_dragged_point = -1
            
    def shiftFormantUp (self, event):
        pass

    def formantMotion (self, event):
        delta_x = event.x - self.drag_data["x"]
        delta_y = event.y - self.drag_data["y"]
        if not self.current_redrawn_formant:
            ymin = self.spectrogram.coords((self.selected_points + self.current_dragged_point)[0])[1]
            ymax = self.spectrogram.coords((self.selected_points + self.current_dragged_point)[0])[1]
            for point_id in list(set(self.selected_points + self.current_dragged_point)):
                y_bottom = self.spectrogram.coords(point_id)[1]
                y_top = self.spectrogram.coords(point_id)[3]
                if y_bottom < ymin:
                    ymin = y_bottom
                elif y_top > ymax:
                    ymax = y_top
            temp_selected_points = self.selected_points[:] + self.current_dragged_point[:]
            selected_columns = []
            while len(temp_selected_points) > 0:
                point_id = temp_selected_points[0]
                selected_columns.append([point_id])
                temp_selected_points.remove(point_id)
                while True:
                    above = self.trajectories_dic[selected_columns[-1][-1]].above
                    if above in temp_selected_points:
                        selected_columns[-1].append(above)
                        temp_selected_points.remove(above)
                    else:
                        break
                while True:
                    below = self.trajectories_dic[selected_columns[-1][-1]].below
                    if below in temp_selected_points:
                        selected_columns[-1].insert(0, below)
                        temp_selected_points.remove(below)
                    else:
                        break
            for column in selected_columns:
                if delta_y > 0:
                    counter = 0
                    step = 1
                else:
                    counter = len(column) - 1
                    step = -1
                while counter > -1 and counter < len(column):
                    point_id = column[counter]
                    counter += step
                    above_id = self.trajectories_dic[point_id].above
                    below_id = self.trajectories_dic[point_id].below
                    current = self.spectrogram.coords(point_id)[3] + delta_y - (self.trajectory_width / 2)
                    if above_id == None:
                        above = 0
                    else:
                        above = self.spectrogram.coords(above_id)[3]
                    if below_id == None:
                        below = self.spectrogram.winfo_height()
                    else:
                        below = self.spectrogram.coords(below_id)[1]
                    if (current + (self.trajectory_width / 2) < below) and (current - (self.trajectory_width / 2) > above):
                        self.spectrogram.move(point_id, 0, delta_y)
                        self.spectrogram.move(self.trajectories_dic[point_id].tag_id, 0, delta_y)
                        canvas_y = self.spectrogram.coords(point_id)[1] + (self.trajectory_width / 2)
                        new_hz = self.yzoom_start + (1 - (canvas_y / self.spectrogram.winfo_height())) * (self.yzoom_end - self.yzoom_start)
                        self.trajectories_dic[point_id].hz = new_hz
            display_x = self.spectrogram.coords(self.drag_data["item_id"])[0] + (self.trajectory_width / 2)
            display_y = self.spectrogram.coords(self.drag_data["item_id"])[1] + (self.trajectory_width / 2)
            self.displayLocationDrag(display_x, display_y)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
    
    def Pass (self, event):
    	pass

    ##################
    #                #
    #  ZOOM & MOVE   #
    #                #
    ##################


    def xZoomIn (self, event=None):
        if self.spectrogram_initialised:
            width = self.xzoom_end - self.xzoom_start
            self.xzoom_start += width * (self.zoom_amount / 2)
            self.xzoom_end -= width * (self.zoom_amount / 2)
            self.displayWaveform()
            self.displaySpectrogram()

    def xZoomOut (self, event=None):
        if self.spectrogram_initialised:
            width = self.xzoom_end - self.xzoom_start
            zoom_incr = width * ((self.zoom_amount / 2) / (1 - self.zoom_amount))
            if self.xzoom_start - zoom_incr < 0:
                self.xzoom_start = 0
            else:
                self.xzoom_start -= zoom_incr
            if self.xzoom_end + zoom_incr > self.current_dur:
                self.xzoom_end = self.current_dur
            else:
                self.xzoom_end += zoom_incr
            self.displayWaveform()
            self.displaySpectrogram()

    def xScrollLeft (self, event=None):
        if self.spectrogram_initialised:
            width = self.xzoom_end - self.xzoom_start
            scroll_amount = width * self.scroll_amount
            if self.xzoom_start - scroll_amount < 0:
                self.xzoom_end = self.xzoom_end - (self.xzoom_start - 0)
                self.xzoom_start = 0
            else: 
                self.xzoom_start = self.xzoom_start - scroll_amount
                self.xzoom_end = self.xzoom_end - scroll_amount
            self.displayWaveform()
            self.displaySpectrogram()

    def xScrollRight (self, event=None):
        if self.spectrogram_initialised:
            width = self.xzoom_end - self.xzoom_start
            scroll_amount = width * self.scroll_amount
            if self.xzoom_end + scroll_amount > self.current_dur:
                self.xzoom_start = self.xzoom_start + (self.current_dur - self.xzoom_end)
                self.xzoom_end = self.current_dur
            else: 
                self.xzoom_start = self.xzoom_start + scroll_amount
                self.xzoom_end = self.xzoom_end + scroll_amount
            self.displayWaveform()
            self.displaySpectrogram()

    def xZoomToSelection (self, event=None):
        if self.spectrogram_initialised:
            if self.play_selection_start_x != -1:
                self.xzoom_start = self.play_selection_start_x
                self.xzoom_end = self.play_selection_end_x
            else:
                self.xzoom_start = self.boundaries[self.left_boundary].ms
                self.xzoom_end = self.boundaries[self.right_boundary].ms
            self.displayWaveform()
            self.displaySpectrogram()

class Boundary:

    def __init__ (self,
                  ms,
                  idd,
                  other=None):
        self.ms = ms
        self.id = idd
        self.other = other
        
class Point:

    def __init__ (self,
                  hz,
                  idd,
                  formant,
                  previous=None,
                  following=None,
                  above=None,
                  below=None):
        self.hz = hz
        self.id = idd
        self.formant = formant
        self.previous = previous
        self.following = following
        self.above = above
        self.below = below
        self.tags = []

class Database:
    
    """
    Class for easily accessing and storing metadata, formant tracker & spectrogram settings
    and measurements for a list of sound files. There are three central lists:
    @metadata_table, @settings_table and @measurements; a sound file is fully described by
    a single item from each of these lists (with the same index). The indices are linked
    to the sound file names through @wav_dic. @wav_list is useful for enumerating all the
    wav files.
    """
    
    def __init__ (self, wav_column, master_folder, metadata, settings, files, measurements=None):
        self.wav_dic = {}
        self.wav_list = []
        self.current_wav = None
        self.metadata_header = metadata[0]
        if wav_column not in self.metadata_header:
            raise ValueError ("WAV column not found in CSV file.")
        self.metadata_table = metadata[1]
        self.settings_header = settings[0]
        self.settings_table = settings[1]
        for r in range(len(self.metadata_table)):
            row = self.metadata_table[r]
            wav = row[self.metadata_header[wav_column]].lower()
            if wav in files:
                self.wav_dic[wav] = r
                self.wav_list.append(wav)
            else:
                raise ValueError("Unable to locate " + wav + ".")
        self.measurements = measurements
    
    def checkSettingsHeader (self, settings_header, settings):
        if self.settings_header != settings_header:
            self.settings_header = settings_header
            self.settings_table = [list(settings) for x in range(len(self.wav_list))]
            return(" Settings changed due to compatibility issues. Measurements remain the same.")
        return("") 
    
    def addAttribute (self, attr_name, sel_attr_name, default_value=""):
        k = self.metadata_header[sel_attr_name]
        for attr in self.metadata_header:
            if self.metadata_header[attr] >= k:
                self.metadata_header[attr] += 1
        self.metadata_header[attr_name] = k
        for row in self.metadata_table:
            row.insert(k, default_value)
    
    def removeAttribute (self, attr_name):
        k = self.metadata_header[attr_name]
        for attr in self.metadata_header:
            if self.metadata_header[attr] > k:
                self.metadata_header[attr] -= 1
        for row in self.metadata_table:
            row.pop(k)
        del self.metadata_header[attr_name]
        
    def upAttribute (self, attr_name):
        k = self.metadata_header[attr_name]
        if k > 0:
            prev_attr_name = self.metadata_header.items()[map(itemgetter(1), self.metadata_header.items()).index(k-1)][0]
            self.metadata_header[attr_name] = k - 1
            self.metadata_header[prev_attr_name] = k
        for row in self.metadata_table:
            k_val = row[k]
            row[k] = row[k-1]
            row[k-1] = k_val
            
    def downAttribute (self, attr_name):
        k = self.metadata_header[attr_name]
        if k < max(self.metadata_header.values()):
            foll_attr_name = self.metadata_header.items()[map(itemgetter(1), self.metadata_header.items()).index(k+1)][0]
            self.metadata_header[attr_name] = k + 1
            self.metadata_header[foll_attr_name] = k
        for row in self.metadata_table:
            k_val = row[k]
            row[k] = row[k+1]
            row[k+1] = k_val

    def refreshWavDic (self):
        self.wav_dic = {}
        for w in range(len(self.wav_list)):
            wav = self.wav_list[w]
            self.wav_dic[wav] = w

    def fullPath (self, wav):
        return self.file[wav]

    def get (self, wav, attr):
        if attr in self.metadata_header:
            return self.metadata_table[self.wav_dic[wav]][self.metadata_header[attr]]
        elif attr in self.settings_header:
            return self.settings_table[self.wav_dic[wav]][self.settings_header[attr]]
        else:
            raise ValueError ("Attribute " + attr + " does not exist.")

    def put (self, wav, attr, value):
        if attr in self.metadata_header:
            self.metadata_table[self.wav_dic[wav]][self.metadata_header[attr]] = value
        elif attr in self.settings_header:
            self.settings_table[self.wav_dic[wav]][self.settings_header[attr]] = value
        else:
            raise ValueError ("Attribute " + attr + " does not exist.")
        
    def join (self, db):
        if type(self)!=type(db):
            raise ValueError("You can only join Database objects.")
        if sorted(self.metadata_header.keys()) != sorted(db.metadata_header.keys()):
            raise ValueError("Metadata headers are different.")
        if len(set(self.wav_list) & set(db.wav_list)) > 0:
            raise ValueError ("WAV file occurs twice in joined database.")
        if map(itemgetter(1), sorted(self.metadata_header.items(),key=itemgetter(0))) != map(itemgetter(1), sorted(db.metadata_header.items(),key=itemgetter(0))):
            for i in range(len(db.metadata_table)):
                row = copy(db.metadata_table[i])
                for colname in db.metadata_header.keys():
                    db.metadata_table[i][self.metadata_header[colname]] = row[db.metadata_header[colname]]
        self.wav_list += db.wav_list
        self.refreshWavDic()
        self.measurements += db.measurements
        self.settings_table += db.settings_table
        self.metadata_table += db.metadata_table
            
    


class selectColumn (tkSimpleDialog.Dialog):

    def body(self, master):

        Label(master, text="Name of WAV column:").grid(row=0)
        Label(master, text="Number of measurement points:").grid(row=1)
        
        self.output = ("", 11)
        self.e1 = Entry(master)
        self.e1.insert(0, self.output[0])
        self.e2 = Entry(master)
        self.e2.insert(0, str(self.output[1]))

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1 # initial focus

    def apply(self):
        self.output = (self.e1.get(), int(self.e2.get()))

class selectFormantNo (tkSimpleDialog.Dialog):

    def body(self, master):

        Label(master, text="Max. no. of formants:").grid(row=0)
        Label(master, text="(note that formants hidden by the user are not written out)").grid(row=1, columnspan=2)
        
        self.no = 3
        self.e1 = Entry(master)
        self.e1.insert(0, self.no)

        self.e1.grid(row=0, column=1)
        return self.e1 # initial focus

    def apply(self):
        self.no = int(self.e1.get())

class selectAttrName (tkSimpleDialog.Dialog):

    def body(self, master):

        Label(master, text="Attribute name:").grid(row=0)
        Label(master, text="Default value:").grid(row=1)
        
        self.e1 = Entry(master)
        self.e2 = Entry(master)
        

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1 # initial focus

    def apply(self):
        self.output = (self.e1.get(), self.e2.get())

class selectFilterExpression (tkSimpleDialog.Dialog):

    def body(self, master):
        
        #master.columnconfigure(0, weight=1)
        #master.rowconfigure(0, weight=1)
        
        Label(master, text="Filter expression:").pack(side=LEFT)
        
        self.e1 = Entry(master)
        self.e1.insert(0, self.parameters)
        
        self.e1.pack(fill=X, expand=1)
        return self.e1 # initial focus

    def apply(self):
        self.output = self.e1.get()


class ConfigWindow (tkSimpleDialog.Dialog):

    def body(self, master):

        Label(master, text="Program folder:", anchor=E).grid(row=0)
        Label(master, text="Temporary folder:", anchor=E).grid(row=1)
        Label(master, text="Praat path:", anchor=E).grid(row=2)

        self.output = self.parameters
        self.program_folder_entry = Entry(master)
        self.program_folder_entry.insert(0, self.parameters["program_folder"])
        self.temporary_folder_entry = Entry(master)
        self.temporary_folder_entry.insert(0, self.parameters["temporary_folder"])
        self.praat_path_entry = Entry(master)
        self.praat_path_entry.insert(0, self.parameters["praat_path"])
        self.program_folder_browse = Button(master, text="Browse", command=self.programFolderBrowse)
        self.temporary_folder_browse = Button(master, text="Browse", command=self.temporaryFolderBrowse)
        self.praat_path_browse = Button(master, text="Browse", command=self.praatPathBrowse)
        self.program_folder_entry.grid(row=0, column=1)
        self.temporary_folder_entry.grid(row=1, column=1)
        self.praat_path_entry.grid(row=2, column=1)
        Label(master, text="  ", anchor=E).grid(row=0,column=2)
        Label(master, text="  ", anchor=E).grid(row=1,column=2)
        Label(master, text="  ", anchor=E).grid(row=2,column=2)
        self.program_folder_browse.grid(row=0, column=3)
        self.temporary_folder_browse.grid(row=1, column=3)
        self.praat_path_browse.grid(row=2, column=3)

        return self.program_folder_entry

    def programFolderBrowse (self):
        out = tkFileDialog.askdirectory(title="Set program folder...")
        if out:
            self.program_folder_entry.delete(0, END)
            self.program_folder_entry.insert(0, out)

    def temporaryFolderBrowse (self):
        out = tkFileDialog.askdirectory(title="Set temporary folder...")
        if out:
            self.temporary_folder_entry.delete(0, END)
            self.temporary_folder_entry.insert(0, out)

    def praatPathBrowse (self):
        out = tkFileDialog.askopenfilename(title="Set Praat path...")
        if out:
            self.praat_path_entry.delete(0, END)
            self.praat_path_entry.insert(0, out)

    def apply(self):
        self.output["program_folder"] = self.program_folder_entry.get()
        self.output["temporary_folder"] = self.temporary_folder_entry.get()
        self.output["praat_path"] = self.praat_path_entry.get()

class RewriteName(ast.NodeTransformer):
    
    def visit_Name(self, node):
        result = ast.copy_location(
            ast.Subscript(value=
                ast.Subscript(value=
                    ast.Attribute(value=
                        ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr="db", ctx=ast.Load()),
                    attr="metadata_table", ctx=ast.Load()),
                slice=ast.Index(value=ast.Name(id="index", ctx=ast.Load())), ctx=ast.Load()),
            slice=ast.Index(value=
                ast.Subscript(value=
                    ast.Attribute(value=
                        ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr="db", ctx=ast.Load()),
                    attr="metadata_header", ctx=ast.Load()),
                slice=ast.Index(value=ast.Str(s=node.id)), ctx=ast.Load())),
            ctx=node.ctx), node)
        ast.fix_missing_locations(result)
        return result



root = Tk()
root.wm_title("Formant editor")
tkSnack.initializeSnack(root)
app = formantMonitor(root, script_dir)
root.mainloop()
