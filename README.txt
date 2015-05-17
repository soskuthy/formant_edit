README file for Formant Editor v0.8.2
by Márton Sóskuthy

1) INTRODUCTION

This is a development version of Formant Editor (working title for the project), a program for creating, checking and adjusting formant measurements for large lists of sound files. Formant Editor has its own graphical interface and allows the user to manipulate formant readings much more easily than other available speech analysis programs and packages. Formant Editor crucially relies on two other pieces of software to analyse speech samples:

- Praat, Copyright (C) Paul Boersma and David Weenink, 2014; available at "http://www.fon.hum.uva.nl/praat/"; Formant Editor relies on Praat to generate its formant readings
- the Snack Sound Toolkit, Copyright (C) Kåre Sjölander, 2005; available at "http://www.speech.kth.se/snack/"; Snack is used to generate spectrograms and waveforms

The Snack Sound Toolkit is included with the current version of Formant Editor, but you will need to download Praat separately.

Formant Editor is written in a programming language called Python, which means that you'll need to have Python (versions 2.6 or 2.7) installed on your computer to run it. You can download Python here:

- http://www.python.org/download/

Note that Formant Editor currently only supports 32 bit versions of Python under Windows 7 and 8 (but it doesn't matter whether the OS itself is 32 or 64 bit).

2) INSTALLATION

Formant Editor is run through Python, which means that you do not have to install it. All you need to do is copy the "formant_edit" library to your computer somewhere where you'll find it. The current version of Formant Editor has been tested on Mac OS X 10.5-10.9,  Windows 7 and Windows 8. It is likely that you will encounter problems if you try to run it on other operating systems.

On Mac computers, you can run Formant Editor from the Terminal by navigating to its parent folder and typing

	python formant_check.py

This should bring up a new window with Formant Editor.

On Windows computers, you're advised to open Formant Editor using IDLE, a user interface for Python (which ships with the standard Python distribution). Just open formant_check.py with IDLE, and then press F5. The program should start up in a new window.

Before you can start using Formant Editor, you have to configure it. This is really simple: you need to set (i) the path to the folder containing Formant Editor (ii) the path to your temporary folder (this can be any folder) and (iii) the path to Praat. The first two parameters are configured automatically, so you likely won't have to change them. However, you'll have to set up the path to Praat manually. This will be done differently depending on your operating system:

- on Mac OS X, you'll need to find the path to the Praat executable, and not the Praat application package; this means that you have to find Praat and then right-click the Praat icon, choose "Show Package Contents", and then keep looking until you find the actual executable called "praat". On my computer, this is the path to Praat:

	/Applications/Praat/Contents/MacOS/praat
	
- on Windows 7, you'll need a version of Praat that can run Praat scripts without opening Praat itself (the standard Praat executable for Windows can't do this); the file that you'll need is called "praatcon.exe"; you can download it here:

	http://www.fon.hum.uva.nl/praat/download_win.html

You'll need to scroll down and download either the 32-bit version or the 64-bit version under the "The console Praat" heading (you should use the 64-bit one on Windows 7). Just unpack the zip archive and move "praatcon.exe" to a folder where you'll easily find it. I'd recommend the "praat" subfolder within the parent folder for Formant Editor. Depending on where you put your file, the path to "praatcon.exe" will look something like this:

	C:\formant_editor\praat\praatcon.exe

Once you're done with the configuration, Formant Editor should be ready to use. If there are problems with the configuration settings, Formant Editor will let you know (and it won't let you open any files).

3) USING THE EDITOR

a) Opening files

There are two ways you can get data into Formant Editor: either by importing a correctly formatted CSV file, or by opening a formant editor output file (usually with the extension .frd, although this is not obligatory). Section 4 explains how your data should be formatted if you want to import it. For now, you can use the file carl_uw.frd in the "example" folder. [these examples are currently unavailable, due to licensing issues; I'll provide new examples soon] .frd files store formant measurements and various spectrogram/formant reader settings for a list of sound files. They do not store audio data or the original segmentation. If you want to open an .frd file with Formant Editor, all wav files and textgrid files should be available in the same folder where the .frd file is located (they can be saved in subfolders, if that's more convenient). The "example" folder shows you the preferred format for the textgrids (although the textgrids themselves are only used when a CSV file is imported; see section 4). Note that you should never change the names of the original wav and textgrid files. If you do, Formant Editor will not be able to open them.

If your .frd file is successfully opened, you should have a list of files shown to you on the right hand side of the Formant Editor window. You can open any of these files for editing by clicking them.

You can open multiple .frd files at the same time (by selecting multiple files in the Open... dialogue window) as long as they all contain the same types of metadata and each sound file only occurs in one of them. This may be useful when you perform the formant correction on a speaker-by-speaker basis, and then want to join the resulting .frd files into a single file. carl_uw_1.frd and carl_uw_2.frd provide examples of two .frd files that can be joined by opening them at the same time.

b) The spectrogram view

Once you open a sound file from the list, Formant Editor will bring up a spectrogram and a waveform, with segment boundaries showing the area where the formant readings are taken, and circles representing the formant measurements. You can only edit these measurements if the spectrogram is active (you can activate it by clicking on it, or pressing Tab if you're in the file list). Once the spectrogram is activated, you can zoom in or out using the buttons below the spectrogram, or the up/down keys (or the 'n' key if you want to zoom to the selection). You can play sections of the file using the buttons below the spectrogram, or the appropriate shortcuts. You can also select a portion of the sound file for playing.

If you're unhappy with the spectrogram, you can adjust the display settings by changing the values in the box below the spectrogram. Sometimes a window length of 0.025 will make it much easier to see what the values of the formants are. Note that if you change the number of measured formants for a given file, your output CSV file _will not contain the measurements for those formants_. Formant Editor stores the display settings separately for each sound file, and loads the last used settings when you open a sound file. If you want to use the same settings for all the files, just check the "Keep constant" box. Note, however, that when you open a sound file with the keep constant setting on, your previously saved settings for that file will be erased.

If you want to adjust the brightness settings quickly, there are two shortcuts: "b" brightens the spectrogram, while "d" darkens it.

c) Changing the measurements

