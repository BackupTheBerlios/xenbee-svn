NAME=main

SRC=$(NAME).tex
PDF=$(NAME).pdf
IDX=$(NAME).idx
LOG=$(NAME).log

latex = pdflatex
bibtex = bibtex
makeindex = makeindex

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

INCLUDES=$(wildcard *.tex *.bib)

default: all
all: $(PDF)

$(PDF): $(SRC) $(INCLUDES)
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


view: view-pdf;

view-pdf: $(PDF)
	$(viewer) $<

clean:
	-rm $(PDF) *.idx *.ilg *.ind *.pdfsync \
                   *.aux *.log *.lof *.loa *.lot *.out \
                   *.toc *.bbl *.blg *.thm *.rel *~ 2>/dev/null

.PHONY: default all clean view view-pdf
