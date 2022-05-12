import os
import operator
from functools import reduce
from experiments import Experiment
import json
import random as rand
import name
import subprocess
from shutil import copyfile, copytree
from multiprocessing.dummy import Pool
from spec_experiments import *
from functools import partial
import pandas as pd

specProj = ['473.astar', '401.bzip2', '445.gobmk', '464.h264ref', '456.hmmer', '462.libquantum', '429.mcf',
            '471.omnetpp', '458.sjeng', '483.xalancbmk']
specExec = ['astar', 'bzip2', 'gobmk', 'h264ref', 'hmmer', 'libquantum', 'mcf', 'omnetpp', 'sjeng', 'Xalan']
specExperiments = [astarExperiment, bzip2Experiment, gobmkExperiment, h264refExperiment, hmmerExperiment,
                   libquantumExperiment, mcfExperiment, omnetppExperiment, sjengExperiment, xalancbmkExperiment]
slowcoach = os.path.expanduser('~/slowcoach/build/slowcoach')


def getProjWorktree(sampledWt, newWt):
    if not os.path.exists(newWt):
        os.mkdir(newWt)
    # Hardcoded copying old worktrees into the new one
    rt, wt, _ = next(os.walk(sampledWt))
    oldWt = map(lambda x: os.path.join(rt, x), wt)
    assert(os.path.exists(newWt) and os.path.isdir(newWt))
    for owt in oldWt:
        assert(os.path.exists(owt) and os.path.isdir(owt))
        ret = os.path.join(newWt, os.path.basename(owt))
        copytree(owt, ret, dirs_exist_ok=True)
        copyfile(os.path.join(os.path.dirname(newWt), 'Makefile'), os.path.join(ret, 'Makefile'))
        copyfile(os.path.join(os.path.dirname(newWt), 'Makefile.deps'), os.path.join(ret, 'Makefile.deps'))
        copyfile(os.path.join(os.path.dirname(newWt), 'Makefile.spec'), os.path.join(ret, 'Makefile.spec'))
        buildOrig = subprocess.Popen(['make', 'clean'], cwd=ret,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = buildOrig.communicate()
        buildOrig = subprocess.Popen(['make', '-j', '16'], cwd=ret,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = buildOrig.communicate()
        yield ret, buildOrig

def isNormalWt(fe, tree):
    ent = fe[fe['mut'] == os.path.basename(tree)]
    return len(ent) == 1 and ent['strong'].iloc[0] == True

def getFunceq(csvPath):
    if os.path.exists(csvPath):
        return pd.read_csv(csvPath, names=['orig', 'mut', 'strong', 'weak', 'timeout'])
    else:
        return None

def main():
    specPrefix = os.path.expanduser('~/cpu06/benchspec/CPU2006')
    configPrefix = os.path.expanduser('~/slowcoach/config')
    specPath = list(map(lambda x: os.path.join(specPrefix, x, 'build', 'build_base_O3.0000'), specProj))
    sampledWt = list(map(lambda x: os.path.join(specPrefix, x, 'build', 'build_base_O0.0000', 'worktrees'),
        specProj))
    assert(len(specPath) > 0)
    funceq = map(lambda x: getFunceq(os.path.join(specPrefix, x, 'funceq.csv')), specProj)
    projArg = list(zip(specPath,
        list(map(lambda x: os.path.join(configPrefix, '{}_config.xml'.format(x.split('.')[1])), specProj)),
        specExec, specExperiments, sampledWt, funceq))
    exists = reduce(operator.and_, map(lambda x: os.path.exists(x[0]) and os.path.exists(x[1]), projArg), True)

    projArg = list(filter(lambda x: x[-1] is not None, projArg))
    assert(len(projArg) == 1)
    for projRoot, conf, exe, experiment, oldWt, fe in projArg:
        assert(os.path.exists(projRoot) and os.path.exists(conf))
        dataDir = os.path.join(os.sep.join(projRoot.split(os.sep)[0:-2]), 'data')
        assert(os.path.exists(dataDir))
        resultDir = os.path.join(projRoot, 'performance_results')
        if not os.path.exists(resultDir):
            os.mkdir(resultDir)
        if not os.path.exists(os.path.join(projRoot, exe)):
            buildOrig = subprocess.Popen(['make', '-j', '8'], cwd=projRoot,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = buildOrig.communicate()
        if not os.path.exists(os.path.join(projRoot, 'performance_results', 'time_baseline_O3.csv')):
            experiment(SpecExperiment(exe, projRoot, resultDir, dataDir, 'O3', True))

        wtbuild = list(getProjWorktree(oldWt, os.path.join(projRoot, 'worktrees')))
        wt = list(filter(partial(isNormalWt, fe), map(lambda x: x[0], wtbuild)))
        list(map(experiment, map(lambda x: SpecExperiment(exe, x, resultDir, dataDir, 'O3'), wt)))


if __name__ == '__main__':
    main()
