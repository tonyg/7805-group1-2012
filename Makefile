group1.pdf: group1.tex
	pdflatex $<
	pdflatex $<
	pdflatex $<

clean:
	rm -f group1.pdf
	rm -f group1.aux
	rm -f group1.log
