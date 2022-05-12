import os
import logging
import gc

from mutate import Mutate

import json

from shutil import copy
from mutant_checker import mutDiff
from cov import getCovLoc
import summary
import name
import timeutils
from functools import partial
import subprocess
from multiprocessing.dummy import Pool
from mutant import Mutant


def mutantInCoverage(origAbs, cov, mutAbs):
    mutLoc = mutDiff(origAbs, mutAbs)
    covLoc = getCovLoc(cov, origAbs)
    return len(mutLoc.intersection(covLoc)) > 0

def sourceHandler(compilation, mutantsRoot, cov, src):
    ret = None
    if os.path.isabs(src['file']):
        sourceAbs = src['file']
    else:
        assert(src['directory'] is not None)
        sourceAbs = os.path.join(src['directory'], src['file'])
    assert(os.path.exists(sourceAbs) and os.path.isfile(sourceAbs))
    srcMutPath = os.path.join(mutantsRoot, src['file'].replace('.', '_'))
    if os.path.exists(srcMutPath):
        muts = map(partial(os.path.join, srcMutPath),
                next(os.walk(srcMutPath))[2])
        with Pool(32) as mutWorker:
            ret = mutWorker.map(lambda mut: Mutant(mutantsRoot, mut, compilation,
                os.path.relpath(sourceAbs, compilation.pwd)), filter(partial(mutantInCoverage,
                    sourceAbs, cov), muts))
        assert(ret is not None)
    return ret


class Experiment:

    def __init__(self, comp, executable, conf, rep, mutantLockFile='.done'):
        self.compilation = comp
        self.slowcoachInst = executable
        assert(os.path.isabs(self.slowcoachInst))
        self.compDB = None
        self.conf = conf
        self.summary = summary.Summary()
        self.repeats = rep

    # originHandler: what to do with unmodified project (usually get coverage, set baseline etc)
    # mutantHandler: what to do with mutants
    def experiment(self, originHandler, mutantHandler, mutantFilter, sampleFnc=lambda x: x):
        # Make sure the project compiles + generating compile_commands.json
        self.compilation.conf()
        self.compilation.build()
        self.compilation.install()

        if originHandler is not None:
            origCov = originHandler(self.compilation, self.repeats)

        with open(self.compilation.compDB) as f:
            self.compDB = json.load(f)
        mutantsPath = os.path.join(self.compilation.pwd, 'mutants')
        if not os.path.exists(mutantsPath):
            with Mutate(self.compilation.compDB, '10.0.1', mutantsPath, [],
                        self.conf, self.slowcoachInst) as m:
                m.mutate()
        # FIXME Luckily I'm not writing C++ here, but still would be quite SLOW
        mutants = sum(filter(lambda x: x is not None,
            map(partial(sourceHandler, self.compilation, mutantsPath, origCov), self.compDB)), [])
        assert(mutants is not None)
        with Pool(8) as p:
            p.map(partial(mutantHandler, self.repeats), sampleFnc(mutants))
