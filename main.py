from argparse import ArgumentParser
from os import getcwd, makedirs
from os.path import getsize, exists, isfile, abspath, isdir, join, basename
from typing import Union, Iterable, Optional, List

__version__ = "0.6.0"


def split_files(filename: str, byte_len: Union[int, Iterable[int]], filename_out: Optional[str] = None,
                out_folder: str = getcwd()) -> List[str]:
    if not exists(out_folder):
        makedirs(out_folder, exist_ok=True)
    elif not isdir(out_folder):
        print(f"{out_folder} is no directory. Specify directory for output")
        exit(1)

    if not hasattr(byte_len, "__iter__"):
        def tmp(tmp_x):
            while True:
                yield tmp_x

        byte_len = tmp(byte_len)
    filename_out = filename_out or "{filename}.fsp.{index}"
    size = getsize(filename)
    index_counter = 1
    wrote_bytes = 0
    file_out = open(join(out_folder, filename_out.format(index=index_counter, filename=basename(filename))), "wb")
    wrote_files = []
    try:
        with open(filename, "rb") as fin:
            read_byte = fin.read(1)
            target_len = next(byte_len)
            counter = 0
            while read_byte != b'':

                if counter >= target_len and (size - wrote_bytes) >= target_len:
                    target_len = next(byte_len)
                    counter = 0
                    if file_out:
                        file_out.close()
                        print(
                            f"Created {index_counter}. part with a size of {target_len}. "
                            f"Wrote {(wrote_bytes / size) * 100:6.2f}% ({wrote_bytes}/{size})")
                        wrote_files.append(abspath(file_out.name))
                    index_counter += 1
                    file_out = open(
                        join(out_folder, filename_out.format(index=index_counter, filename=basename(filename))), "wb")

                file_out.write(read_byte)

                counter += 1
                wrote_bytes += 1
                read_byte = fin.read(1)

    finally:
        if file_out:
            file_out.close()
            wrote_files.append(abspath(file_out.name))

    return wrote_files


def equal_byte_len(filename: str, count_splits: int = 100) -> Iterable[int]:
    storage = 0
    count_splits = int(count_splits)
    size_target = getsize(filename) / count_splits
    while True:
        ret = int(size_target + storage)
        storage = size_target + storage - ret
        yield ret


if __name__ == "__main__":

    __default_pattern = "{filename}.fsp.{index}"

    parser = ArgumentParser(
        description="Split or merge some files into some nice smaller byte files. Super useful. "
                    "Output will be named like <orig_name>.fsp.<index>",
        epilog="Have fun splitting :)")

    parser.add_argument("--version", "-v", action="store_true", dest="version",
                        help="Show version")
    parser.add_argument("--merge", "-m", action="store_true", dest="merge",
                        help="Merge the given files instead of splitting")
    parser.add_argument("--files", "-f", dest="files", nargs="+", default=[],
                        help="Files to split or merge. In split mode every file is split individually. "
                             "In Merge mode all files are merged into one. "
                             "The order in wiich files are worked on is the natural order.")
    parser.add_argument("--count", "-c", dest="count", nargs="?", default=None, type=int,
                        help="Count of files to split into. In split mode this or 'size' has to be set. "
                             "If both are set 'size' will be used. In merge mode this is not used")
    parser.add_argument("--size", "-s", dest="size", nargs="*", default=None, type=int,
                        help="Sizes of files. If not enough sizes are given they are iterated again. "
                             "In split mode this or 'count' has to be set. If both are set this will be used. "
                             "In merge mode this is not used")
    parser.add_argument("--out", "-o", dest="out", nargs="?", default=getcwd(), type=str,
                        help="Specify the folder the file[s] should be written to")
    parser.add_argument("--pattern", "-p", dest="pattern", default=__default_pattern, nargs=1, required=False,
                        help=f"Pattern of outputfiles. Don't use this if you don't know what you are doing. "
                             f"Use python formatted strings to specify format. "
                             f"Use {'{filename}'} to include original name. "
                             f"Use {'{index}'} to include the current index of created file. "
                             f"[Default: '{__default_pattern}']")

    args = parser.parse_args()

    if args.version:
        print(__version__)
        exit(0)

    if not args.merge and (args.size is None and args.count is None):
        parser.error("You have to either specify the count of files to produce or the sizes of files to produce")
        exit(1)

    if args.merge:
        print("Merge mode is not implemented as of yet")
        exit(1)

    else:

        for file_name in (str(x) for x in args.files):
            if not exists(file_name) or not isfile(file_name):
                print(f"File '{file_name}' does not exist or is no file. Please check input")
                continue
            if args.size:
                def tmp(sizes):
                    counter = 0
                    sl = len(sizes)
                    while True:
                        yield sizes[counter % sl]
                        counter += 1


                size_iterator = tmp(args.size)
            else:
                size_iterator = equal_byte_len(file_name, args.count)

            created_files = split_files(filename=file_name,
                                        byte_len=size_iterator,
                                        out_folder=args.out,
                                        filename_out=args.pattern)
            print(f"Did split '{file_name}' into {len(created_files)} files")
