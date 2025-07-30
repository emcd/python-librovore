''' Test utilities for extension manager testing. '''


from pathlib import Path


def get_fake_extension_url():
    ''' Get file:// URL for fake extension package. '''
    fake_extension_path = (
        Path( __file__ ).parent.parent / "fixtures" / "fake-extension" )
    return f"file://{fake_extension_path.absolute()}"

def get_broken_extension_url():
    ''' Get file:// URL for broken extension package. '''
    broken_extension_path = (
        Path( __file__ ).parent.parent / "fixtures" / "broken-extension" )
    return f"file://{broken_extension_path.absolute()}"
