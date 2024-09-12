import re
import unittest
from argparse import Namespace
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

from streamlink.exceptions import StreamError, StreamlinkDeprecationWarning
from streamlink_cli.compat import stdout
from streamlink_cli.exceptions import StreamlinkCLIError
from streamlink_cli.main import (
    Formatter,
    create_output,
    output_stream,
    resolve_stream_name,
)
from streamlink_cli.output import FileOutput, PlayerOutput


# TODO: rewrite the entire mess


class TestCLIMain(unittest.TestCase):
    def test_resolve_stream_name(self):
        a = Mock()
        b = Mock()
        c = Mock()
        d = Mock()
        e = Mock()
        streams = {
            "160p": a,
            "360p": b,
            "480p": c,
            "720p": d,
            "1080p": e,
            "worst": b,
            "best": d,
            "worst-unfiltered": a,
            "best-unfiltered": e,
        }

        assert resolve_stream_name(streams, "unknown") == "unknown"
        assert resolve_stream_name(streams, "160p") == "160p"
        assert resolve_stream_name(streams, "360p") == "360p"
        assert resolve_stream_name(streams, "480p") == "480p"
        assert resolve_stream_name(streams, "720p") == "720p"
        assert resolve_stream_name(streams, "1080p") == "1080p"
        assert resolve_stream_name(streams, "worst") == "360p"
        assert resolve_stream_name(streams, "best") == "720p"
        assert resolve_stream_name(streams, "worst-unfiltered") == "160p"
        assert resolve_stream_name(streams, "best-unfiltered") == "1080p"


# TODO: don't use Mock() for mocking args, use a custom argparse.Namespace instead
class TestCLIMainCreateOutput(unittest.TestCase):
    @patch("streamlink_cli.main.args")
    @patch("streamlink_cli.main.console", Mock())
    @patch("streamlink_cli.main.DEFAULT_STREAM_METADATA", {"title": "bar"})
    def test_create_output_no_file_output_options(self, args: Mock):
        formatter = Formatter({
            "author": lambda: "foo",
        })
        args.output = None
        args.stdout = None
        args.record = None
        args.record_and_pipe = None
        args.player_fifo = False
        args.player_http = False
        args.title = None
        args.url = "URL"
        args.player = Path("mpv")
        args.player_args = ""
        args.player_env = None

        output = create_output(formatter)
        assert type(output) is PlayerOutput
        assert output.playerargs.title == "URL"
        assert output.env == {}

        args.title = "{author} - {title}"
        output = create_output(formatter)
        assert type(output) is PlayerOutput
        assert output.playerargs.title == "foo - bar"

    @patch("streamlink_cli.main.args")
    @patch("streamlink_cli.main.check_file_output")
    def test_create_output_file_output(self, mock_check_file_output: Mock, args: Mock):
        formatter = Formatter({})
        mock_check_file_output.side_effect = lambda path, force: FileOutput(path)
        args.output = "foo"
        args.stdout = None
        args.record = None
        args.record_and_pipe = None
        args.force = False
        args.fs_safe_rules = None

        output = create_output(formatter)
        assert mock_check_file_output.call_args_list == [call(Path("foo"), False)]
        assert type(output) is FileOutput
        assert output.filename == Path("foo")
        assert output.fd is None
        assert output.record is None

    @patch("streamlink_cli.main.args")
    def test_create_output_stdout(self, args: Mock):
        formatter = Formatter({})
        args.output = None
        args.stdout = True
        args.record = None
        args.record_and_pipe = None

        output = create_output(formatter)
        assert type(output) is FileOutput
        assert output.filename is None
        assert output.fd is stdout
        assert output.record is None

        args.output = "-"
        args.stdout = False
        output = create_output(formatter)
        assert type(output) is FileOutput
        assert output.filename is None
        assert output.fd is stdout
        assert output.record is None

    @patch("streamlink_cli.main.args")
    @patch("streamlink_cli.main.check_file_output")
    def test_create_output_record_and_pipe(self, mock_check_file_output: Mock, args: Mock):
        formatter = Formatter({})
        mock_check_file_output.side_effect = lambda path, force: FileOutput(path)
        args.output = None
        args.stdout = None
        args.record_and_pipe = "foo"
        args.force = False
        args.fs_safe_rules = None

        output = create_output(formatter)
        assert mock_check_file_output.call_args_list == [call(Path("foo"), False)]
        assert type(output) is FileOutput
        assert output.filename is None
        assert output.fd is stdout
        assert type(output.record) is FileOutput
        assert output.record.filename == Path("foo")
        assert output.record.fd is None
        assert output.record.record is None

    @patch("streamlink_cli.main.args")
    @patch("streamlink_cli.main.check_file_output")
    @patch("streamlink_cli.main.DEFAULT_STREAM_METADATA", {"title": "bar"})
    def test_create_output_record(self, mock_check_file_output: Mock, args: Mock):
        formatter = Formatter({
            "author": lambda: "foo",
        })
        mock_check_file_output.side_effect = lambda path, force: FileOutput(path)
        args.output = None
        args.stdout = None
        args.record = "foo"
        args.record_and_pipe = None
        args.force = False
        args.fs_safe_rules = None
        args.title = None
        args.url = "URL"
        args.player = Path("mpv")
        args.player_args = ""
        args.player_env = [("VAR1", "abc"), ("VAR2", "def")]
        args.player_fifo = None
        args.player_http = None

        output = create_output(formatter)
        assert type(output) is PlayerOutput
        assert output.playerargs.title == "URL"
        assert output.env == {"VAR1": "abc", "VAR2": "def"}
        assert type(output.record) is FileOutput
        assert output.record.filename == Path("foo")
        assert output.record.fd is None
        assert output.record.record is None

        args.title = "{author} - {title}"
        output = create_output(formatter)
        assert type(output) is PlayerOutput
        assert output.playerargs.title == "foo - bar"
        assert type(output.record) is FileOutput
        assert output.record.filename == Path("foo")
        assert output.record.fd is None
        assert output.record.record is None

    @patch("streamlink_cli.main.args")
    @patch("streamlink_cli.main.DEFAULT_STREAM_METADATA", {"title": "bar"})
    def test_create_output_record_stdout(self, args: Mock):
        formatter = Formatter({
            "author": lambda: "foo",
        })
        args.output = None
        args.stdout = None
        args.record = "-"
        args.record_and_pipe = None
        args.force = False
        args.fs_safe_rules = None
        args.title = "{author} - {title}"
        args.url = "URL"
        args.player = Path("mpv")
        args.player_args = ""
        args.player_env = [("VAR1", "abc"), ("VAR2", "def")]
        args.player_fifo = None
        args.player_http = None

        output = create_output(formatter)
        assert type(output) is PlayerOutput
        assert output.playerargs.title == "foo - bar"
        assert output.env == {"VAR1": "abc", "VAR2": "def"}
        assert type(output.record) is FileOutput
        assert output.record.filename is None
        assert output.record.fd is stdout
        assert output.record.record is None

    @patch("streamlink_cli.main.args")
    def test_create_output_record_and_other_file_output(self, args: Mock):
        formatter = Formatter({})
        args.output = None
        args.stdout = True
        args.record_and_pipe = True
        with pytest.raises(StreamlinkCLIError) as excinfo:
            create_output(formatter)
        assert str(excinfo.value) == "Cannot use record options with other file output options."
        assert excinfo.value.code == 1

    @patch("streamlink_cli.main.args")
    def test_create_output_no_default_player(self, args: Mock):
        formatter = Formatter({})
        args.output = None
        args.stdout = False
        args.record_and_pipe = False
        args.player = None
        with pytest.raises(StreamlinkCLIError) as excinfo:
            create_output(formatter)
        assert re.search(r"^The default player \(\w+\) does not seem to be installed\.", str(excinfo.value))
        assert excinfo.value.code == 1


