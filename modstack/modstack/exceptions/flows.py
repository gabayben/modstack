class FlowError(Exception):
    pass

class FlowRuntimeError(Exception):
    pass

class FlowConnectError(FlowError):
    pass

class FlowValidationError(FlowError):
    pass

class FlowDrawingError(FlowError):
    pass

class FlowMaxLoops(FlowError):
    pass

class FlowUnmarshalError(FlowError):
    pass

class NodeError(Exception):
    pass

class NodeDeserializationError(Exception):
    pass