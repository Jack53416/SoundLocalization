cc := gcc
cxxflags := -pedantic -Wall -pthread
libs := -lpigpio -lrt
includes := registers.h spi.h driver.h wavWriter.h ciricularBuffer.h
objects := driver.o spi.o wavWriter.o ciricularBuffer.o
buildDir := build
OBJS := $(addprefix $(buildDir)/, $(objects))

#$< - $(input) - the name of first input file 
#$@ - $(output) - the name of first output file
#$^ - $(inputs) - the name of all input files 

driver: $(OBJS)
	$(cc) $^ -o $@ $(libs) $(cxxflags)

$(buildDir)/%.o: %.c $(includes) | $(buildDir)/
	$(cc) $(cxxflags) -c $< -o $@ 

$(buildDir)/:
	mkdir -p $@

.PHONY: clean

clean:
	rm -f -r driver $(buildDir) 