As a first step, you might want to move the segment boundaries, which you can do simply by clicking on them and dragging them to the appropriate location. If you do that, the formant readings will be automatically recalculated (this may cause the program to pause for a second or two).

The formant readings can be manipulated either manually, or by changing the settings for the Praat formant tracker. These are shown under the "Formant measurements" label. Similarly to the display settings, the settings for the tracker are also saved separately for each sound file. However, you can use the same settings for all files by ticking the "Keep constant" box. Be careful, though: if this setting is on, the formant readings are automatically recalculated for each newly opened sound file, which means that you might lose your manual edits (e.g. if you start going backwards through your list). A better way to pre-specify the formant reader parameters is to set them to the appropriate values before you import a CSV file (see Section 4) -- this way, the same settings will be used for all files, but there will be no automatic overwriting.

This takes us to manual editing, which should only be done once you've found the correct boundaries, and the best formant measurement settings (if you change any of these after you've done some manual editing, you'll lose your edits). You can drag the circles representing the formant measurements up and down. But the most efficient way to edit the formant readings is to redraw them. You can do this by holding the number of the formant that you want to edit (i.e. key 1 for the first formant, key 2 for the second formant, etc.), and simply redrawing the trajectory. Pressing 1/2/3/etc. will also hide the circles, in case they are obscuring some details in the spectrogram.

If you want to hide the circles and boundary markers, just press "h". Pressing it again will bring them back.

If some of the formants are not visible in the spectrogram, you can change the number of measured formants, which means that only the first N formants will be written out into your final csv file.

If you think that a given sound file is useless (e.g. it doesn't actually have the target word), you can discard it by clicking the discard button on the right. Note, however, that this will permanently remove the file from your .frd list. You won't be able to undo this action.

d) Changing the metadata

You may want to change the metadata that you imported from the original CSV file (see Section 4 below for more information about importing CSV files). For instance, some of the annotations may be wrong -- perhaps the speaker is a female, not a male, the preceding sound is wrong, etc. In such cases, you can simply double-click the relevant row in the metadata box, and enter the correct annotations.

In other cases, you might want to add further metadata. For instance, you may want to add narrow IPA transcriptions for each of the files, or show whether the relevant token shows t/d-deletion, etc. You can add metadata fields by clicking "Add" under the metadata box (you can also specify a default value). You can also remove metadata fields, and move them up and down the list (note that the order of metadata fields doesn't matter when you join .frd files, as long as they are all there in the files you want to join).

e) Filtering

You may want to display only a subset of all your files. For example, if you have a large set of words ending in "t" or "d", but you're only interested in t-deletion, you may want to set the d-final words aside. You can do this by filtering your data set based on the metadata fields. Let's assume you have a metadata field that specifies what the last sound of the word is (let's call this field "final_sound"). In order to filter the data set, you would need to click the Filter button, and enter the following filter expression:

	final_sound == "t"

The filter expression relies on Python logical expressions, so you may put together quite complicated filters if you know a bit of Python. Here's another way of restricting your data set to "t"-final words using filters:

	word[-1] == "t" or word[-2:] == "te"

And another option:

	word.endswith("t") or word.endswith("te")

Note that filtering doesn't discard the rest of the tokens. It only determines the range of tokens displayed in the file list on the right. If you want to see all your tokens, leave the filter expression empty.

f) Exporting your measurements

Exporting your measurements is really easy. Just go to the file menu and click on "Export as CSV...". You'll be prompted to choose a file name, and then to specify the number of formant measurements. This is the maximum number of measurements: the number of formants that are written out for a given file may be less if you specified a smaller number while editing that file.

Each measurement point is stored as a separate observation in the CSV file. So if you have 11 measurements for each vowel (i.e. one at 0%, 10%, 20%, etc.), the CSV file will contain 11 rows for each vowel, each row containing the formant values at a specific point in time. The rows include the duration of the entire vowel as well.

4) Creating your own data set

You can create a new project by importing a CSV file, which contains metadata for each sound file. Minimally, this CSV file will contain a single column with a header and a list of all the wav files. This column is obligatory, but you can have other columns as well (as many as you wish). However, you have to make sure that your file is correctly formatted: the rows should be separated by newline characters, and the columns by tab characters; cells containing text should have their contents surrounded by "s (including the column with the names of the wav files). You also need to have a header -- but the names in the header should not be surrounded by "s. The "examples" folder has a representative example named "carl_uw.csv".

When you import the CSV file, Formant Editor will ask you to type in the name of the column containing the names of the sound files. If your CSV file is correctly formatted, it will look for all the wav files you specified (in the same folder as the CSV file - but the individual files can be in subfolders), and generate preliminary formant analyses for each of them. This might take a while, especially if you have a lot of wav files. The formant analyses use the settings in the Formant Reader window (bottom left) -- for instance, if you think that the number of expected formants should be 6 for your speaker, you should change the settings immediately before you import the file. Once the CSV file has been imported, you can save your project (I'd recommend that you use the .frd extension, so that you can easily recognise these files), and you'll be able to reload it in the future.

5) Reporting bugs

This is a development version, which means that it will likely have some bugs or awkward features. If you think you've found a bug, or if you think the program is misbehaving, you should tell Márton Sóskuthy, the author of Formant Editor. Please explain what the problem is exactly, when it occurred and what OS you're using. 

I also welcome recommendations for additional features, but I can't promise 
anything!
