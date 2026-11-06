Data from Randi et al. 2022. 
- exported_data_full.tar.gz contains the files readable by our Python libraries (github.com/leiferlab/pumpprobe, github.com/leiferlab/wormdatamodel,github.com/leiferlab/wormbrain), including all the fits and the high-level analysis. See note below when using this version of the data.
- exported_data contains plain txt files containing the basic results for the wild-type background animals
- exported_data_unc31 contains plain txt files containing the basic results for the unc-31 mutant animals
- fitted functional connectivity kernels are available in a simplified format also in the repository github.com/leiferlab/worm-functional-connectivity, which can also be used from the web-app funsim.princeton.edu

When using exported_data_full.tar.gz: After installing the libraries, extract the archive, and then run the script pumpprobe/scripts/adjust_paths.py, following the instruction inside that script. This will adjust some paths stored inside the files to the location on your computer.