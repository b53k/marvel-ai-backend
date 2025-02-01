from app.services.logger import setup_logger
from langchain_google_genai import GoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
import os

from langchain_core.prompts import PromptTemplate
from langchain.document_loaders import PyPDFLoader, TextLoader, CSVLoader, Docx2txtLoader, UnstructuredPowerPointLoader, UnstructuredURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = setup_logger(__name__)

def read_text_file(file_path):
    # Get the directory containing the script file
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Combine the script directory with the relative file path
    absolute_file_path = os.path.join(script_dir, file_path)

    with open(absolute_file_path, 'r') as file:
        return file.read()


class Rewrite_Text:
    def __init__(self, args=None, vectorstore_class=Chroma, embedding_model=None, model=None, verbose=False):
        default_config = {
            "model": GoogleGenerativeAI(model="gemini-1.5-flash"),
            "embedding_model": GoogleGenerativeAIEmbeddings(model='models/embedding-001'),
            "prompt": read_text_file("prompt/text-rewriter-prompt.txt"),
            "vectorstore_class": Chroma
        }
        self.args = args
        self.vectorstore_class = vectorstore_class or default_config["vectorstore_class"]
        self.embedding_model = embedding_model or default_config["embedding_model"]
        self.model = model or default_config["model"]
        self.verbose = verbose

        self.prompt_template_text = default_config["prompt"]

    
    def _load_content(self):

        try:
            if self.args.input_text:
                return self.args.input_text
            
            if self.args.file_url:
                logger.info(f"Loading content from URL: {self.args.file_url}")
                loader = UnstructuredURLLoader([self.args.file_url])
                return loader.load()[0].page_content
            
            if self.args.file_type.lower() in ["csv", "pdf", "docx", "ppt" "pptx", "txt"]:
                logger.info(f"Loading content from uploaded file of type: {self.args.file_type}")

                if self.args.file_type == "txt":
                    loader = TextLoader(self.args.file_url, encoding="UTF-8")
                    content = loader.load()[0].page_content
                
                elif self.args.file_type == "pdf":
                    loader = PyPDFLoader(self.args.file_url)
                    content = [doc.page_content for doc in loader.load()]
                    content = " ".join(content)
                
                elif self.args.file_type == "docx":
                    loader = Docx2txtLoader(self.args.file_url)
                    content = loader.load()[0].page_content
                
                elif self.args.file_type == "pptx" or self.args.file_type == "ppt":
                    loader = UnstructuredPowerPointLoader(self.args.file_url)
                    content = loader.load()[0].page_content
                
                elif self.args.file_type == "csv":
                    loader = CSVLoader(self.args.file_url)
                    content = [doc.page_content for doc in loader.load()]
                    content = " ".join(content)
                
                else:
                    logger.info(f"Unsupported file type: {self.args.file_type}")
                    raise ValueError(f"Unsupported file type: {self.args.file_type}")
            
                return content
        
        except Exception as e:
            logger.info(f"Failed to load content: {str(e)}")
            raise e

            

    def generate(self):
        logger.info(f"Generating re-written text...")

        try:
            content = self._load_content()

            prompt_template = PromptTemplate(template=self.prompt_template_text,
                                            input_variables=["context", "rewrite_instructions", "language"])
            
            prompt = prompt_template.format(
                context = content,
                rewrite_instructions = self.args.rewrite_instructions,
                language = self.args.lang
            )

            response = self.model.invoke(prompt)

            assert type(response) == str

            logger.info(f"Generated response: {response}")

            return response
        
        except Exception as e:
            logger.error(f"Error while generating re-written text: {str(e)}")
            raise e