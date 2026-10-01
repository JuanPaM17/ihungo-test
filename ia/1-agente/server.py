# Standard libraries
import os
import time
import logging
import urllib.parse
import uuid
import base64
import json as _json_std

# Third-party packages
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Internal modules
from version.assistant_v1 import process_query_v1
from version.assistant_v2 import process_query_v2, stream_query_v2


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

load_dotenv()

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8085").split(",")

limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])

app = FastAPI(root_path="/llm")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Session-Id", "Cache-Control"],
)

logger = logging.getLogger(__name__)


def _extract_role_from_jwt(token: str) -> str:
    """Decodes the JWT payload (no signature verification) and returns the role claim."""
    try:
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = _json_std.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("role", "associate")
    except Exception:
        return "associate"


class RequestParams(BaseModel):
    query: Optional[str] = None
    type: Optional[str] = None
    document: Optional[str] = None
    userName: Optional[str] = None
    language: Optional[str] = None
    prefixHistory: Optional[str] = None
    isAnonymous: bool = True

@app.post("/{version}/{tenant_id}")
@limiter.limit("30/minute")
async def entry_tenant(
    request: Request,
    version: str,
    tenant_id: str,
    params: RequestParams,):

    start_time_llm_service = time.time()
    version = version.lower()

    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Unsupported version")

    _raw_auth = request.headers.get("Authorization") or request.headers.get("authorization") or ""
    token = _raw_auth.removeprefix("Bearer ").strip()
    role = _extract_role_from_jwt(token)
    query = params.query
    query_type = params.type
    document = params.document
    user_name = params.userName
    language = params.language or "es"
    prefix_history = params.prefixHistory
    is_anonymous = params.isAnonymous

    if not query:
        message = "Query was not provided."
        raise ValueError(message)
    query = urllib.parse.unquote(query).replace('"', "")

    if not token:
        logger.warning("Error: Token not found.")

    session_id = request.headers.get("X-Session-Id") or str(uuid.uuid4())
    if prefix_history:
        thread_id = session_id + "_" + prefix_history
    else:
        thread_id = session_id

    logger.info("---- INVOKING ASSISTANT WITH THE FOLLOWING PARAMS ---- ")
    logger.info("Version: %s", version)
    logger.info("Session ID: %s", session_id)
    logger.info("Query: %s", query)
    logger.info("Tenant id: %s", tenant_id)
    logger.info("Query Type: %s", query_type)
    logger.info("Document: %s", document)
    logger.info("User Name: %s", user_name)
    logger.info("Is Anonymous: %s", is_anonymous)
    logger.info("Role: %s", role)
    logger.info("Language: %s", language)
    logger.info("Prefix History: %s", prefix_history)

    params = {
        "tenant_id": tenant_id,
        "query": query,
        "thread_id": thread_id,
        "token": token,
        "document": document,
        "user_name": user_name,
        "language": language,
        "version": version,
        "is_anonymous": is_anonymous,
        "role": role,
    }
    llm_response = {}
    if version == "v1":
        llm_response = await process_query_v1(**params)
    elif version == "v2":
        llm_response = await process_query_v2(**params)

        #llm_response = await hablar_con_llm(query, token)

    end_time_llm_service = time.time()

    total_time = f"{end_time_llm_service - start_time_llm_service:.3f}s"
    data_response = {"response": llm_response, "session_id": session_id, "total_time": total_time}
    logger.info("--- Logging Response ---")
    logger.info(
        "\nResponse: %s\nSession ID: %s\nTotal Time: %s",
        data_response["response"],
        data_response["session_id"],
        data_response["total_time"],
    )

    return data_response


@app.post("/{version}/{tenant_id}/stream")
@limiter.limit("30/minute")
async def entry_tenant_stream(
    request: Request,
    version: str,
    tenant_id: str,
    params: RequestParams,
):
    version = version.lower()

    if version != "v2":
        raise HTTPException(status_code=400, detail="Streaming only supported for v2")

    _raw_auth = request.headers.get("Authorization") or request.headers.get("authorization") or ""
    token = _raw_auth.removeprefix("Bearer ").strip()
    role = _extract_role_from_jwt(token)
    query = params.query
    document = params.document
    user_name = params.userName
    language = params.language or "es"
    prefix_history = params.prefixHistory
    is_anonymous = params.isAnonymous

    if not query:
        raise HTTPException(status_code=400, detail="Query was not provided.")
    query = urllib.parse.unquote(query).replace('"', "")

    if not token:
        logger.warning("stream: Token not found.")

    session_id = request.headers.get("X-Session-Id") or str(uuid.uuid4())
    thread_id = session_id + "_" + prefix_history if prefix_history else session_id

    logger.info("---- INVOKING STREAM ASSISTANT ----")
    logger.info("Version: %s", version)
    logger.info("Session ID: %s", session_id)
    logger.info("Query: %s", query)
    logger.info("Tenant id: %s", tenant_id)

    async def event_generator():
        try:
            async for chunk in stream_query_v2(
                tenant_id=tenant_id,
                query=query,
                thread_id=thread_id,
                token=token,
                session_id=session_id,
                document=document,
                user_name=user_name,
                is_anonymous=is_anonymous,
                role=role,
                language=language,
                version=version,
            ):
                if await request.is_disconnected():
                    logger.info("stream: client disconnected, stopping.")
                    break
                yield chunk
        except Exception as e:
            logger.error("stream: unexpected error in generator: %s", e)
            import json as _json
            yield f"event: error\ndata: {_json.dumps({'type': 'internal_error', 'message': 'Error inesperado.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("-- STARTING SERVER WITH GUNICORN --")
    port = int(os.getenv("APP_PORT", 8001))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
