__author__ = 'Kal Ahmed'

from quince.core.qsort import sort_all, sort_modified


def parser(subparsers):
    """
    Adds a parser for the quince sort sub-command
    :param subparsers: The list of quince sub-command parsers to append the resulting parser to
    :return: None
    """
    sort_parser = subparsers.add_parser(
        'sort',
        help='Ensure that the quad files in the Quince repository properly sorted'
    )
    sort_parser.add_argument('--all', '-a',
                             help='Check the sorting of all files even if they are not locally modified',
                             action='store_true')
    sort_parser.add_argument('--since', '-s',
                             help='Check the sorting of all files modified since the specified commit')
    sort_parser.set_defaults(func=main)


def main(args):
    if args.all:
        sort_all()
    else:
        sort_modified(args.since)
    return True