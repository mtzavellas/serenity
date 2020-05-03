import datetime
import logging
import mmap
import os
import struct

from pathlib import Path


DEFAULT_MAX_JOURNAL_SIZE = 64 * 1024 * 1024  # 64MB


class NoSpaceException(Exception):
    pass


class NoSuchJournalException(Exception):
    def __init__(self, path: Path):
        super(NoSuchJournalException, self).__init__("Journal file does not exist: {}".format(str(path)))


class MMap:
    def __init__(self, mm):
        self.mm = mm
        self.start_pos = 4
        self.pos = self.start_pos
        self.len = ~struct.unpack('i', self.mm[0:self.start_pos])[0]

    def get_pos(self):
        return self.pos

    def next_pos(self, distance):
        ret = self.pos
        self.advance(distance)
        return ret

    def next_slice(self, distance):
        ret = slice(self.pos, self.pos + distance)
        self.advance(distance)
        return ret

    def advance(self, step: int):
        self.pos += step

        # this is the conservative thing to do: every time we move the pointer forward, update the length
        # however performance-wise it's not ideal because it means a seek() back to start of file plus a
        # second write to the mmap just to ensure data segment length is persisted.
        self.update_length()

    def seek_end(self):
        self.pos = len(self) + self.start_pos

    def update_length(self):
        self.len = self.pos - self.start_pos
        self.mm[0:4] = struct.pack('i', ~self.len)

    def close(self):
        if self.mm:
            self.mm.close()
            self.mm = None

    def __getitem__(self, item):
        return self.mm[item]

    def __setitem__(self, key, value):
        self.mm[key] = value

    def __len__(self):
        return self.len

    def __del__(self):
        return self.close()


class Journal:
    logger = logging.getLogger(__name__)

    def __init__(self, base_path: Path, max_size: int = DEFAULT_MAX_JOURNAL_SIZE):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size

    def create_reader(self, date: datetime.date = datetime.datetime.utcnow().date()):
        return JournalReader(self, self._get_mmap(date, 'r+b'))

    def create_appender(self, date: datetime.date = datetime.datetime.utcnow().date()):
        return JournalAppender(self, self._get_mmap(date, 'a+b'), date)

    def _get_mmap(self, date: datetime.date, mode: str, extending: bool = False) -> MMap:
        mmap_path = self._get_mmap_path(date)
        if not mmap_path.exists():
            if mode != 'r+b':
                # switch to file create mode and create directories if needed
                mmap_path.parent.mkdir(parents=True, exist_ok=True)
                mode = 'w+b'
            else:
                # bail out, cannot read non-existent file
                raise NoSuchJournalException(mmap_path)

        mmap_file = mmap_path.open(mode=mode)
        if mode == 'w+b':
            # zero-fill the entire memory-map file before memory-mapping it
            self.logger.info(f'initializing journal file at {mmap_path}')
            os.write(mmap_file.fileno(), struct.pack('B', 0) * self.max_size)
            mmap_file.flush()

        if mode == 'w+b':
            # store a zero length
            mm = MMap(self._mmap_file(mmap_file))
            mm.update_length()
        elif mode == 'a+b':
            # if necessary extend the file before memory mapping
            if extending:
                self.logger.info(f'extending journal file to {self.max_size} bytes')
                os.truncate(str(mmap_path), self.max_size)

            # memory map and move the pointer to the end
            mm = MMap(self._mmap_file(mmap_file))
            mm.seek_end()
            pos = mm.get_pos()

            self.logger.info(f'recovering journal file from {mmap_path}; starting at position {pos}')
        elif mode == 'r+b':
            mm = MMap(self._mmap_file(mmap_file))
        else:
            raise ValueError(f'undefined mode: {mode}')

        return mm

    def _mmap_file(self, mmap_file):
        return mmap.mmap(mmap_file.fileno(), self.max_size)

    def _get_mmap_path(self, date: datetime.date):
        return self.base_path.joinpath(Path('%4d%02d%02d/journal.dat' % (date.year, date.month, date.day)))


