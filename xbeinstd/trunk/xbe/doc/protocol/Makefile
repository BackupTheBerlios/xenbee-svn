PRM=protocol.prm

default: run

run: $(PRM).trail
	if test -f $(PRM).trail ; then spin -m -t -r -s -c $(PRM) ; else echo "No errors found."; fi

$(PRM).trail: pan
	./pan

pan: pan.c Makefile
	gcc -o $@ pan.c

pan.c: $(PRM)
	spin -a $<

clean:
	rm -f *.trail
	rm -f pan*
