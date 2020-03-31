import sys
import os

import matplotlib.pyplot as plt

import ..utils.utilities
import ..utils.metrics
import ..utils.models
import ..utils.modelFuncs
import ..utils.plots
import ..utils.prints
import ..utils.analysis

import numpy as np
import tensorflow as tf

np.random.seed(100)
tf.random.set_seed(100)

_filename = None
_names = None
_descriptions = None
_units = None
_relevantColumns = None
_columnDescriptions = None
_columnUnits = None
_columnNames = None
_df = None
_traintime = None
_testtime = None
_df_train = None
_df_test = None
_targetColumns = None
_modelList = None
_X_train = None
_y_train = None
_X_test = None
_y_test = None
_maxEnrolWindow = None
_indexColumn = None

_default_MLP_args = {
    'activation': 'relu',
    'loss': 'mean_squared_error',
    'optimizer': 'adam',
    'metrics': ['mean_squared_error'],
    'epochs': 1000,
    'batchSize': 64,
    'verbose': 1,
    'callbacks': modelFuncs.getBasicCallbacks(patience_es=150, patience_rlr=100),
    'enrolWindow': 0,
    'validationSize': 0.2,
    'testSize': 0.2,
}

_default_LSTM_args = {
    'activation': 'tanh',
    'loss': 'mean_squared_error',
    'optimizer': 'adam',
    'metrics': ['mean_squared_error'],
    'epochs': 500,
    'batchSize': 128,
    'verbose': 1,
    'callbacks': modelFuncs.getBasicCallbacks(patience_es=75, patience_rlr=50),
    'enrolWindow': 32,
    'validationSize': 0.2,
    'testSize': 0.2,
}

def initDataframe(filename, columns, irrelevantColumns):
    """
    FUNCTION:
        Used to initiate a pandas dataframe from file and provided metadata
    
    PARAMS:
        filename: str
            location of dataset file on disk in .csv format
        columns: List of list of column data
            Provided metadata of column names, column descriptions and column units
        irrelevantColumns: List of strings
            columnNames excluded from the dataset
    
    RETURNS:
        df: Pandas dataframe
            Dataframe generated from file and metadata
    """
    global _filename, _relevantColumns, _columnDescriptions, _columnUnits, _columnNames, _df

    columnNames = list(map(lambda el: el[0], columns))
    descriptions = list(map(lambda el: el[1], columns))
    units = list(map(lambda el: el[2], columns))

    relevantColumns = list(filter(lambda col: col not in irrelevantColumns, map(lambda el: el[0], columns)))
    columnUnits = dict(zip(columnNames, units))
    columnDescriptions = dict(zip(columnNames, descriptions))

    _filename = filename
    _relevantColumns = relevantColumns
    _columnDescriptions = columnDescriptions
    _columnUnits = columnUnits
    _columnNames = columnNames
    
    df = utilities.initDataframe(
        filename,
        relevantColumns,
        columnDescriptions,
    )

    _df = df

    return df

def getTestTrainSplit(traintime, testtime):
    """
    FUNCTION:
        Used to split training and testing rows into separate data frames
    
    PARAMS:
        traintime: List of list of string pairs
            start and end times indicating periods used for training
        testtime: List of string pair
            start and end time indicating period used for testing
            preferably the entire period of the dataset
    
    RETURNS:
        List[df_train, df_test]: [Pandas dataframe, Pandas dataframe]
            Dataframes of training and testing dataset rows
    """
    global _traintime, _testtime, _df, _df_train, _df_test

    _traintime = traintime
    _testtime = testtime

    df_train, df_test = utilities.getTestTrainSplit(
        _df,
        traintime,
        testtime,
    )

    _df_train = df_train
    _df_test = df_test

    return [df_train, df_test]

def getFeatureTargetSplit(targetColumns):
    """
    FUNCTION:
        Used to split feature and target columns into separate arrays
    
    PARAMS:
        targetColumns: List of strings
            names of columns present in the dataset used as output(target) values
    
    RETURNS:
        List[X_train, y_train, X_test, y_test]: [Numpy array, Numpy array, Numpy array, Numpy array]
            Arrays of feature and target values for training and testing
    """
    global _targetColumns, _X_train, _y_train, _X_test, _y_test

    _targetColumns = targetColumns

    X_train, y_train, X_test, y_test =  utilities.getFeatureTargetSplit(
        _df_train,
        _df_test,
        targetColumns,
    )

    _X_train = X_train
    _y_train = y_train
    _X_test = X_test
    _y_test = y_test

    return [X_train, y_train, X_test, y_test]

