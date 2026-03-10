"""
Amazon Transcribe Plugin
Speech-to-text transcription using the Amazon Transcribe service
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
import hashlib
import hmac
import datetime
import uuid

logger = logging.getLogger(__name__)


class Plugin(IntegrationPlugin):
    """
    Amazon Transcribe plugin for cloud-based speech-to-text

    Capabilities:
    - Asynchronous batch transcription of audio/video files
    - Streaming real-time transcription
    - Automatic language identification across 35+ languages
    - Custom vocabulary and language model support
    - Speaker diarization, content redaction, and channel identification
    - List and manage transcription jobs

    Actions:
    - transcribe: Submit and poll a transcription job to completion
    - start_streaming: Start a streaming transcription session (returns config)
    - get_job: Retrieve details/status of an existing transcription job
    - list_jobs: List transcription jobs with optional filters
    - identify_language: Detect spoken language from an audio clip
    """

    # AWS service constants
    SERVICE = "transcribe"
    REGION_DEFAULT = "us-east-1"

    SUPPORTED_LANGUAGES = {
        "en-US": "English (US)", "en-GB": "English (UK)", "en-AU": "English (Australia)",
        "en-IN": "English (India)", "en-IE": "English (Ireland)", "en-AB": "English (Scottish)",
        "en-WL": "English (Welsh)", "es-US": "Spanish (US)", "es-ES": "Spanish (Spain)",
        "es-MX": "Spanish (Mexico)", "fr-CA": "French (Canada)", "fr-FR": "French (France)",
        "de-CH": "German (Switzerland)", "de-DE": "German (Germany)", "it-IT": "Italian",
        "pt-PT": "Portuguese (Portugal)", "pt-BR": "Portuguese (Brazil)", "nl-NL": "Dutch",
        "ru-RU": "Russian", "zh-CN": "Chinese (Simplified)", "zh-TW": "Chinese (Traditional)",
        "ja-JP": "Japanese", "ko-KR": "Korean", "ar-AE": "Arabic (Gulf)",
        "ar-SA": "Arabic (Modern Standard)", "hi-IN": "Hindi", "th-TH": "Thai",
        "tr-TR": "Turkish", "pl-PL": "Polish", "cs-CZ": "Czech", "da-DK": "Danish",
        "fi-FI": "Finnish", "nb-NO": "Norwegian", "sv-SE": "Swedish", "he-IL": "Hebrew",
        "id-ID": "Indonesian", "ms-MY": "Malay", "ro-RO": "Romanian", "uk-UA": "Ukrainian",
    }

    def __init__(self):
        metadata = PluginMetadata(
            id="amazon_transcribe",
            name="Amazon Transcribe",
            description="Cloud-based speech-to-text using Amazon Transcribe with multi-language and diarization support",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["audio", "ai", "transcription", "aws", "amazon"],
        )
        super().__init__(metadata)

        self.session = None
        self._access_key = None
        self._secret_key = None
        self._region = self.REGION_DEFAULT
        self._api_base = f"https://transcribe.{self._region}.amazonaws.com"
        self._initialized = False
        self._poll_interval = 5  # seconds between job status polls

    async def initialize(self) -> bool:
        """Initialize the Amazon Transcribe plugin"""
        if self._initialized:
            return True
        try:
            self._access_key = os.environ.get("AWS_ACCESS_KEY_ID")
            self._secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
            self._region = os.environ.get("AWS_DEFAULT_REGION", self.REGION_DEFAULT)
            self._api_base = f"https://transcribe.{self._region}.amazonaws.com"

            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=600)
                self.session = aiohttp.ClientSession(timeout=timeout)
            else:
                self.session = None

            self._initialized = True
            if not (self._access_key and self._secret_key):
                logger.warning(
                    "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY not set. "
                    "Amazon Transcribe plugin running in offline simulation mode."
                )
            else:
                logger.info(f"Amazon Transcribe plugin initialized (region: {self._region})")
            return True
        except Exception as e:
            logger.error(f"Amazon Transcribe initialization failed: {e}")
            return False

    async def connect(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Update AWS credentials"""
        try:
            if credentials:
                self._access_key = credentials.get("access_key_id", self._access_key)
                self._secret_key = credentials.get("secret_access_key", self._secret_key)
                new_region = credentials.get("region", self._region)
                if new_region != self._region:
                    self._region = new_region
                    self._api_base = f"https://transcribe.{self._region}.amazonaws.com"
            return True
        except Exception as e:
            logger.error(f"Amazon Transcribe connect failed: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            return True
        except Exception as e:
            logger.error(f"Amazon Transcribe disconnect failed: {e}")
            return False

    async def execute(self, action: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Dispatch to action handlers"""
        if not self._initialized:
            await self.initialize()
        try:
            if action == "transcribe":
                return await self._transcribe(params)
            elif action == "start_streaming":
                return await self._start_streaming(params)
            elif action == "get_job":
                return await self._get_job(params)
            elif action == "list_jobs":
                return await self._list_jobs(params)
            elif action == "identify_language":
                return await self._identify_language(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "supported_actions": [
                        "transcribe", "start_streaming", "get_job", "list_jobs", "identify_language"
                    ],
                }
        except Exception as e:
            logger.error(f"Amazon Transcribe execute failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Action implementations
    # ------------------------------------------------------------------

    async def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit an audio file for transcription and wait for completion.

        Parameters:
            audio_file (str): S3 URI (s3://bucket/key) or public HTTPS URL to media
            language_code (str): Language code (e.g. "en-US"). Omit for auto-detect.
            job_name (str): Unique job name (auto-generated if omitted)
            media_format (str): Audio format – mp3, mp4, wav, flac, ogg, amr, webm (default mp3)
            diarize (bool): Enable speaker diarization (default False)
            max_speakers (int): Max speakers for diarization (default 2)
            content_redaction (bool): Redact PII from transcript (default False)
            vocabulary_name (str): Custom vocabulary to apply (optional)
            output_bucket (str): S3 bucket for transcript output (optional)
        """
        audio_file = params.get("audio_file")
        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not (self._access_key and self._secret_key):
            return {
                "success": True,
                "result": {
                    "job_name": params.get("job_name", "simulated-job-001"),
                    "job_status": "COMPLETED",
                    "transcript": {
                        "transcript_file_uri": "https://example.com/simulated-transcript.json",
                        "text": (
                            "This is a simulated Amazon Transcribe result. "
                            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to use the live service."
                        ),
                    },
                    "language_code": params.get("language_code", "en-US"),
                    "media_format": params.get("media_format", "mp3"),
                    "duration_in_seconds": 12.4,
                    "num_speakers": 1 if not params.get("diarize") else 2,
                },
                "mode": "offline_simulation",
            }

        # Submit job
        submit_result = await self._start_transcription_job(params)
        if not submit_result.get("success"):
            return submit_result

        job_name = submit_result["result"].get("TranscriptionJobName")
        if not job_name:
            return {"success": False, "error": "No job name returned"}

        # Poll until complete
        return await self._poll_job_to_completion(job_name)

    async def _start_streaming(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return configuration for starting a streaming transcription session.

        Parameters:
            language_code (str): Language for streaming (default "en-US")
            sample_rate (int): Audio sample rate in Hz (default 16000)
            media_encoding (str): pcm, ogg-opus, or flac (default pcm)
            vocabulary_name (str): Custom vocabulary (optional)
            enable_partial_results (bool): Stream partial results (default True)
        """
        if not (self._access_key and self._secret_key):
            return {
                "success": True,
                "result": {
                    "endpoint": f"wss://transcribestreaming.{self._region}.amazonaws.com:8443/stream-transcription-websocket",
                    "language_code": params.get("language_code", "en-US"),
                    "sample_rate": int(params.get("sample_rate", 16000)),
                    "media_encoding": params.get("media_encoding", "pcm"),
                    "note": "Streaming requires signed WebSocket connection. AWS credentials needed for production use.",
                    "docs": "https://docs.aws.amazon.com/transcribe/latest/dg/streaming.html",
                },
                "mode": "offline_simulation",
            }

        return {
            "success": True,
            "result": {
                "endpoint": f"wss://transcribestreaming.{self._region}.amazonaws.com:8443/stream-transcription-websocket",
                "language_code": params.get("language_code", "en-US"),
                "sample_rate": int(params.get("sample_rate", 16000)),
                "media_encoding": params.get("media_encoding", "pcm"),
                "region": self._region,
                "note": "Sign the WebSocket URL with SigV4 before connecting.",
            },
        }

    async def _get_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the status and result of a transcription job.

        Parameters:
            job_name (str): The name of the transcription job
        """
        job_name = params.get("job_name")
        if not job_name:
            return {"success": False, "error": "job_name is required"}

        if not (self._access_key and self._secret_key):
            return {
                "success": True,
                "result": {
                    "TranscriptionJobName": job_name,
                    "TranscriptionJobStatus": "COMPLETED",
                    "LanguageCode": "en-US",
                    "CompletionTime": "2024-01-01T00:01:00Z",
                    "Transcript": {
                        "TranscriptFileUri": f"https://example.com/{job_name}-transcript.json"
                    },
                },
                "mode": "offline_simulation",
            }

        return await self._aws_api_call("GetTranscriptionJob", {"TranscriptionJobName": job_name})

    async def _list_jobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List transcription jobs.

        Parameters:
            status (str): Filter by status – QUEUED, IN_PROGRESS, FAILED, COMPLETED (optional)
            job_name_contains (str): Filter jobs whose name contains this string (optional)
            max_results (int): Maximum number of results (default 100)
            next_token (str): Pagination token (optional)
        """
        if not (self._access_key and self._secret_key):
            return {
                "success": True,
                "result": {
                    "TranscriptionJobSummaries": [
                        {
                            "TranscriptionJobName": "simulated-job-001",
                            "TranscriptionJobStatus": "COMPLETED",
                            "LanguageCode": "en-US",
                            "CreationTime": "2024-01-01T00:00:00Z",
                        },
                        {
                            "TranscriptionJobName": "simulated-job-002",
                            "TranscriptionJobStatus": "IN_PROGRESS",
                            "LanguageCode": "es-US",
                            "CreationTime": "2024-01-02T00:00:00Z",
                        },
                    ],
                    "NextToken": None,
                },
                "mode": "offline_simulation",
            }

        request_body: Dict[str, Any] = {
            "MaxResults": int(params.get("max_results", 100)),
        }
        if params.get("status"):
            request_body["Status"] = params["status"].upper()
        if params.get("job_name_contains"):
            request_body["JobNameContains"] = params["job_name_contains"]
        if params.get("next_token"):
            request_body["NextToken"] = params["next_token"]

        return await self._aws_api_call("ListTranscriptionJobs", request_body)

    async def _identify_language(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect the spoken language by submitting a transcription job with auto language identification.

        Parameters:
            audio_file (str): S3 URI or public URL for the audio
            language_options (list): Optional list of candidate language codes to consider
        """
        audio_file = params.get("audio_file")
        if not audio_file:
            return {"success": False, "error": "audio_file is required"}

        if not (self._access_key and self._secret_key):
            return {
                "success": True,
                "result": {
                    "identified_language": "en-US",
                    "identified_language_name": "English (US)",
                    "language_score": 0.98,
                    "alternatives": [
                        {"language_code": "en-US", "score": 0.98},
                        {"language_code": "en-GB", "score": 0.01},
                    ],
                },
                "mode": "offline_simulation",
            }

        # Submit job with IdentifyLanguage=True
        identify_params = dict(params)
        identify_params["identify_language"] = True
        submit_result = await self._start_transcription_job(identify_params)
        if not submit_result.get("success"):
            return submit_result

        job_name = submit_result["result"].get("TranscriptionJobName")
        if not job_name:
            return {"success": False, "error": "No job name returned"}

        completed = await self._poll_job_to_completion(job_name)
        if not completed.get("success"):
            return completed

        job_details = completed["result"]
        return {
            "success": True,
            "result": {
                "identified_language": job_details.get("IdentifiedLanguageCode"),
                "language_score": job_details.get("IdentifiedLanguageScore"),
                "job_name": job_name,
            },
        }

    # ------------------------------------------------------------------
    # AWS API helpers
    # ------------------------------------------------------------------

    async def _start_transcription_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start an Amazon Transcribe job"""
        audio_file = params.get("audio_file", "")
        job_name = params.get("job_name") or f"windows-ai-{uuid.uuid4().hex[:12]}"
        media_format = params.get("media_format", "mp3")

        request_body: Dict[str, Any] = {
            "TranscriptionJobName": job_name,
            "Media": {"MediaFileUri": audio_file},
            "MediaFormat": media_format,
        }

        language_code = params.get("language_code")
        if language_code:
            request_body["LanguageCode"] = language_code
        elif params.get("identify_language"):
            request_body["IdentifyLanguage"] = True
        else:
            request_body["LanguageCode"] = "en-US"

        if params.get("diarize"):
            request_body["Settings"] = {
                "ShowSpeakerLabels": True,
                "MaxSpeakerLabels": int(params.get("max_speakers", 2)),
            }

        if params.get("content_redaction"):
            request_body["ContentRedaction"] = {
                "RedactionType": "PII",
                "RedactionOutput": "redacted",
            }

        if params.get("vocabulary_name"):
            request_body.setdefault("Settings", {})["VocabularyName"] = params["vocabulary_name"]

        if params.get("output_bucket"):
            request_body["OutputBucketName"] = params["output_bucket"]

        return await self._aws_api_call("StartTranscriptionJob", request_body)

    async def _poll_job_to_completion(self, job_name: str) -> Dict[str, Any]:
        """Poll until a job reaches COMPLETED or FAILED"""
        for _ in range(240):  # up to ~20 minutes
            await asyncio.sleep(self._poll_interval)
            result = await self._aws_api_call("GetTranscriptionJob", {"TranscriptionJobName": job_name})
            if not result.get("success"):
                continue
            job = result["result"].get("TranscriptionJob", result["result"])
            status = job.get("TranscriptionJobStatus", "")
            if status == "COMPLETED":
                return {"success": True, "result": job}
            elif status == "FAILED":
                return {
                    "success": False,
                    "error": f"Job {job_name} failed: {job.get('FailureReason', 'unknown')}",
                }

        return {"success": False, "error": f"Job {job_name} timed out while polling"}

    async def _aws_api_call(self, action: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Make a signed AWS Transcribe API call using SigV4"""
        if not self.session:
            return {"success": False, "error": "HTTP session not available"}

        now = datetime.datetime.utcnow()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        body_json = json.dumps(body)
        body_bytes = body_json.encode("utf-8")
        payload_hash = hashlib.sha256(body_bytes).hexdigest()

        host = f"transcribe.{self._region}.amazonaws.com"
        canonical_uri = "/"
        canonical_querystring = ""
        canonical_headers = (
            f"content-type:application/x-amz-json-1.1\n"
            f"host:{host}\n"
            f"x-amz-date:{amz_date}\n"
            f"x-amz-target:Transcribe.{action}\n"
        )
        signed_headers = "content-type;host;x-amz-date;x-amz-target"

        canonical_request = "\n".join([
            "POST", canonical_uri, canonical_querystring,
            canonical_headers, signed_headers, payload_hash,
        ])

        credential_scope = f"{date_stamp}/{self._region}/transcribe/aws4_request"
        string_to_sign = "\n".join([
            "AWS4-HMAC-SHA256", amz_date, credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ])

        signing_key = self._get_signature_key(date_stamp)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization = (
            f"AWS4-HMAC-SHA256 Credential={self._access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Date": amz_date,
            "X-Amz-Target": f"Transcribe.{action}",
            "Authorization": authorization,
        }

        try:
            async with self.session.post(
                f"https://{host}/",
                headers=headers,
                data=body_bytes,
            ) as resp:
                resp_text = await resp.text()
                if resp.status in (200, 201):
                    try:
                        return {"success": True, "result": json.loads(resp_text)}
                    except json.JSONDecodeError:
                        return {"success": True, "result": {"raw": resp_text}}
                else:
                    return {"success": False, "error": f"AWS API error {resp.status}: {resp_text}"}
        except Exception as e:
            logger.error(f"AWS Transcribe API call failed: {e}")
            return {"success": False, "error": str(e)}

    def _get_signature_key(self, date_stamp: str) -> bytes:
        """Derive the SigV4 signing key"""
        k_date = hmac.new(
            f"AWS4{self._secret_key}".encode("utf-8"), date_stamp.encode("utf-8"), hashlib.sha256
        ).digest()
        k_region = hmac.new(k_date, self._region.encode("utf-8"), hashlib.sha256).digest()
        k_service = hmac.new(k_region, b"transcribe", hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()
        return k_signing

    async def shutdown(self):
        """Shutdown the plugin"""
        await self.disconnect()

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["transcribe", "start_streaming", "get_job", "list_jobs", "identify_language"],
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

