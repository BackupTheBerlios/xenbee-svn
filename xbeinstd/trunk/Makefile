subdirs=seda mqs xbe

default: $(subdirs)

$(subdirs):
	make -C $@ $(MAKECMDGOALS)

.DEFAULT:
	@for d in $(subdirs); do \
		make -C $$d $(MAKECMDGOALS); \
	done

.PHONY: clean distclean all default $(subdirs)