def prepareDataframe(df, traintime, testtime, targetColumns):
    """
    FUNCTION:
        Combination of getTestTrainingSplit and getFeatureTargetSplit
        Used for even higher level programs where df_train and df_test are not needed
    
    PARAMS:
        df: Pandas dataframe
            dataframe generated from provided metadata
        traintime: List of list of string pairs
            start and end times indicating periods used for training
        testtime: List of string pair
            start and end time indicating period used for testing
            preferably the entire period of the dataset
        targetColumns: List of strings
            names of columns present in the dataset used as output(target) values
    
    RETURNS:
        List[X_train, y_train, X_test, y_test]: [Numpy array, Numpy array, Numpy array, Numpy array]
            Arrays of feature and target values for training and testing
    """

    df_train, df_test = getTestTrainSplit(
        df,
        traintime,
        testtime,
    )

    return getFeatureTargetSplit(
        df_train,
        df_test,
        targetColumns,
    )

def initModels(modelList):
    """
    FUNCTION:
        Used to initiate the provided models by calculating required model parameters
    
    PARAMS:
        modelList: list of MachineLearningModel/EnsembleModel objects
            The models used to make predictions
    
    RETURNS:
        None
    """
    global _maxEnrolWindow, _indexColumn, _modelList, _df_test

    _maxEnrolWindow = utilities.findMaxEnrolWindow(modelList)
    _indexColumn = _df_test.iloc[_maxEnrolWindow:].index
    _modelList = modelList

def trainModels(retrain=False):
    """
    FUNCTION:
        Used to train the models previously provided in the initModels method
    
    PARAMS:
        retrain: boolean
            Indicates if the program should prefer to load existing models where possible
    
    RETURNS:
        None
    """
    global _modelList, _filename, _targetColumns

    modelFuncs.trainModels(
        _modelList,
        _filename,
        _targetColumns,
        retrain
    )

def predictWithModelsUsingDropout(numberOfPredictions=20):
    """
    FUNCTION:
        Used to make predictions with RNN models using dropout
        at predict time. Requires that the provided models
        have training=True, otherwise mean and std will be zero
    
    PARAMS:
        numberOfPredictions: int
            How many predictions to average in the result
    
    RETURNS:
        List[predictions, means, standarddevs]: [list(float), list(float), list(float)]
            Lists containing the predicted values and their means and stds
    """
    global _modelList, _X_test, _y_test

    return utilities.predictMultipleWithModels(
        _modelList,
        _X_test,
        _y_test,
        numberOfPredictions,
    )

def predictWithModels(plot=True, interpol=False):
    """
    FUNCTION:
        Used to make predictions using previously defined models
    
    PARAMS:
        plot: boolean
            Indicates if plots of the calculated predictions are desired
        interpol: boolean
            Indicates if interpolated functions for predictions should be plotted
    
    RETURNS:
        List[modelNames, metrics_train, metrics_test]: [list(Str), list(float), list(float)]
            Lists containing the names and train/test scores of the provided models
    """
    global _modelList, _X_train, _y_train, _X_test, _y_test, _targetColumns, _indexColumn, _columnDescriptions, _columnUnits, _traintime

    modelNames, metrics_train, metrics_test, deviationsList, columnsList = utilities.predictWithModels(
        _modelList,
        _X_train,
        _y_train,
        _X_test,
        _y_test,
        _targetColumns 
    )

    if plot:
        prints.printModelScores(
            modelNames,
            metrics_train,
            metrics_test
        )
        plots.plotModelPredictions(
            plt,
            deviationsList,
            columnsList,
            _indexColumn,
            _columnDescriptions,
            _columnUnits,
            _traintime,
            interpol=interpol,
        )
        plots.plotModelScores(
            plt,
            modelNames,
            metrics_train,
            metrics_test
        )

    return [modelNames, metrics_train, metrics_test, columnsList, deviationsList]

def predictWithAutoencoderModels():
    """
    FUNCTION:
        Used to make predictions in the case where all
        models in self.modelList are of type AutoencoderModel
    """
    global _modelList, _df_test, _X_test

    utilities.predictWithAutoencoderModels(
        _modelList,
        _df_test,
        _X_test
    )

