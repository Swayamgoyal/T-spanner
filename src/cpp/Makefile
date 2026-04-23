# C++ Spanner Implementation — Build System
# 
# Targets:
#   make all     — build all executables
#   make bench   — build with optimization
#   make clean   — remove build artifacts
#   make test    — run quick test
#
# Part of t-Spanner project — Person A

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra
OPTFLAGS = -O2

# Default: optimized build
all: spanner_cpp

spanner_cpp: baswana_sen.cpp
	$(CXX) $(CXXFLAGS) $(OPTFLAGS) -o spanner_cpp baswana_sen.cpp

# Debug build
debug: OPTFLAGS = -g -O0 -DDEBUG
debug: spanner_cpp

# Benchmark build (maximum optimization)
bench: OPTFLAGS = -O3 -march=native
bench: spanner_cpp

# Quick test with a small graph
test: spanner_cpp
	@echo "10 15" > /tmp/test_graph.txt
	@for i in $$(seq 0 9); do \
		for j in $$(seq $$(($$i+1)) 9); do \
			if [ $$(( ($$i + $$j) % 3 )) -eq 0 ]; then \
				echo "$$i $$j 1.0" >> /tmp/test_graph.txt; \
			fi; \
		done; \
	done
	./spanner_cpp --algo baswana --k 2 --verify < /tmp/test_graph.txt
	@echo ""
	./spanner_cpp --algo greedy --t 3 --verify < /tmp/test_graph.txt

clean:
	rm -f spanner_cpp spanner_cpp.exe
	rm -f /tmp/test_graph.txt

.PHONY: all debug bench test clean
