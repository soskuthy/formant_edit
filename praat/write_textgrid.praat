#/applications/praat.app/contents/macos/praat
form Input
	word Tgrid
	word Times
	word Labels
endform
temp$ = ""
counter_t = 1
for c from 1 to length(times$)
	char$ = mid$(times$, c, 1)
	if char$ = ","
		times_array[counter_t] = 'temp$'
		counter_t = counter_t + 1
		temp$ = ""
	else
		temp$ = temp$ + char$
	endif
endfor
times_array[counter_t] = 'temp$'
temp$ = ""
counter_l = 1
for c from 1 to length(labels$)
	char$ = mid$(labels$, c, 1)
	if char$ = ","
		labels_array$[counter_l] = temp$
		counter_l = counter_l + 1
		temp$ = ""
	else
		temp$ = temp$ + char$
	endif
endfor
labels_array$[counter_l] = temp$
start = times_array[1]
end = times_array[counter_t]
Create TextGrid... start end labels 
for i from 2 to counter_t - 1
	Insert boundary... 1 times_array[i]
endfor
for i from 1 to counter_l
	txt$ = labels_array$[i]
	Set interval text... 1 i 'txt$'
endfor
Save as text file... 'tgrid$'