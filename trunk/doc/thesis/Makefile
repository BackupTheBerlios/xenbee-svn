NAME=main

SRC=$(NAME).tex
PDF=$(NAME).pdf
IDX=$(NAME).idx
LOG=$(NAME).log
GLS=$(NAME).gls

latex = pdflatex -halt-on-error
bibtex = bibtex
makeindex = makeindex
makeglos = makeglos.pl

SYS_NAME := $(shell uname -s)
viewer = echo "could not open "
ifeq ($(SYS_NAME), Linux)
viewer = gv
endif
ifeq ($(SYS_NAME), Darwin)
ifneq ($(DISPLAY),)
viewer = gv
else
viewer = open
endif
endif

GRAPHICS = $(shell find ./graphics/ -name "*.pdf")
TEX = $(wildcard *.tex)
BIB = $(wildcard *.bib)

default: all
all: $(PDF)

$(PDF): $(SRC) $(GLS) $(GRAPHICS) $(TEX) $(BIB)
	@echo "Running $(latex)..."
	$(latex) $(SRC)
	@echo "Running $(bibtex).."
	$(bibtex) $(NAME)
	@echo "Running $(makeindex)..."
	-$(makeindex) $(IDX)
	@echo "Rerunning latex...."
	$(latex) $(SRC)
	latex_count=2 ; \
	while egrep -s 'Rerun (LaTeX|to get cross-references right|to get citations correct)' $(LOG) && [ $$latex_count -gt 0 ] ;\
	    do \
	      echo "Rerunning latex...." ;\
	      $(latex) $(SRC) ;\
	      latex_count=`expr $$latex_count - 1` ;\
	    done
	if egrep -is 'overful \\hbox' $(LOG); then \
		echo "WARNING: There where overful hboxes:"; \
	fi

main.glo: main.tex
	$(latex) $<

$(GLS): main.glo
#$(makeindex) -t $(NAME).glg -o $@ -s $(NAME).ist $< #$(NAME) -s $(NAME).ist -t $(NAME).glg -o $@ $(NAME).glo
	$(makeglos) $<

view: view-pdf;

view-pdf: $(PDF)
	$(viewer) $<

clean:
	-rm $(PDF) *.idx *.ilg *.ind *.pdfsync \
                   *.aux *.log *.lof *.loa *.lot *.out \
                   *.toc *.bbl *.blg *.thm *.rel *~ 2>/dev/null

.PHONY: default all clean view view-pdf
