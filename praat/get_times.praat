#/applications/praat.app/contents/macos/praat
form Input
	word Tgrid
endform

Read from file... 'tgrid$'
noi = Get number of intervals... 1
ret$ = ""
for i from 1 to noi
	time = Get start point... 1 i
	ret$ = ret$ + "'time'	"
endfor
time = Get end point... 1 i - 1
ret$ = ret$ + "'time'"
echo 'ret$'