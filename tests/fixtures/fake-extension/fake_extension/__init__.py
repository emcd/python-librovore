''' Fake extension package for testing extension manager functionality. '''

def register( arguments ):
    ''' Register the fake processor with given arguments. '''
    from .processor import FakeProcessor
    return FakeProcessor( arguments )