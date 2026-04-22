import asyncio

import pytest

from windows_ai.provider_cli_executor import ProviderCLIExecutionError, provider_cli_executor


async def _consume_invalid_provider():
    return await provider_cli_executor.execute_chat(
        target_model="cli:zzz",
        messages=[{"role": "user", "content": "hi"}],
    )


def test_execute_chat_normalizes_invalid_provider_id_error():
    with pytest.raises(ProviderCLIExecutionError, match="Unknown provider: zzz"):
        asyncio.run(_consume_invalid_provider())
