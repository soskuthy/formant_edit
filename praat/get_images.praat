#/applications/praat.app/contents/macos/praat
form Input
	word Wav
        word Textgrid
	word Tmp
	real Window_length
	real Max_freq
	real Time_step
	real Freq_step
	real Din_range
endform

Read from file... 'wav$'

# create waveform

path$ = tmp$ + "/tmp_waveform.eps"
Select inner viewport... 0 6 0 1.5
Draw... 0 0 0 0 0 0
Select outer viewport... 0 6 0 1.5
Save as EPS file... 'path$'

# create spectrogram

path$ = tmp$ + "/tmp_spectrogram.eps"
Select inner viewport... 0 6 0 3
To Spectrogram... window_length max_freq time_step freq_step Gaussian
Paint... 0 0 0 0 100 1 din_range 6.0 0.0 0
Select outer viewport... 0 6 0 3
Save as EPS file... 'path$'