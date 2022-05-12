import filecmp
import os
import argparse
import logging
import subprocess
import re


LinenumMatcher = re.compile('^\<(\d+)\>')


def mutDiff(orig, mut):
    ret = set()
    # Ignore unchanged lines
    diffCmd = ['diff', r'--unchanged-line-format=', r'--new-line-format=<%dn> %L',
               r'--old-line-format=<%dn> %L', orig, mut]
    diffProc = subprocess.Popen(diffCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = diffProc.communicate()
    for line in out.decode('utf-8').splitlines():
        ret.add(int(LinenumMatcher.match(line).group(1)))
    return ret


def main():
    argParser = argparse.ArgumentParser(description='A script to check if mutants change the source code')
    argParser.add_argument('mutants_path',
                           metavar='mutants_path',
                           help='The path to mutants',
                           type=str)
    argParser.add_argument('source_path',
                           metavar='src_path',
                           help='The path to the original source code',
                           type=str)
    args = argParser.parse_args()
    logging.basicConfig(filename='duplicated_mutants.log', level=logging.ERROR)

    mutantsPath = os.path.abspath(args.mutants_path)
    source = os.path.abspath(args.source_path)

    if os.path.isdir(mutantsPath) and os.path.exists(mutantsPath):
        # compare original source and mutants
        mutants = os.listdir(mutantsPath)
        for mut in mutants:
            if filecmp.cmp(source, os.path.join(mutantsPath, mut)):
                logging.error('%s is identical to %s' % (mut, source))

        # for mut1 in mutants:
        #     for mut2 in mutants:
        #         if mut1 != mut2 and filecmp.cmp(os.path.join(mutantsPath, mut1),
        #                 os.path.join(mutantsPath, mut2)):
        #             logging.error('%s is identical to %s' % (mut1, mut2))


if __name__ == '__main__':
    main()