class JournalReader:
    def __init__(self, journal: Journal, mm: MMap):
        self.journal = journal
        self.mm = mm

    def get_length(self):
        return len(self.mm)

    def get_pos(self):
        return self.mm.get_pos()

    def read_byte(self) -> int:
        return self.mm[self.mm.next_pos(1)]

    def read_boolean(self) -> bool:
        return self.read_byte() != 0

    def read_short(self) -> int:
        return self._unpack_next('h', 2)

    def read_int(self) -> int:
        return self._unpack_next('i', 4)

    def read_long(self) -> int:
        return self._unpack_next('q', 8)

    def read_float(self) -> float:
        return self._unpack_next('f', 4)

    def read_double(self) -> float:
        return self._unpack_next('d', 8)

    def read_string(self) -> str:
        val_sz = self._read_stopbit()
        return self.mm[self.mm.next_slice(val_sz)].decode()

    def close(self):
        if self.mm:
            self.mm.close()
            self.mm = None

    def _unpack_next(self, pattern: str, num_bytes: int):
        return struct.unpack(pattern, self.mm[self.mm.next_slice(num_bytes)])[0]

    def _read_stopbit(self) -> int:
        shift = 0
        value = 0
        while True:
            b = self.read_byte()
            value += (b & 0x7f) << shift
            shift += 7
            if (b & 0x80) == 0:
                return value

    def __del__(self):
        self.close()


class JournalAppender:
    logger = logging.getLogger(__name__)

    def __init__(self, journal: Journal, mm: MMap, current_date: datetime.date):
        self.journal = journal
        self.mm = mm
        self.max_size = journal.max_size
        self.current_date = current_date
        self.num_extents = 1

    def write_byte(self, value: int):
        assert value < 256
        val_sz = 1
        self._check_space(val_sz)
        mm = self._get_current_mmap()
        mm[mm.next_pos(1)] = value

    def write_boolean(self, value: bool):
        self.write_byte(1 if value else 0)

    def write_short(self, value: int):
        self._pack_next('h', 2, value)

    def write_int(self, value: int):
        self._pack_next('i', 4, value)

    def write_long(self, value: int):
        self._pack_next('q', 8, value)

    def write_float(self, value: float):
        self._pack_next('f', 4, value)

    def write_double(self, value: float):
        self._pack_next('d', 8, value)

    def write_string(self, value: str):
        encoded = value.encode()
        val_sz = len(encoded)
        self._write_stopbit(val_sz)
        self._check_space(val_sz)
        mm = self._get_current_mmap()
        mm[mm.next_slice(val_sz)] = encoded

    def close(self):
        if self.mm:
            self.mm.update_length()
            data_len = len(self.mm)
            self.logger.info('finalizing JournalAppender; updating data segment length to {}'.format(data_len))
            self.mm.close()
            self.mm = None

    def _pack_next(self, pattern: str, num_bytes: int, value):
        self._check_space(num_bytes)
        mm = self._get_current_mmap()
        mm[mm.next_slice(num_bytes)] = struct.pack(pattern, value)

    def _write_stopbit(self, value):
        if value < 0:
            raise ValueError('Stop-bit encoding does not support negative values')
        mm = self._get_current_mmap()
        while value > 127:
            mm[self.pos] = 0x80 | (value & 0x7f)
            mm.advance(1)
            value >>= 7
        mm[self.mm.next_pos(1)] = value

    # noinspection PyProtectedMember
    def _get_current_mmap(self):
        now_date = datetime.datetime.utcnow().date()
        if self.current_date != now_date:
            # finish writing the file and unmap
            self.close()

            # initialize the new mmap
            self.current_date = now_date
            self.pos = 4
            self.start_pos = self.pos
            self.mm = self.journal._get_mmap(self.current_date, mode='a+b')

        return self.mm

    # noinspection PyProtectedMember
    def _check_space(self, add_length: int):
        if self.mm.get_pos() + add_length >= self.max_size:
            self.mm.close()
            self.max_size += DEFAULT_MAX_JOURNAL_SIZE
            self.mm = self.journal._get_mmap(self.current_date, mode='a+b', extending=True)

    def __del__(self):
        self.close()