def MLP(
        name,
        layers=[128],
        dropout=None,
        l1_rate=0.0,
        l2_rate=0.0,
        activation=_default_MLP_args['activation'],
        loss=_default_MLP_args['loss'],
        optimizer=_default_MLP_args['optimizer'],
        metrics=_default_MLP_args['metrics'],
        epochs=_default_MLP_args['epochs'],
        batchSize=_default_MLP_args['batchSize'],
        verbose=_default_MLP_args['verbose'],
        validationSize=_default_MLP_args['validationSize'],
        testSize=_default_MLP_args['testSize'],
        callbacks=_default_MLP_args['callbacks'],
    ):
    """
    FUNCTION:
        Used to create a Neural Network model using multilayer perceptron
    
    PARAMS:
        name: str
            A name/alias given to the model by the user
        layers: list of integers
            List of neuron size for each layer
        dropout: float
            Level of dropout regularization
        l1_rate: float
            Level of l1 (Lasso) regularization
        l2_rate: float
            Level of l2 (Ridge) regularization

    RETURNS:
        model: MachineLearningModel
            Object with typical machine learning methods like train, predict etc.
    """
    global _X_train, _y_train, _default_MLP_args

    mlpLayers = []
    for layerSize in layers:
        mlpLayers.append([layerSize, activation])

    model = models.kerasMLP(
        params = {
            'name': name,
            'X_train': _X_train,
            'y_train': _y_train,
            'args': {
                'activation': activation,
                'loss': loss,
                'optimizer': optimizer,
                'metrics': metrics,
                'epochs': epochs,
                'batchSize': batchSize,
                'verbose': verbose,
                'callbacks': callbacks,
                'enrolWindow': 0,
                'validationSize': validationSize,
                'testSize': testSize,
            },
        },
        structure = mlpLayers,
        dropout = dropout,
        l1_rate = l1_rate,
        l2_rate = l2_rate,
    )

    return model

def LSTM(
    name,
    layers=[128],
    dropout=0.0,
    recurrentDropout=0.0,
    alpha=None,
    training=False,
    enrolWindow=_default_LSTM_args['enrolWindow'],
    activation=_default_LSTM_args['activation'],
    loss=_default_LSTM_args['loss'],
    optimizer=_default_LSTM_args['optimizer'],
    metrics=_default_LSTM_args['metrics'],
    epochs=_default_LSTM_args['epochs'],
    batchSize=_default_LSTM_args['batchSize'],
    verbose=_default_LSTM_args['verbose'],
    validationSize=_default_LSTM_args['validationSize'],
    testSize=_default_LSTM_args['testSize'],
    callbacks=_default_LSTM_args['callbacks'],
    ):
    """
    FUNCTION:
        Used to create a Recurrent Neural Network model using
        Long-Short Term Memory neurons (LSTM). Uses 
        traditional dropout as regularization method
    
    PARAMS:
        name: str
            A name/alias given to the model by the user
        layers: list of integers
            List of neuron size for each layer
        dropout: float
            Level of dropout
        recurrentDropout: float
            Level of recurrent dropout
        alpha: float
            Alpha of the leaky relu function
        enrolWindow: int
            Number of samples used to make each prediction
    
    RETURNS:
        model: MachineLearningModel
            Object with typical machine learning methods like train, predict etc.
    """
    global _X_train, _y_train, _default_LSTM_args

    model = models.kerasLSTM(
        params = {
            'name': name,
            'X_train': _X_train,
            'y_train': _y_train,
            'args': {
                'activation': activation,
                'loss': loss,
                'optimizer': optimizer,
                'metrics': metrics,
                'epochs': epochs,
                'batchSize': batchSize,
                'verbose': verbose,
                'callbacks': callbacks,
                'enrolWindow': enrolWindow,
                'validationSize': validationSize,
                'testSize': testSize,
            },
        },
        layers=layers,
        dropout=dropout,
        recurrentDropout=recurrentDropout,
        alpha=alpha,
        training=training,
    )
    
    return model

