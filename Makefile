all:
	$(MAKE) -C crawler

clean:
	$(MAKE) -C crawler clean
	rm -rf output/*