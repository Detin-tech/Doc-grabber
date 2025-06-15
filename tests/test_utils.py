import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location('utils', pathlib.Path(__file__).parent.parent / 'doc-tool' / 'utils.py')
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)

def test_domain_to_folder_simple():
    assert utils.domain_to_folder('https://example.com/docs') == 'example_com'

def test_domain_to_folder_subdomain():
    assert utils.domain_to_folder('http://sub.domain.co.uk/') == 'sub_domain_co_uk'
