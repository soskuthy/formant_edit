#/applications/praat.app/contents/macos/praat
form Input
	word Wav
	word Folder
	real Start
	real End
endform

Read from file... 'wav$'

Erase all

# create waveform

path$ = folder$ + "/tmp_waveform.eps"
Select inner viewport... 0 6 0 1.5
Draw... start end 0 0 0 0
Select outer viewport... 0 6 0 1.5
Save as EPS file... 'path$'