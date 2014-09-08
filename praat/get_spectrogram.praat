#/applications/praat.app/contents/macos/praat
form Input
	word Wav
	word Folder
	real Start
	real End
	real Window_length
	real Max_freq
	real Freq_step
	real Dynamic_range
endform

Open long sound file... 'wav$'
Extract part... start end 0
Erase all

time_step = (end - start) / 1000

# create spectrogram

path$ = folder$ + "/tmp_spectrogram.eps"
Select inner viewport... 0 6 0 3
To Spectrogram... window_length max_freq time_step freq_step Gaussian
Paint... 0 0 0 0 100 1 dynamic_range 6.0 0.0 0
Select outer viewport... 0 6 0 3
Save as EPS file... 'path$'