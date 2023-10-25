import os
from typing import Optional
from tempfile import SpooledTemporaryFile as BaseSpooledTemporaryFile

from aiofiles import open as async_open


class SpooledTemporaryFile(BaseSpooledTemporaryFile):
    """
    A temporary file to store files uploaded by the Form form
    The save method allows you to write temporary data from memory to disk
    """
    async def save(self, destination: Optional[os.PathLike] = None):
        destination = destination or f"./{self.name}"
        dirname = os.path.dirname(destination)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        async with async_open(destination, mode="wb") as f:
            for line in self.readlines():
                await f.write(line)
