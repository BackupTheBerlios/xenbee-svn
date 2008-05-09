latex=pdflatex
bibtex=bibtex

SRC=main.tex
BIB=main.bib
AUX=$(SRC:.tex=.aux)
PDF=$(SRC:.tex=.pdf)

default: all

all: pdf

pdf: $(PDF)

$(PDF): $(SRC)
	-rm -f $(AUX)
	$(latex) $<
	$(latex) $<

clean:
	-rm -f *~
	-rm -f $(PDF)
	-rm -f $(AUX)
	-rm -f *.log
	-rm -f *.bbl
	-rm -f *.blg

.PHONY: default all clean
