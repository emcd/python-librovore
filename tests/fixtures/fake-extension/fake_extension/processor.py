''' Fake processor implementation for testing. '''

class FakeProcessor:
    ''' Mock processor that simulates basic extension functionality. '''

    def __init__( self, arguments ):
        self.arguments = arguments
        self.processed_count = 0

    def process( self, content ):
        ''' Mock processing that adds a test marker. '''
        self.processed_count += 1
        return f"[FAKE-PROCESSED] {content}"

    def get_stats( self ):
        ''' Return processing statistics for testing. '''
        return {
            'arguments': self.arguments,
            'processed_count': self.processed_count
        }