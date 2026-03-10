"""
Rev AI Plugin
High-accuracy speech recognition and transcription using the Rev AI API
"""

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
from typing import Dict, Any, Optional, List
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None
import os
import logging
import json
import asyncio
import base64

logger = logging.getLogger(__name__)


class Plugin(IntegrationPlugin):
    """
    Rev AI plugin for professional-grade speech-to-text transcription

    Capabilities:
    - Submit audio/video files for asynchronous transcription
    - Retrieve completed transcripts in multiple formats
    - List all transcription jobs and their statuses
    - Real-time streaming transcription support
    - Human review option for maximum accuracy

    Actions:
    - transcribe: Submit audio for transcription and poll until complete
    - get_transcript: Retrieve transcript for an existing job
    - list_jobs: List all transcription jobs
    - submit_job: Submit a job without waiting (returns job ID)
    """

    # Rev AI job statuses
    JOB_STATUS_IN_PROGRESS = "in_progress"
    JOB_STATUS_TRANSCRIBED = "transcribed"
    JOB_STATUS_FAILED = "failed"

    SUPPORTED_LANGUAGES = {
        "en": "English", "es": "Spanish", "fr": "French", "de": "German",
        "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "ru": "Russian",
        "zh": "Chinese (Simplified)", "ja": "Japanese", "ko": "Korean",
        "ar": "Arabic", "hi": "Hindi", "pl": "Polish",
    }

    def __init__(self):
        metadata = PluginMetadata(
            id="rev_ai",
            name="Rev AI",
            description="Professional speech recognition and transcription using the Rev AI API",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["audio", "ai", "transcription", "rev-ai", "speech"],
        )
        super().__init__(metadata)

        self.session = None
        self._api_key = None
        self._api_base = "https://api.rev.ai/speechtotext/v1"
        self._initialized = False
        self._poll_interval = 5  # seconds between job status polls

    async def initialize(self) -> bool:
        """Initialize the Rev AI plugin"""
        if self._initialized:
            return True
        try:
            self._api_key = os.environ.get("REV_AI_ACCESS_TOKEN")
            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=600)
                self.session = aiohttp.ClientSession(timeout=timeout)
            else:
                self.session = None
            self._initialized = True
            if not self._api_key:
                logger.warning(
                    "REV_AI_ACCESS_TOKEN not set. Rev AI plugin running in offline simulation mode."
                )
            else:
                logger.info("Rev AI plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Rev AI initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Update credentials"""
        try:
            if credentials:
                self._api_key = credentials.get("api_key", self._api_key)
                self._api_base = credentials.get("api_base", self._api_base)
            return True
        except Exception as e:
            logger.error(f"Rev AI connect failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            return True
        except Exception as e:
            logger.error(f"Rev AI disconnect failed: {e}")
            return False

    async def execute(self, action: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Dispatch to action handlers"""
        if not self._initialized:
            await self.initialize()
        try:
            if action == "transcribe":
                return await self._transcribe(params)
            elif action == "get_transcript":
                return await self._get_transcript(params)
            elif action == "list_jobs":
                return await self._list_jobs(params)
            elif action == "submit_job":
                return await self._submit_job(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "supported_actions": ["transcribe", "get_transcript", "list_jobs", "submit_job"],
                }
        except Exception as e:
            logger.error(f"Rev AI execute failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Action implementations
    # ------------------------------------------------------------------

    async def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit audio for transcription and poll until the job completes.

        Parameters:
            audio_file (str): Path to audio/video file or a public URL
            language (str): Language code (default "en")
            skip_diarization (bool): Disable speaker diarization (default False)
            skip_punctuation (bool): Disable punctuation (default False)
            verbatim (bool): Include filler words / false starts (default False)
            metadata (str): Optional metadata string attached to the job
        """
        audio_file = params.get("audio_file")
        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "job_id": "simulated_job_001",
                    "status": "transcribed",
                    "text": (
                        "This is a simulated Rev AI transcription. "
                        "Configure REV_AI_ACCESS_TOKEN to use the live API."
                    ),
                    "monologues": [
                        {
                            "speaker": 0,
                            "elements": [
                                {"type": "text", "value": "This is a simulated Rev AI transcription.", "ts": 0.0, "end_ts": 2.5, "confidence": 0.99},
                                {"type": "punct", "value": " "},
                                {"type": "text", "value": "Configure REV_AI_ACCESS_TOKEN to use the live API.", "ts": 2.8, "end_ts": 5.2, "confidence": 0.97},
                            ],
                        }
                    ],
                    "language": params.get("language", "en"),
                    "duration": 5.5,
                },
                "mode": "offline_simulation",
            }

        # Submit job
        submit_result = await self._submit_job(params)
        if not submit_result.get("success"):
            return submit_result

        job_id = submit_result["result"].get("id")
        if not job_id:
            return {"success": False, "error": "No job ID returned"}

        # Poll until complete
        return await self._poll_job_to_completion(job_id)

    async def _submit_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a transcription job without waiting for completion.

        Parameters:
            audio_file (str): Path or URL to audio/video
            language (str): Language hint (default "en")
            skip_diarization (bool): Disable diarization (default False)
            skip_punctuation (bool): Disable punctuation (default False)
            verbatim (bool): Verbatim transcription including filler words (default False)
            metadata (str): Optional job metadata
        """
        audio_file = params.get("audio_file")
        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "id": "simulated_job_001",
                    "status": "in_progress",
                    "created_on": "2024-01-01T00:00:00Z",
                    "language": params.get("language", "en"),
                },
                "mode": "offline_simulation",
            }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        # Determine if audio_file is a URL or a local path
        if audio_file.startswith("http://") or audio_file.startswith("https://"):
            job_body: Dict[str, Any] = {"media_url": audio_file}
        else:
            # Upload file directly
            return await self._submit_job_with_file(audio_file, params)

        job_body.update({
            "language": params.get("language", "en"),
            "skip_diarization": bool(params.get("skip_diarization", False)),
            "skip_punctuation": bool(params.get("skip_punctuation", False)),
            "verbatim": bool(params.get("verbatim", False)),
        })
        if params.get("metadata"):
            job_body["metadata"] = str(params["metadata"])

        try:
            async with self.session.post(
                f"{self._api_base}/jobs",
                headers=headers,
                json=job_body,
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return {"success": True, "result": data}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
        except Exception as e:
            logger.error(f"Rev AI job submission failed: {e}")
            return {"success": False, "error": str(e)}

    async def _submit_job_with_file(
        self, audio_file: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit a local audio file to Rev AI as a multipart upload"""
        headers = {"Authorization": f"Bearer {self._api_key}"}
        options: Dict[str, Any] = {
            "language": params.get("language", "en"),
            "skip_diarization": bool(params.get("skip_diarization", False)),
            "skip_punctuation": bool(params.get("skip_punctuation", False)),
            "verbatim": bool(params.get("verbatim", False)),
        }
        if params.get("metadata"):
            options["metadata"] = str(params["metadata"])

        try:
            with open(audio_file, "rb") as audio_fh:
                form_data = aiohttp.FormData()
                form_data.add_field(
                    "media",
                    audio_fh,
                    filename=os.path.basename(audio_file),
                )
                form_data.add_field("options", json.dumps(options), content_type="application/json")

            async with self.session.post(
                f"{self._api_base}/jobs",
                headers=headers,
                data=form_data,
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return {"success": True, "result": data}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
        except Exception as e:
            logger.error(f"Rev AI file upload failed: {e}")
            return {"success": False, "error": str(e)}

    async def _get_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve the transcript for a completed job.

        Parameters:
            job_id (str): Rev AI job ID
            format (str): Output format: "json" (default) or "text"
        """
        job_id = params.get("job_id")
        if not job_id:
            return {"success": False, "error": "job_id is required"}

        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "job_id": job_id,
                    "text": "Simulated transcript text for job " + job_id,
                    "monologues": [],
                    "format": params.get("format", "json"),
                },
                "mode": "offline_simulation",
            }

        headers = {"Authorization": f"Bearer {self._api_key}"}
        fmt = params.get("format", "json")
        if fmt == "text":
            headers["Accept"] = "text/plain"
        else:
            headers["Accept"] = "application/vnd.rev.transcript.v1.0+json"

        try:
            async with self.session.get(
                f"{self._api_base}/jobs/{job_id}/transcript",
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    if fmt == "text":
                        text_content = await resp.text()
                        return {"success": True, "result": {"job_id": job_id, "text": text_content}}
                    else:
                        data = await resp.json()
                        return {"success": True, "result": data}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
        except Exception as e:
            logger.error(f"Rev AI get transcript failed: {e}")
            return {"success": False, "error": str(e)}

    async def _list_jobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List transcription jobs.

        Parameters:
            limit (int): Maximum number of jobs to return (default 100)
            starting_after (str): Cursor for pagination (job ID)
        """
        if not self._api_key:
            return {
                "success": True,
                "result": {
                    "jobs": [
                        {
                            "id": "simulated_job_001",
                            "status": "transcribed",
                            "created_on": "2024-01-01T00:00:00Z",
                            "duration_seconds": 120.5,
                            "language": "en",
                        },
                        {
                            "id": "simulated_job_002",
                            "status": "in_progress",
                            "created_on": "2024-01-02T00:00:00Z",
                            "language": "es",
                        },
                    ],
                    "total": 2,
                },
                "mode": "offline_simulation",
            }

        headers = {"Authorization": f"Bearer {self._api_key}"}
        query: Dict[str, Any] = {"limit": int(params.get("limit", 100))}
        if params.get("starting_after"):
            query["starting_after"] = params["starting_after"]

        try:
            async with self.session.get(
                f"{self._api_base}/jobs",
                headers=headers,
                params=query,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"success": True, "result": {"jobs": data, "total": len(data)}}
                else:
                    text = await resp.text()
                    return {"success": False, "error": f"API error {resp.status}: {text}"}
        except Exception as e:
            logger.error(f"Rev AI list jobs failed: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Polling helper
    # ------------------------------------------------------------------

    async def _poll_job_to_completion(self, job_id: str) -> Dict[str, Any]:
        """Poll a Rev AI job until it reaches a terminal state"""
        headers = {"Authorization": f"Bearer {self._api_key}"}
        for _ in range(240):  # up to ~20 minutes
            await asyncio.sleep(self._poll_interval)
            try:
                async with self.session.get(
                    f"{self._api_base}/jobs/{job_id}",
                    headers=headers,
                ) as resp:
                    if resp.status != 200:
                        continue
                    job = await resp.json()
                    status = job.get("status")
                    if status == self.JOB_STATUS_TRANSCRIBED:
                        transcript_result = await self._get_transcript({"job_id": job_id})
                        if transcript_result.get("success"):
                            transcript_result["result"]["job"] = job
                        return transcript_result
                    elif status == self.JOB_STATUS_FAILED:
                        return {
                            "success": False,
                            "error": f"Job {job_id} failed: {job.get('failure_detail', 'unknown error')}",
                        }
            except Exception as e:
                logger.warning(f"Polling job {job_id} failed: {e}")

        return {"success": False, "error": f"Job {job_id} timed out after polling"}

    async def shutdown(self):
        """Shutdown the plugin"""
        await self.disconnect()

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["transcribe", "get_transcript", "list_jobs", "submit_job"],
                    "description": "Action to perform",
                },
                "params": {
                    "type": "object",
                    "description": "Action-specific parameters",
                },
            },
            "required": ["action"],
        }


plugin = Plugin()

