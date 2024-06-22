class FlowRecursionError(RecursionError):
    """Raised when the flow has exhausted the maximum number of steps.

    This prevents infinite loops. To increase the maximum number of steps,
    run your flow with a config specifying a higher `recursion_limit`.

    Examples:

        flow = builder.compile()
        flow.invoke(
            {"messages": [("user", "Hello, world!")]},
            # The config is the second positional argument
            {"recursion_limit": 1000},
        )
    """

    pass