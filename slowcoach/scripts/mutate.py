#!/usr/bin/python3

import argparse
import os
import logging
import json
import subprocess
from pathlib import Path


class Mutate:

    def __init__(self, compDB, clangVer, output='./', include=[],
                 conf=None, executable=None, needDump=False):
        self.compDB = os.path.abspath(compDB)
        self.binary = executable
        self.clangVersion = clangVer
        self.execPrefix = []
        self.include = include
        self.output = output
        self.needDump = needDump
        self.conf = os.path.abspath(conf)

    def fileLookup(self, fname, path):
        for dp, _, fn in os.walk(path):
            if fname in fn:
                return os.path.join(dp, fname)

    def __enter__(self):
        if not os.path.exists(self.output):
            os.mkdir(self.output)

        self.findBinary()
        self.findClangHeaders()
        return self

    def __exit__(self, type, value, tb):
        pass

    def mutate(self):
        # Iterating through compDB to inject our faults
        with open(self.compDB, 'r') as compDBFile:
            compDB = json.load(compDBFile)
            self.execPrefix.append('-p')
            self.execPrefix.append(self.compDB)
            # self.execPrefix.append('-o')
            # self.execPrefix.append(self.output)
            if self.conf is not None:
                self.execPrefix.append('-c')
                self.execPrefix.append(self.conf)
            # FIXME Can we parallelize this?
        for entry in compDB:
            execArgs = list(self.execPrefix)
            execArgs.append(os.path.join(entry['directory'], entry['file']))

            slowcoachInst = subprocess.Popen(execArgs, cwd=self.output,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
            out, err = slowcoachInst.communicate()
            if (self.needDump):
                print(out.decode())
                print(err.decode())
            if not slowcoachInst.returncode == 0:
                logging.error('Error while running on {0}'.format(entry['file']))
                print('Error while running on {0}'.format(entry['file']))
                raise subprocess.CalledProcessError(slowcoachInst.returncode, execArgs)

    def findBinary(self):
        needwritecache = False
        # Checking validity of self.binary
        # If external argument is valid
        if self.binary is not None and os.access(self.binary, os.X_OK):
            needwritecache = True
            # External argument is invalid
        else:
            # Can I open the cache file?
            try:
                with open('.exec_cache', 'r') as cache:
                    self.binary = cache.readline()
            except FileNotFoundError:
                needwritecache = True

            # Cache does not work
            if self.binary is None or len(self.binary) == 0:
                self.binary = self.fileLookup('slowcoach', '/')
                logging.debug('self.binary found in %s' % self.binary)
                # Did we find the right binary?
                if self.binary is None:
                    raise ValueError('Cannot find the SlowCoach self.binary')
                if not os.access(self.binary, os.X_OK):
                    raise ValueError('%s is not a valid SlowCoach self.binary binary' % self.binary)
                needwritecache = True
        if needwritecache:
            with open('.exec_cache', 'w') as cache:
                cache.write(self.binary)
                self.execPrefix.append(self.binary)
        assert(self.binary is not None)

    def findClangHeaders(self):
        # Ummm, we need to look for clang tooling headers
        # Currently (as of 9.0.1) there is a bug for clang tooling that standard headers are not included
        # by default. Therefore we need to add this header manually

        # Theoretically every PATH is somewhat bin/, whose corresponding lib/ is just next to it
        clangIncPrefix = map(lambda x: x + '/../lib/clang', os.getenv('PATH').split(':'))
        clangInc = None
        for prefix in clangIncPrefix:
            if os.path.exists(prefix) and os.path.isdir(prefix):
                # walk one layer
                _, dn, _ = next(os.walk(prefix))
                if self.clangVersion in dn:
                    dp = os.path.join(prefix, self.clangVersion, 'include')
                    if os.path.isdir(dp):
                        clangInc = dp
                        break

        if clangInc is None:
            logging.warning('Cannot find clang headers given version {0}'.format(self.clangVersion))
        if clangInc not in self.include:
            self.include.append(clangInc)
            # Users always need reminds
        if len(self.include) == 0:
            logging.warning('No headers included, clang frontend may probably fail to compile')
        for i in self.include:
            self.execPrefix.append('--extra-arg=-I%s' % i)


def main():
    argParser = argparse.ArgumentParser(description='A user friendly SlowCoach launcher')
    argParser.add_argument('compile_database',
                           metavar='COMPILE DATABASE',
                           help='compilation database file',
                           type=str)
    argParser.add_argument('-i',
                           '--include',
                           help='inclusion paths',
                           type=list,
                           default=[],
                           nargs='+')
    argParser.add_argument('-e',
                           '--executable',
                           help='SlowCoach executable binary',
                           type=str)
    argParser.add_argument('-c',
                           '--configuration',
                           help='the configuration file',
                           type=str)
    argParser.add_argument('-o',
                           '--output',
                           help='output directory',
                           type=str,
                           default='./mutants')
    args = argParser.parse_args()

    # Setup logging
    logging.basicConfig(filename='mutation_{0}.log'.format(str(Path(args.compile_database).parent.stem)),
                        level=logging.INFO)
    with Mutate(args.compile_database, '10.0.1', args.output,
                args.include, args.configuration,
                '{0}/slowcoach/build/slowcoach'.format(os.getenv('HOME')), True) as m:
        m.mutate()


if __name__ == '__main__':
    main()
