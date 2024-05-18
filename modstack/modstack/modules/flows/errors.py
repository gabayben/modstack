class FlowError(Exception):
    pass

class FlowConnectError(FlowError):
    pass

class NodeNotFound(FlowError):
    pass