def GRU(
    name,
    layers=[128],
    dropout=0.0,
    recurrentDropout=0.0,
    alpha=None,
    training=False,
    enrolWindow=_default_LSTM_args['enrolWindow'],
    activation=_default_LSTM_args['activation'],
    loss=_default_LSTM_args['loss'],
    optimizer=_default_LSTM_args['optimizer'],
    metrics=_default_LSTM_args['metrics'],
    epochs=_default_LSTM_args['epochs'],
    batchSize=_default_LSTM_args['batchSize'],
    verbose=_default_LSTM_args['verbose'],
    validationSize=_default_LSTM_args['validationSize'],
    testSize=_default_LSTM_args['testSize'],
    callbacks=_default_LSTM_args['callbacks'],
    ):
    """
    FUNCTION:
        Used to create a Recurrent Neural Network model using
        Long-Short Term Memory neurons (LSTM). Uses 
        traditional dropout as regularization method
    
    PARAMS:
        name: str
            A name/alias given to the model by the user
        layers: list of integers
            List of neuron size for each layer
        dropout: float
            Level of dropout
        recurrentDropout: float
            Level of recurrent dropout
        alpha: float
            Alpha of the leaky relu function
        enrolWindow: int
            Number of samples used to make each prediction
    
    RETURNS:
        model: MachineLearningModel
            Object with typical machine learning methods like train, predict etc.
    """
    global _X_train, _y_train, _default_LSTM_args

    model = models.kerasGRU(
        params = {
            'name': name,
            'X_train': _X_train,
            'y_train': _y_train,
            'args': {
                'activation': activation,
                'loss': loss,
                'optimizer': optimizer,
                'metrics': metrics,
                'epochs': epochs,
                'batchSize': batchSize,
                'verbose': verbose,
                'callbacks': callbacks,
                'enrolWindow': enrolWindow,
                'validationSize': validationSize,
                'testSize': testSize,
            },
        },
        layers=layers,
        dropout=dropout,
        recurrentDropout=recurrentDropout,
        alpha=alpha,
        training=training,
    )
    
    return model

def Linear(name):
    """
    FUNCTION:
        Used to create a Linear Machine Learning model
    
    PARAMS:
        name: str
            A name/alias given to the model by the user
    
    RETURNS:
        model: MachineLearningModel
            Object with typical machine learning methods like train, predict etc.
    """
    global _X_train, _y_train

    model = models.sklearnLinear(
        params={
            'name': name,
            'X_train': _X_train,
            'y_train': _y_train,
        },
    )

    return model

def Linear_Regularized(name):
    """
    FUNCTION:
        Used to create a Linear Machine Learning model with built-in
        regularization and cross validation
    
    PARAMS:
        name: str
            A name/alias given to the model by the user
    
    RETURNS:
        model: MachineLearningModel
            Object with typical machine learning methods like train, predict etc.
    """
    global _X_train, _y_train

    model = models.sklearnRidgeCV(
        params={
            'name': name,
            'X_train': _X_train,
            'y_train': _y_train,
        },
    )

    return model

def Ensemble(name, modelList):
    """
    FUNCTION:
        Used to create an Ensemble model, combining the prediction
        of n>1 machine learning methods using a linear regressor
    
    PARAMS:
        name: str
            A name/alias given to the model by the user
        modelList: list of MachineLearningModel objects
            A list of machine learning models used to construct the Ensemble model
    
    RETURNS:
        model: EnsembleModel
            Ensemble model object which behaves the same as any other MachineLearningModel
    """
    global _X_train, _y_train

    model = models.ensembleModel(
        params={
            'name': name,
            'X_train': _X_train,
            'y_train': _y_train,
        },
        models=modelList,
    )

    return model

def Autoencoder_Regularized(
        name,
        l1_rate=10e-4,
        encodingDim=3,
        activation=_default_MLP_args['activation'],
        loss=_default_MLP_args['loss'],
        optimizer=_default_MLP_args['optimizer'],
        metrics=_default_MLP_args['metrics'],
        epochs=_default_MLP_args['epochs'],
        batchSize=_default_MLP_args['batchSize'],
        verbose=_default_MLP_args['verbose'],
        validationSize=_default_MLP_args['validationSize'],
        testSize=_default_MLP_args['testSize'],
        callbacks=_default_MLP_args['callbacks'],
    ):
    """
    FUNCTION:
        Used to create an Autoencoder model using multilayer perceptron
        and reguarlization by Lasso regluarization
        NB: Autoencoder models SHOULD NOT and CAN NOT
            be used together with other models, or
            as submodels to Ensemble models
    
    PARAMS:
        name: str
            A name/alias given to the model by the user
        l1_rate: float
            Level of L1 regularization
        encodingDim: int
            Size of autoencoder middle layer
    
    RETURNS:
        model: AutoencoderModel
            Object with typical machine learning methods like train, predict etc.
    """
    global _X_train, _default_MLP_args

    model = models.autoencoder_Regularized(
        params = {
            'name': name,
            'X_train': _X_train,
            'args': {
                'activation': activation,
                'loss': loss,
                'optimizer': optimizer,
                'metrics': metrics,
                'epochs': epochs,
                'batchSize': batchSize,
                'verbose': verbose,
                'callbacks': callbacks,
                'enrolWindow': 0,
                'validationSize': validationSize,
                'testSize': testSize,
            },
        },
        l1_rate=l1_rate,
        encodingDim=encodingDim,
    )
    
    return model

