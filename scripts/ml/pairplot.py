import sys
import os

import time
import numpy as np
import ..utils.utilities
import ..utils.prints
import ..utils.analysis
import pandas as pd
import matplotlib.pyplot as plt
from ..utils.configs import getConfig
from sklearn import decomposition

def main(filename):
    df = utilities.readDataFile(filename)
    df = utilities.getDataWithTimeIndex(df)
    df = df.dropna()

    subdir = filename.split('/')[-2]
    columns, relevantColumns, labelNames, columnUnits, timestamps = getConfig(subdir)

    if relevantColumns is not None:
        df = utilities.dropIrrelevantColumns(df, [relevantColumns, labelNames])

    analysis.pairplot(df)

pyName = "pairplot.py"
arguments = [
    "- file name (string)",
]

# usage: python src/ml/analysis/pca.py datasets/subdir/filename.csv nrOfComponents
if __name__ == "__main__":
    start_time = time.time()
    prints.printEmptyLine()
    
    print("Running", pyName)
    print("Plots 2D pair plots of dataset columns")
    prints.printEmptyLine()

    try:
        filename = sys.argv[1]
    except IndexError:
        print(pyName, "was called with inappropriate arguments")
        print("Please provide the following arguments:")
        for argument in arguments:
            print(argument)
        sys.exit()

    main(filename)

    prints.printEmptyLine()
    print("Running of", pyName, "finished in", time.time() - start_time, "seconds")
    prints.printEmptyLine()