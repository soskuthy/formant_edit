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
	f1 = Get value at time... 1 t Hertz Linear
	f2 = Get value at time... 2 t Hertz Linear
	f3 = Get value at time... 3 t Hertz Linear
	f4 = Get value at time... 4 t Hertz Linear
	f5 = Get value at time... 5 t Hertz Linear
	print 'f1'	'f2'	'f3'	'f4'	'f5''newline$'
endfor

