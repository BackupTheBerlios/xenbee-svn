PRM=protocol.prm

default: run

run: $(PRM).trail
	spin -m -t -r -s -c $(PRM)

$(PRM).trail: pan
	./pan

pan: pan.c
	gcc -o $@ $<

pan.c: $(PRM)
	spin -a $<

clean:
	rm -f *.trail
	rm -f pan*
