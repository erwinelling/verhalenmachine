from verhalenmachine.uploader import Uploader
from verhalenmachine.log import setup_custom_logger
logger = setup_custom_logger('root')

uploader = Uploader()
uploader.clean_directory()
uploader.upload_directory()
