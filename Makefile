all: group1.pdf

%.pdf: %.tex %.bib
	pdflatex $<
	bibtex $*.aux
	pdflatex $<
	pdflatex $<

clean:
	rm -f group1.pdf
	rm -f group1.aux
	rm -f group1.log
	rm -f group1.bbl
	rm -f group1.blg