def Autoencoder_Dropout(
        name,
        dropout=0.0,
        encodingDim=3,
        activation=_default_MLP_args['activation'],
        loss=_default_MLP_args['loss'],
        optimizer=_default_MLP_args['optimizer'],
        metrics=_default_MLP_args['metrics'],
        epochs=_default_MLP_args['epochs'],
        batchSize=_default_MLP_args['batchSize'],
        verbose=_default_MLP_args['verbose'],
        validationSize=_default_MLP_args['validationSize'],
        testSize=_default_MLP_args['testSize'],
        callbacks=_default_MLP_args['callbacks'],
    ):
    """
    FUNCTION:
        Used to create an Autoencoder model using multilayer perceptron
        and reguarlization by Lasso regluarization
        NB: Autoencoder models SHOULD NOT and CAN NOT
            be used together with other models, or
            as submodels to Ensemble models
    
    PARAMS:
        name: str
            A name/alias given to the model by the user
        dropout: float
            Level of dropout
        encodingDim: int
            Size of autoencoder middle layer
    
    RETURNS:
        model: AutoencoderModel
            Object with typical machine learning methods like train, predict etc.
    """
    global _X_train, _default_MLP_args

    model = models.autoencoder_Dropout(
        params = {
            'name': name,
            'X_train': _X_train,
            'args': {
                'activation': activation,
                'loss': loss,
                'optimizer': optimizer,
                'metrics': metrics,
                'epochs': epochs,
                'batchSize': batchSize,
                'verbose': verbose,
                'callbacks': callbacks,
                'enrolWindow': 0,
                'validationSize': validationSize,
                'testSize': testSize,
            },
        },
        dropout=dropout,
        encodingDim=encodingDim,
    )
    
    return model

def correlationMatrix(df):
    return analysis.correlationMatrix(df)

def pca(df, numberOfComponents, relevantColumns=None, columnDescriptions=None):
    return analysis.pca(df, numberOfComponents, relevantColumns, columnDescriptions)

def pcaPlot(df, timestamps=None):
    return analysis.pcaPlot(df, timestamps)

def pcaDuoPlot(df_train, df_test_1, df_test_2, plotTitle=None):
    return analysis.pcaDuoPlot(df_train, df_test_1, df_test_2, plotTitle)

def pairplot(df):
    return analysis.pairplot(df)

def scatterplot(df):
    return analysis.scatterplot(df)

def correlationPlot(df, title="Correlation plot"):
    return analysis.correlationPlot(df, title)

def correlationDuoPlot(df1, df2, title1="Correlation plot 1", title2="Correlation plot 2"):
    return analysis.correlationDuoPlot(df1, df2, title1, title2)

def correlationDifferencePlot(df1, df2, title="Correlation difference plot"):
    return analysis.correlationDifferencePlot(df1, df2, title)

def valueDistribution(df, traintime, testtime):
    return analysis.valueDistribution(df, traintime, testtime)

def printCorrelationMatrix(covmat, df, columnNames=None):
    return prints.printCorrelationMatrix(covmat, df, columnNames)

def printExplainedVarianceRatio(pca):
    return prints.printExplainedVarianceRatio(pca)

def reset():
    global _filename, _names, _descriptions, _units, _relevantColumns, _columnDescriptions, _columnUnits, _columnNames, _df, _traintime, _testtime, _df_train, _df_test, _targetColumns, _modelList, _X_train, _y_train, _X_test, _y_test, _maxEnrolWindow, _indexColumn
    _filename = None
    _names = None
    _descriptions = None
    _units = None
    _relevantColumns = None
    _columnDescriptions = None
    _columnUnits = None
    _columnNames = None
    _df = None
    _traintime = None
    _testtime = None
    _df_train = None
    _df_test = None
    _targetColumns = None
    _modelList = None
    _X_train = None
    _y_train = None
    _X_test = None
    _y_test = None
    _maxEnrolWindow = None
    _indexColumn = None

def getCallbacks(patience_es, patience_rlr):
    return modelFuncs.getBasicCallbacks(patience_es=patience_es, patience_rlr=patience_rlr)

def setMLPCallbacks(patience_es, patience_rlr):
    global _default_MLP_args
    _default_MLP_args['callbacks'] = modelFuncs.getBasicCallbacks(patience_es=patience_es, patience_rlr=patrience_rlr)

def setLSTMCallbacks(patience_es, patience_rlr):
    global _default_LSTM_args
    _default_LSTM_args['callbacks'] = modelFuncs.getBasicCallbacks(patience_es=patience_es, patience_rlr=patrience_rlr)