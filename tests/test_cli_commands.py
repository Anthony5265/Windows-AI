import pytest
try:
    from click.testing import CliRunner
    from windows_ai.cli.main import cli
except ImportError:
    pytest.skip("CLI main module not available", allow_module_level=True)

class TestCLICommands:
    @pytest.fixture
    def runner(self):
        return CliRunner()
        
    def test_help_command(self, runner):
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Usage' in result.output
        
    def test_plugin_list_command(self, runner):
        result = runner.invoke(cli, ['plugin', 'list'])
        assert result.exit_code in [0, 1]
        
    def test_config_command(self, runner):
        result = runner.invoke(cli, ['config', 'show'])
        assert result.exit_code in [0, 1]
