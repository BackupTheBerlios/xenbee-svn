PRM=protocol.prm

default: run

run: run_safety run_progress

run_progress: pan_progress
	@echo "Running progress analysis..."
	./$< -v -X -m10000 -w19 -c1
	if test -f $(PRM).trail ; then spin -T -m -t -r -s -c $(PRM) ; else echo "No errors found."; fi
	
run_safety: pan_safety
	@echo "Running safety analysis..."
	./$< -v -X -m10000 -w19 -c1
	if test -f $(PRM).trail ; then spin -T -m -t -r -s -c $(PRM) ; else echo "No errors found."; fi

pan_progress: pan.c Makefile
	gcc -w -o $@ -D_POSIX_SOURCE -DMEMLIM=128 -DNP -DNOCLAIM -DXUSAFE -DNOFAIR pan.c
pan_safety: pan.c Makefile
	gcc -w -o $@ -D_POSIX_SOURCE -DMEMLIM=128 -DSAFETY -DNOCLAIM -DXUSAFE -DNOFAIR pan.c

pan.c: $(PRM)
	spin -a $<

clean:
	rm -f *.trail
	rm -f pan*

.PHONY: clean run run_progress run_safety default
