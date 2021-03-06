import asyncio
import importlib
import importlib.resources
import inspect
import os
import pathlib
import sys
import unittest

from ...Stream import NullStream, PipeStream
from ...PipelineNode import PipelineProcess
from ...util import which, export

from ..test_util import register, TmpDirMixin

__all__ = []

@export
@register()
class TestConstruct(TmpDirMixin):
    def runTest(self):
        cwd = pathlib.Path(self.tmpdir.name).resolve()
        args = [which('touch'), "tmp.txt"]

        with NullStream(None) as null_stream:
            process = PipelineProcess(
                cwd = cwd,
                env = {},
                args = args,
                stdin_stream = null_stream,
                stdout_stream = null_stream,
                stderr_stream = null_stream
            )

        self.assertEqual(process.cwd, cwd)
        self.assertEqual(process.args, args)

        str(process)
        repr(process)

@export
@register()
class TestCreateAndWait(TmpDirMixin):
    def runTest(self):
        cwd = pathlib.Path(self.tmpdir.name)
        test_file = cwd / 'tmp.txt'
        args = [which('touch'), test_file]

        async def run_and_wait():
            with NullStream(None) as null_stream:
                process = await PipelineProcess.create(
                    cwd = cwd.resolve(),
                    env = {},
                    args = args,
                    stdin_stream = null_stream,
                    stdout_stream = null_stream,
                    stderr_stream = null_stream
                )

            await process.wait()

            return process

        process = asyncio.run(run_and_wait())

        self.assertEqual(process.proc.returncode, 0)
        self.assertTrue(test_file.exists())

@export
@register()
class TestEnvironmentVariableExists(TmpDirMixin):
    def runTest(self):
        cwd = pathlib.Path(self.tmpdir.name)
        from .. import test_util
        with importlib.resources.path(test_util.__package__, 'echo_env.py') as echo_env:
            args = [which('python3'), echo_env]
            message = 'Hello World!'

            async def run_and_wait():
                with NullStream(None) as null_stream, PipeStream(None) as stdout_stream:
                    process = await PipelineProcess.create(
                        cwd = cwd.resolve(),
                        env = {
                            'A': 'wrong output',
                            'MESSAGE': message,
                            'Z': 'wrong output'
                        },
                        args = [which('python3'), echo_env, "MESSAGE"],
                        stdin_stream = null_stream,
                        stdout_stream = stdout_stream,
                        stderr_stream = null_stream
                    )
                    stdout_stream.close_writer()
                    observed = stdout_stream.reader().read()
                    stdout_stream.close()

                await process.wait()

                return process, observed

            process, observed = asyncio.run(run_and_wait())

            self.assertEqual(process.proc.returncode, 0)
            self.assertEqual(message, observed)
