"""
Rev.ai Transcription Plugin
Supports speech-to-text transcription via Rev.ai API
"""

from typing import Dict, Any, Optional, List
import os


class RevaiPlugin:
    """Plugin for Rev.ai speech-to-text transcription"""

    name = "revai"
    version = "1.0.0"
    description = "Integration with Rev.ai speech-to-text transcription"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Rev.ai plugin"""
        try:
            from rev_ai import apiclient

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("REV_AI_ACCESS_TOKEN")
            )

            if not self.api_key:
                return False

            self.client = apiclient.RevAiAPIClient(self.api_key)
            self._initialized = True
            return True

        except ImportError:
            print("rev_ai package not installed. Install with: pip install rev_ai")
            return False
        except Exception as e:
            print(f"Error initializing Rev.ai plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Rev.ai action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}

        try:
            if action == "submit_job_url":
                return self._submit_job_url(params)
            elif action == "submit_job_local_file":
                return self._submit_job_local_file(params)
            elif action == "get_job_details":
                return self._get_job_details(params)
            elif action == "get_transcript_text":
                return self._get_transcript_text(params)
            elif action == "get_transcript_json":
                return self._get_transcript_json(params)
            elif action == "get_transcript_object":
                return self._get_transcript_object(params)
            elif action == "get_captions":
                return self._get_captions(params)
            elif action == "get_list_of_jobs":
                return self._get_list_of_jobs(params)
            elif action == "delete_job":
                return self._delete_job(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _submit_job_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a transcription job from URL"""
        url = params.get("url")
        if not url:
            return {"error": "url parameter required"}

        # Extract optional parameters
        metadata = params.get("metadata")
        notification_config = params.get("notification_config")
        skip_diarization = params.get("skip_diarization", False)
        skip_punctuation = params.get("skip_punctuation", False)
        speaker_channels_count = params.get("speaker_channels_count")
        custom_vocabularies = params.get("custom_vocabularies")
        filter_profanity = params.get("filter_profanity", False)
        remove_disfluencies = params.get("remove_disfluencies", False)
        delete_after_seconds = params.get("delete_after_seconds")
        language = params.get("language", "en")
        custom_vocabulary_id = params.get("custom_vocabulary_id")
        transcriber = params.get("transcriber", "machine")
        verbatim = params.get("verbatim", True)
        source_config = params.get("source_config")
        summarization_config = params.get("summarization_config")
        translation_config = params.get("translation_config")

        try:
            job = self.client.submit_job_url(
                url=url,
                metadata=metadata,
                notification_config=notification_config,
                skip_diarization=skip_diarization,
                skip_punctuation=skip_punctuation,
                speaker_channels_count=speaker_channels_count,
                custom_vocabularies=custom_vocabularies,
                filter_profanity=filter_profanity,
                remove_disfluencies=remove_disfluencies,
                delete_after_seconds=delete_after_seconds,
                language=language,
                custom_vocabulary_id=custom_vocabulary_id,
                transcriber=transcriber,
                verbatim=verbatim,
                source_config=source_config,
                summarization_config=summarization_config,
                translation_config=translation_config
            )

            return {
                "job_id": job.id,
                "status": job.status,
                "language": getattr(job, 'language', None),
                "created_on": getattr(job, 'created_on', None),
                "transcriber": getattr(job, 'transcriber', None)
            }

        except Exception as e:
            return {"error": f"Failed to submit job: {str(e)}"}

    def _submit_job_local_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a transcription job from local file"""
        filename = params.get("filename")
        if not filename:
            return {"error": "filename parameter required"}

        # Extract optional parameters
        metadata = params.get("metadata")
        notification_config = params.get("notification_config")
        skip_diarization = params.get("skip_diarization", False)
        skip_punctuation = params.get("skip_punctuation", False)
        speaker_channels_count = params.get("speaker_channels_count")
        custom_vocabularies = params.get("custom_vocabularies")
        filter_profanity = params.get("filter_profanity", False)
        remove_disfluencies = params.get("remove_disfluencies", False)
        delete_after_seconds = params.get("delete_after_seconds")
        language = params.get("language", "en")
        custom_vocabulary_id = params.get("custom_vocabulary_id")
        transcriber = params.get("transcriber", "machine")
        verbatim = params.get("verbatim", True)
        summarization_config = params.get("summarization_config")
        translation_config = params.get("translation_config")

        try:
            job = self.client.submit_job_local_file(
                filename=filename,
                metadata=metadata,
                notification_config=notification_config,
                skip_diarization=skip_diarization,
                skip_punctuation=skip_punctuation,
                speaker_channels_count=speaker_channels_count,
                custom_vocabularies=custom_vocabularies,
                filter_profanity=filter_profanity,
                remove_disfluencies=remove_disfluencies,
                delete_after_seconds=delete_after_seconds,
                language=language,
                custom_vocabulary_id=custom_vocabulary_id,
                transcriber=transcriber,
                verbatim=verbatim,
                summarization_config=summarization_config,
                translation_config=translation_config
            )

            return {
                "job_id": job.id,
                "status": job.status,
                "language": getattr(job, 'language', None),
                "created_on": getattr(job, 'created_on', None),
                "transcriber": getattr(job, 'transcriber', None)
            }

        except Exception as e:
            return {"error": f"Failed to submit job: {str(e)}"}

    def _get_job_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get details of a transcription job"""
        job_id = params.get("job_id")
        if not job_id:
            return {"error": "job_id parameter required"}

        try:
            job_details = self.client.get_job_details(job_id)

            return {
                "job_id": job_details.id,
                "status": job_details.status,
                "language": getattr(job_details, 'language', None),
                "created_on": getattr(job_details, 'created_on', None),
                "transcriber": getattr(job_details, 'transcriber', None),
                "type": getattr(job_details, 'type', None),
                "delete_after_seconds": getattr(job_details, 'delete_after_seconds', None)
            }

        except Exception as e:
            return {"error": f"Failed to get job details: {str(e)}"}

    def _get_transcript_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get transcript as plain text"""
        job_id = params.get("job_id")
        if not job_id:
            return {"error": "job_id parameter required"}

        try:
            transcript_text = self.client.get_transcript_text(job_id)
            return {"transcript": transcript_text}

        except Exception as e:
            return {"error": f"Failed to get transcript text: {str(e)}"}

    def _get_transcript_json(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get transcript as JSON"""
        job_id = params.get("job_id")
        if not job_id:
            return {"error": "job_id parameter required"}

        try:
            transcript_json = self.client.get_transcript_json(job_id)
            return {"transcript": transcript_json}

        except Exception as e:
            return {"error": f"Failed to get transcript JSON: {str(e)}"}

    def _get_transcript_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get transcript as Python object"""
        job_id = params.get("job_id")
        if not job_id:
            return {"error": "job_id parameter required"}

        language = params.get("language")  # For translated transcripts

        try:
            if language:
                transcript_object = self.client.get_translated_transcript_object(job_id, language)
            else:
                transcript_object = self.client.get_transcript_object(job_id)

            # Convert to dict for JSON serialization
            return {"transcript": transcript_object.__dict__ if hasattr(transcript_object, '__dict__') else str(transcript_object)}

        except Exception as e:
            return {"error": f"Failed to get transcript object: {str(e)}"}

    def _get_captions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get captions in SRT or VTT format"""
        job_id = params.get("job_id")
        if not job_id:
            return {"error": "job_id parameter required"}

        from rev_ai.models import CaptionType

        content_type = params.get("content_type", "srt").lower()
        channel_id = params.get("channel_id")
        language = params.get("language")  # For translated captions

        try:
            caption_type = CaptionType.SRT if content_type == "srt" else CaptionType.VTT

            if language:
                captions = self.client.get_translated_captions(job_id, language, caption_type, channel_id)
            else:
                captions = self.client.get_captions(job_id, caption_type, channel_id)

            return {"captions": captions}

        except Exception as e:
            return {"error": f"Failed to get captions: {str(e)}"}

    def _get_list_of_jobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of transcription jobs"""
        limit = params.get("limit", 100)
        starting_after = params.get("starting_after")

        try:
            jobs = self.client.get_list_of_jobs(limit=limit, starting_after=starting_after)

            job_list = []
            for job in jobs:
                job_list.append({
                    "job_id": job.id,
                    "status": job.status,
                    "created_on": getattr(job, 'created_on', None),
                    "type": getattr(job, 'type', None),
                    "transcriber": getattr(job, 'transcriber', None)
                })

            return {"jobs": job_list}

        except Exception as e:
            return {"error": f"Failed to get list of jobs: {str(e)}"}

    def _delete_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a transcription job"""
        job_id = params.get("job_id")
        if not job_id:
            return {"error": "job_id parameter required"}

        try:
            self.client.delete_job(job_id)
            return {"success": True, "message": f"Job {job_id} deleted successfully"}

        except Exception as e:
            return {"error": f"Failed to delete job: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = RevaiPlugin
PLUGIN_NAME = "revai"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Rev.ai speech-to-text transcription"
PLUGIN_ACTIONS = [
    "submit_job_url",
    "submit_job_local_file",
    "get_job_details",
    "get_transcript_text",
    "get_transcript_json",
    "get_transcript_object",
    "get_captions",
    "get_list_of_jobs",
    "delete_job"
]