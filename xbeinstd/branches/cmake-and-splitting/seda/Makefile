BUILD_DIR=build

default: compile
$(BUILD_DIR):
	mkdir $(BUILD_DIR)

compile: config
	make -C $(BUILD_DIR)

config: $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake ..

distclean:
	@-rm -r $(BUILD_DIR) 2>/dev/null
	@-find . -name "*~" -delete

.DEFAULT:
	make -C $(BUILD_DIR) $(MAKECMDGOALS)

.PHONY: clean distclean all default