class TestCLIMainOutputStream:
    def test_stream_failure_no_output_open(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
        output = Mock()
        stream = Mock(
            __str__=lambda _: "fake-stream",
            open=Mock(side_effect=StreamError("failure")),
        )
        formatter = Mock()

        caplog.set_level(1, "streamlink.cli")

        monkeypatch.setattr("streamlink_cli.main.args", Namespace(retry_open=2))
        monkeypatch.setattr("streamlink_cli.main.output", output)
        monkeypatch.setattr("streamlink_cli.main.create_output", Mock(return_value=output))

        with pytest.raises(StreamlinkCLIError) as excinfo:
            output_stream(stream, formatter)

        assert [(record.levelname, record.module, record.message) for record in caplog.records] == [
            ("error", "main", "Try 1/2: Could not open stream fake-stream (Could not open stream: failure)"),
            ("error", "main", "Try 2/2: Could not open stream fake-stream (Could not open stream: failure)"),
        ]
        assert not output.open.called, "Does not open the output on stream error"
        assert str(excinfo.value) == "Could not open stream fake-stream, tried 2 times, exiting"
        assert excinfo.value.code == 1

    @pytest.mark.parametrize(
        ("args", "isatty", "deprecation", "expected"),
        [
            ({"progress": "yes", "force_progress": False}, True, False, True),
            ({"progress": "no", "force_progress": False}, True, False, False),
            ({"progress": "yes", "force_progress": False}, False, False, False),
            ({"progress": "no", "force_progress": False}, False, False, False),
            ({"progress": "force", "force_progress": False}, False, False, True),
            ({"progress": "yes", "force_progress": True}, False, True, True),
            ({"progress": "no", "force_progress": True}, False, True, True),
        ],
    )
    def test_show_progress(
        self,
        caplog: pytest.LogCaptureFixture,
        recwarn: pytest.WarningsRecorder,
        args: dict,
        isatty: bool,
        deprecation: bool,
        expected: bool,
    ):
        streamio = BytesIO(b"0" * 8192 * 2)
        stream = Mock(open=Mock(return_value=streamio))
        output = Mock()
        formatter = Mock()

        caplog.set_level(1, "streamlink.cli")

        with patch("streamlink_cli.main.sys.stderr.isatty", return_value=isatty), \
             patch("streamlink_cli.main.args", Namespace(retry_open=1, **args)), \
             patch("streamlink_cli.main.console") as mock_console, \
             patch("streamlink_cli.main.output"), \
             patch("streamlink_cli.main.create_output", return_value=output), \
             patch("streamlink_cli.main.StreamRunner") as mock_streamrunner:
            assert output_stream(stream, formatter)

        assert not mock_console.exit.called
        assert [(record.levelname, record.module, record.message) for record in caplog.records] == [
            ("debug", "main", "Pre-buffering 8192 bytes"),
            ("debug", "main", "Writing stream to output"),
        ]
        assert [(record.category, str(record.message)) for record in recwarn.list] == ([(
            StreamlinkDeprecationWarning,
            "The --force-progress option has been deprecated in favor of --progress=force",
        )] if deprecation else [])
        assert mock_streamrunner.call_args_list == [call(streamio, output, show_progress=expected)]
