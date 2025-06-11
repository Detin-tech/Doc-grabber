from urllib.parse import urlparse

def domain_to_folder(url):
    domain = urlparse(url).netloc
    # Replace dots and slashes with underscores
    folder_name = domain.replace('.', '_').replace('/', '_')
    return folder_name
