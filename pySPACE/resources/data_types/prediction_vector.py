""" 1d array of prediction values with properties (labels, reference to the predictor)

"""

import numpy
from pySPACE.resources.data_types import base


class PredictionVector(base.BaseData):
    """ Represents a prediction vector
    
    It contains a label, a prediction and a reference to the predictor.
    I doesn't matter if it uses one or multiple predictions.
    The object might be even used for regression, where no label is needed.
    In contrast to :class:`~pySPACE.resources.data_types.time_series.TimeSeries`
    or :class:`~pySPACE.resources.data_types.feature_vector.FeatureVector`
    objects, prediction vectors are currently generated in a node chain
    with classifiers for example and not loaded.
    For evaluation the
    :class:`~pySPACE.missions.nodes.sink.classification_performance_sink.PerformanceSinkNode`
    can be used to evaluate the predictions.

    For multiple predictions, nodes from the
    :mod:`~pySPACE.missions.nodes.classification.ensemble`
    module can be used.

    For creating a prediction vector, there are four

    **Parameters**

        :input_array:
            The prediction vector is (for historical reasons) a 2d numpy array
            with some additional (mode important parameters).
            The content of the input_array should be/is the same
            as used in  the *prediction* parameter.
            If you do not specify this parameter, it is generated from
            the *prediction* and vice versa.
            Any object, which can be converted to a 2d-numpy array can be
            used to specify this parameter.

        :label:
            The label normally gives a semantic meaning to the prediction value
            and is a string, e.g., "ill" or "Target".
            For regression this parameter can be ignored and is set to None.
            For multiple predictions, it is a list.

        :prediction:
            For regression, this is the regression value and
            for binary classification it is the prediction value.
            For SVMs it can be any real value and for algorithms
            with probabilistic output it should be the probability
            of the respective data belonging to the second and not the first
            class or vice versa.
            For multiple predictions this is not a single number,
            but a list of floats.
            The prediction value is used to generate the *input_array*
            parameter or vice versa.

        :predictor:
            For accessing special parameters of the decision algorithm,
            this parameter is used (default: None).
            It is typically a pointer to the Node, which created the vector.
            For multiple predictions, a list might be used, which might be
            replaced during the processing by an ensemble classifier.
            One main usage is when reading out additional metrics in the
            evaluation process like convergence behaviour or weights of
            a linear classifier.

    The last 3 parameters are directly to object variables with the same name.
    Currently, the object is by default like an array, with access to
    the different other parameters.
    For future developments, only these parameters should be used.

    .. todo:: Implement a method _generate_tag for BaseData type (if desired)

    .. todo:: Eliminate 2d-array behaviour incl. modifications in some nodes

    :Author: Mario Micheal Krell
    :Created: 2010/07/28
    """
    def __new__(subtype, input_array=None, label=None, prediction=None,
                predictor=None, tag=None, **kwargs):
        """ Create the object including several type mappings """
        # Input array is not an already formed ndarray instance
        # We first cast to be our class type
        if input_array is None:
            if type(prediction) == list:
                input_array = [prediction]
            elif type(prediction) == numpy.ndarray:
                input_array = numpy.atleast_2d(prediction)
            elif prediction is None:
                raise TypeError(
                    "You should at least give a prediction value " +
                    "of 1 or -1 in the input array or the prediction component")
            else:
                if type(prediction) == numpy.float64:
                    pass
                elif type(prediction) == float:
                    prediction = numpy.float64(prediction)
                elif type(prediction) == int or type(prediction) == numpy.int64:
                    prediction *= 1.0
                else:
                    import warnings
                    warnings.warn("Type mismatch in Prediction Vector: %s!"%type(prediction))
                    prediction = float(prediction)
                input_array = [[prediction]]
        if not numpy.isfinite(input_array).all():
            if type(prediction) == list:
                input_array = [0 for i in range(len(prediction))]
            elif prediction > 0:
                prediction = 10**9
                input_array = [[float(prediction)]]
            else:
                prediction = -10**9
                input_array = [[float(prediction)]]

        obj = base.BaseData.__new__(subtype, input_array)

        # add subclasses attributes to the created instance
        # obj.feature_names = ["prediction value"]
        obj.label = label
        obj.predictor = predictor
        
        # using the input array is not necessary any more
        if prediction is None:
            l = list(input_array[0])
            if len(l) == 1:
                obj.prediction = l[0]
            else:
                obj.prediction = l
        else:
            obj.prediction = prediction
        if not tag is None:
            obj.tag = tag
        # Finally, we must return the newly created object:
        return obj
    
    def __array_finalize__(self, obj):
        super(PredictionVector, self).__array_finalize__(obj)
        # set default values for attributes, since normally they are not needed
        # when taking just the values
        if not (obj is None) and not (type(obj) == numpy.ndarray):
            # reset the attributes from passed original object
            self.label = getattr(obj, 'label', None)
            self.predictor = getattr(obj, 'predictor', None)
            self.prediction = getattr(obj, 'prediction', None)
        else:
            self.label = None
            self.predictor = None
            self.prediction = None

    # which is a good printing format? "label, value"?
    def __str__(self):
        str_repr =  ""
        if hasattr(self.label, "__iter__"):
            for label, prediction in zip(self.label, self.prediction):
                str_repr += "%s : %.4f \t" % (label, prediction)
        else: 
            str_repr += "%s : %.4f \t" % (self.label, self.prediction)
        return str_repr
        
    def __reduce__(self):
        """ Refer to 
        http://www.mail-archive.com/numpy-discussion@scipy.org/msg02446.html#
        for infos about pickling ndarray subclasses
        """
        object_state = list(super(PredictionVector, self).__reduce__())
        subclass_state = (self.label, self.predictor, self.prediction)
        object_state[2].append(subclass_state)
        object_state[2] = tuple(object_state[2])
        return tuple(object_state)
    
    def __setstate__(self, state):
        nd_state, base_state, own_state = state
        super(PredictionVector, self).__setstate__((nd_state, base_state))
        
        (self.label, self.predictor, self.prediction) = own_state

    def __eq__(self, other):
        """ Same label and prediction value """
        if type(other) != type(self):
            return False

        return (self.label == other.label and
                numpy.allclose(self.prediction, other.prediction))
