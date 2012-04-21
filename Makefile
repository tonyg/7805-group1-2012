all: group1.pdf

%.pdf: %.tex %.bib
	pdflatex $<
	bibtex $*.aux
	pdflatex $<

clean:
	rm -f group1.pdf
	rm -f group1.aux
	rm -f group1.log
