from app.services.logger import setup_logger
from app.services.schemas import TextRewriterArgs

from app.tools.text_rewriter.tools import Rewrite_Text
from app.api.error_utilities import TextRewriterError



import os
from dotenv import load_dotenv, find_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "../../../.env/.env")
load_dotenv(dotenv_path=dotenv_path)
api_key = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = api_key




logger = setup_logger()

def executor(input_text: str,
             file_url: str,
             file_type: str,
             rewrite_instructions: str,
             lang: str,
             verbose: bool = True):
    
    if verbose:
        # TODO: Need to correct this log info e.g. currently it displays file_url even when only input_text & rewrite_ins is provided
        logger.info(f"Loading File: {file_url}")
    try:
        
        text_rewriter_args = TextRewriterArgs(
            input_text=input_text,
            file_url=file_url,
            file_type=file_type,
            rewrite_instructions=rewrite_instructions,
            lang=lang
        )

        output = Rewrite_Text(text_rewriter_args, verbose=verbose).generate()

        logger.info(f"Successfully generated re-written text")
    
    except Exception as e:
        logger.error(f"Failed to generate Re-written Text: {str(e)}")
        raise TextRewriterError(f"Failed to generate Re-written Text: {str(e)}") from e
    
    return output