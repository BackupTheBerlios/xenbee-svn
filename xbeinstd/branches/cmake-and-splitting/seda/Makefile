BUILD_DIR=build
srcdir=${CURDIR}

default: compile
$(BUILD_DIR):
	mkdir $(BUILD_DIR)

compile: config
	make -C $(BUILD_DIR)

config: $(BUILD_DIR) CMakeLists.txt
	cd $(BUILD_DIR) && cmake $(srcdir)

distclean:
	@-rm -r $(BUILD_DIR) 2>/dev/null
	@-find . -name "*~" -delete

.DEFAULT:
	make -C $(BUILD_DIR) $(MAKECMDGOALS)

.PHONY: clean distclean all default
