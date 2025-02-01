import os
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import Union
from app.assistants.utils.assistants_utilities import execute_assistant, finalize_inputs_assistants, load_assistant_metadata
from app.services.schemas import GenericAssistantRequest, ToolRequest, ChatRequest, Message, ChatResponse, ToolResponse
from app.utils.auth import key_check
from app.services.logger import setup_logger
from app.api.error_utilities import InputValidationError, ErrorResponse
from app.tools.utils.tool_utilities import load_tool_metadata, execute_tool, finalize_inputs
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/")
def read_root():
    return {"Hello": "World"}

@router.post("/submit-tool", response_model=Union[ToolResponse, ErrorResponse])
async def submit_tool( data: ToolRequest, _ = Depends(key_check)):     
    try: 
        # Unpack GenericRequest for tool data
        request_data = data.tool_data
        
        requested_tool = load_tool_metadata(request_data.tool_id)
        
        request_inputs_dict = finalize_inputs(request_data.inputs, requested_tool['inputs'])

        result = execute_tool(request_data.tool_id, request_inputs_dict)
        
        return ToolResponse(data=result)
    
    except InputValidationError as e:
        logger.error(f"InputValidationError: {e}")

        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(ErrorResponse(status=400, message=e.message))
        )
    
    except HTTPException as e:
        logger.error(f"HTTPException: {e}")
        return JSONResponse(
            status_code=e.status_code,
            content=jsonable_encoder(ErrorResponse(status=e.status_code, message=e.detail))
        )

@router.post("/assistant-chat", response_model=ChatResponse)
async def assistants( request: GenericAssistantRequest, _ = Depends(key_check) ):
    
    assistant_group = request.assistant_inputs.assistant_group
    assistant_name = request.assistant_inputs.assistant_name

    requested_assistant = load_assistant_metadata(assistant_group, assistant_name)
    request_inputs_dict = finalize_inputs_assistants(request.assistant_inputs.inputs, requested_assistant['inputs'])
    result = execute_assistant(assistant_group, assistant_name, request_inputs_dict)

    formatted_response = Message(
        role="ai",
        type="text",
        payload={"text": result}
    )
    
    return ChatResponse(data=[formatted_response])

@router.post("/test-rewriter")
async def test_rewriter(
    input_text: str = Body(..., example="Enter the text to rewrite"),
    rewrite_instructions: str = Body(..., example="Summarize the text"),
    file_url: str = Body(..., example="Optional file URL"),
    file_type: str = Body(..., example="pdf"),
    lang: str = Body(..., example="Language of the output, e.g., 'en' for English")
):
    """
    Endpoint to test text rewriting directly by providing input text and instructions.
    """
    try:
        from app.tools.text_rewriter.core import executor

        # call Executor with the provided parameters
        rewritten_text = executor(
            input_text=input_text,
            file_url=file_url,
            file_type=file_type,
            rewrite_instructions=rewrite_instructions,
            lang=lang,
            verbose=True
        )

        #return {
        #    "status": "success",
        #    "rewritten_text": rewritten_text
        #}

        return rewritten_text

    except Exception as e:
        logger.error(f"Error in test-rewriter endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")