"""
Comprehensive VideoGenerationManager Tests
Tests all 10 video providers with mock responses
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from windows_ai.integrations.video_generation import VideoGenerationManager, VideoProvider


def create_mock_session(post_response_data, get_response_data):
    """Helper to create properly configured mock aiohttp session"""
    # Create mock responses
    mock_post_response = MagicMock()
    mock_post_response.status = 200
    mock_post_response.json = AsyncMock(return_value=post_response_data)
    
    mock_get_response = MagicMock()
    mock_get_response.status = 200
    mock_get_response.json = AsyncMock(return_value=get_response_data)
    
    # Create mock session
    mock_session = MagicMock()
    
    # Mock post context manager
    mock_post_cm = MagicMock()
    mock_post_cm.__aenter__ = AsyncMock(return_value=mock_post_response)
    mock_post_cm.__aexit__ = AsyncMock(return_value=None)
    mock_session.post = MagicMock(return_value=mock_post_cm)
    
    # Mock get context manager
    mock_get_cm = MagicMock()
    mock_get_cm.__aenter__ = AsyncMock(return_value=mock_get_response)
    mock_get_cm.__aexit__ = AsyncMock(return_value=None)
    mock_session.get = MagicMock(return_value=mock_get_cm)
    
    # Mock session context manager
    mock_session_class = MagicMock()
    mock_session_class.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_class.__aexit__ = AsyncMock(return_value=None)
    
    return mock_session_class

# Alias for backwards compatibility
create_mock_aiohttp_session = create_mock_session


@pytest.mark.integration
@pytest.mark.asyncio
async def test_video_manager_initialization():
    """Test VideoGenerationManager initializes correctly"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    assert manager._initialized == True
    assert manager.output_dir.exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runway_text_to_video():
    """Test RunwayML Gen-3 text-to-video generation"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    mock_session = create_mock_session(
        post_response_data={"id": "test-task-123"},
        get_response_data={
            "status": "SUCCEEDED",
            "output": [{"url": "https://runway.ml/video.mp4"}]
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await manager.generate(
            VideoProvider.RUNWAY,
            "A cat walking on a beach at sunset",
            duration=5
        )
        
        assert result["provider"] == "runway"
        assert "url" in result
        assert result["url"] == "https://runway.ml/video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pika_text_to_video():
    """Test Pika 1.5 text-to-video generation"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    mock_session = create_mock_aiohttp_session(
        post_response_data={"job": {"id": "pika-job-456"}},
        get_response_data={
            "job": {
                "status": "finished",
                "result": {"videos": [{"url": "https://pika.art/video.mp4"}]}
            }
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await manager.generate(
            VideoProvider.PIKA,
            "A dog playing in a park",
            duration=5,
            aspect_ratio="16:9"
        )
        
        assert result["provider"] == "pika"
        assert result["url"] == "https://pika.art/video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_luma_text_to_video():
    """Test Luma Dream Machine text-to-video generation"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    mock_session = create_mock_aiohttp_session(
        post_response_data={"id": "luma-gen-789"},
        get_response_data={
            "state": "completed",
            "assets": {"video": "https://luma.ai/video.mp4"}
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await manager.generate(
            VideoProvider.LUMA,
            "A futuristic city at night",
            duration=5,
            aspect_ratio="16:9"
        )
        
        assert result["provider"] == "luma"
        assert result["url"] == "https://luma.ai/video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_kling_text_to_video():
    """Test Kling AI text-to-video generation"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    mock_session = create_mock_aiohttp_session(
        post_response_data={"data": {"task_id": "kling-task-101"}},
        get_response_data={
            "data": {
                "task_status": "succeed",
                "task_result": {"videos": [{"url": "https://klingai.com/video.mp4"}]}
            }
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await manager.generate(
            VideoProvider.KLING,
            "A dragon flying through clouds",
            duration=5,
            aspect_ratio="16:9"
        )
        
        assert result["provider"] == "kling"
        assert result["url"] == "https://klingai.com/video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stable_video_diffusion():
    """Test Stable Video Diffusion via Replicate"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    with patch('replicate.run') as mock_replicate:
        mock_replicate.return_value = "https://replicate.com/stable-video.mp4"
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = MagicMock()
            mock_executor.run_in_executor = AsyncMock(return_value="https://replicate.com/stable-video.mp4")
            mock_loop.return_value = mock_executor
            
            result = await manager.generate(
                VideoProvider.STABLE_VIDEO,
                "Ocean waves crashing on shore"
            )
            
            assert result["provider"] == "stable_video"
            assert "url" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_replicate_generic_model():
    """Test generic Replicate model"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    with patch('replicate.run') as mock_replicate:
        mock_replicate.return_value = ["https://replicate.com/minimax-video.mp4"]
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_executor = MagicMock()
            mock_executor.run_in_executor = AsyncMock(return_value=["https://replicate.com/minimax-video.mp4"])
            mock_loop.return_value = mock_executor
            
            result = await manager.generate(
                VideoProvider.REPLICATE,
                "A robot dancing",
                model="minimax/video-01"
            )
            
            assert result["provider"] == "replicate"
            assert result["url"] == "https://replicate.com/minimax-video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fal_ai_video():
    """Test FAL.ai video generation"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    with patch('fal_client.submit_async') as mock_fal:
        mock_fal.return_value = {
            "video": {"url": "https://fal.ai/video.mp4"}
        }
        
        result = await manager.generate(
            VideoProvider.FAL,
            "A spaceship landing on Mars"
        )
        
        assert result["provider"] == "fal"
        assert result["url"] == "https://fal.ai/video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_heygen_avatar_video():
    """Test HeyGen AI avatar video"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    mock_session = create_mock_aiohttp_session(
        post_response_data={"data": {"video_id": "heygen-vid-202"}},
        get_response_data={
            "data": {
                "status": "completed",
                "video_url": "https://heygen.com/avatar-video.mp4"
            }
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await manager.create_avatar_video(
            VideoProvider.HEYGEN,
            "Hello, I'm an AI avatar!",
            avatar_id="default",
            voice_id="default"
        )
        
        assert result["provider"] == "heygen"
        assert result["url"] == "https://heygen.com/avatar-video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_synthesia_avatar_video():
    """Test Synthesia AI avatar video"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    mock_session = create_mock_aiohttp_session(
        post_response_data={"id": "synthesia-vid-222"},
        get_response_data={
            "status": "complete",
            "download": "https://synthesia.io/avatar-video.mp4"
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await manager.create_avatar_video(
            VideoProvider.SYNTHESIA,
            "Welcome to our presentation!",
            avatar_id="anna_costume1_cameraA"
        )
        
        assert result["provider"] == "synthesia"
        assert result["url"] == "https://synthesia.io/avatar-video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_did_avatar_video():
    """Test D-ID photo-to-talking-video"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    mock_session = create_mock_aiohttp_session(
        post_response_data={"id": "did-talk-333"},
        get_response_data={
            "status": "done",
            "result_url": "https://d-id.com/talking-video.mp4"
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await manager.create_avatar_video(
            VideoProvider.DID,
            "This is amazing AI technology!",
            voice_id="en-US-JennyNeural"
        )
        
        assert result["provider"] == "d_id"
        assert result["url"] == "https://d-id.com/talking-video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runway_image_to_video():
    """Test RunwayML image-to-video"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    # Create test image
    test_image = manager.output_dir / "test_input.png"
    test_image.write_text("fake image data")
    
    mock_session = create_mock_aiohttp_session(
        post_response_data={"id": "runway-i2v-505"},
        get_response_data={
            "status": "SUCCEEDED",
            "output": [{"url": "https://runway.ml/i2v-video.mp4"}]
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b"fake_image_bytes"
            
            result = await manager.image_to_video(
                VideoProvider.RUNWAY,
                str(test_image),
                "Make the image come alive"
            )
            
            assert result["provider"] == "runway"
            assert result["url"] == "https://runway.ml/i2v-video.mp4"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_providers():
    """Test listing all video providers"""
    manager = VideoGenerationManager()
    providers = manager.list_providers()
    
    assert len(providers) == 10
    assert "runway" in providers
    assert "pika" in providers
    assert "luma" in providers
    assert "kling" in providers
    assert "stable_video" in providers
    assert "replicate" in providers
    assert "fal" in providers
    assert "heygen" in providers
    assert "synthesia" in providers
    assert "d_id" in providers


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling_invalid_provider():
    """Test error handling for invalid provider"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    with pytest.raises(ValueError, match="Unsupported video provider"):
        await manager.generate(
            "invalid_provider",  # type: ignore
            "Test prompt"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling_generation_failure():
    """Test error handling when generation fails"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    mock_session = create_mock_aiohttp_session(
        post_response_data={"id": "fail-task"},
        get_response_data={
            "status": "FAILED",
            "failure": "API rate limit exceeded"
        }
    )
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(RuntimeError, match="Generation failed"):
            await manager.generate(
                VideoProvider.RUNWAY,
                "Test prompt"
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cleanup():
    """Test manager cleanup"""
    manager = VideoGenerationManager()
    await manager.initialize()
    
    assert manager._initialized == True
    
    await manager.cleanup()
    
    assert manager._initialized == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
