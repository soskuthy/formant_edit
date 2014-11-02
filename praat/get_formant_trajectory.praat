#/applications/praat.app/contents/macos/praat
form Input
	word Wav
	real Start
	real End
	integer Number_of_measurements
	integer Number_of_formants
	positive Maximum_formant
	positive Window_length
	positive Pre_emph
endform

Open long sound file... 'wav$'
dur = Get total duration
start_p_s = start - (window_length * 2)
end_p_s = end + (window_length * 2)
if start_p_s < 0
	start_p_s = 0
endif
if end_p_s > dur
	end_p_s = dur
endif

Extract part... start_p_s end_p_s 1
time_step =  (end - start) / (number_of_measurements + 2)
To Formant (burg)... time_step number_of_formants maximum_formant window_length pre_emph

incr = (end - start) / (number_of_measurements - 1)
for i from 0 to number_of_measurements - 1
	t = start + incr * i
	for j from 1 to 10
		f = Get value at time... j t Hertz Linear
		print 'f''tab$'
	endfor
	print 'newline$'
endfor

