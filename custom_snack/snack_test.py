from Tkinter import *
import os

root = Tk()

os.chdir("/volumes/stuff/york/formant_extractor/snack")

import tkSnack

tkSnack.initializeSnack(root)

mysound = tkSnack.Sound()
mysound.read('/volumes/stuff/york/search_test/carl_uw/carl_wl_c_19.wav')

cc = Canvas(root)
cc.pack(fill=BOTH)

tkSnack.createSpectrogram(cc, 0,0, sound=mysound)
