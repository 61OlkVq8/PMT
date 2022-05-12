from mutate import Mutate
import os
import operator
from functools import reduce
import json
import random as rand
import name
import subprocess
from shutil import copyfile
from multiprocessing.dummy import Pool
from spec_experiments import *
from functools import partial
import time


# specProj = ['473.astar', '401.bzip2', '445.gobmk', '464.h264ref', '456.hmmer', '462.libquantum', '429.mcf',
#             '471.omnetpp', '458.sjeng', '483.xalancbmk']
# specExec = ['astar', 'bzip2', 'gobmk', 'h264ref', 'hmmer', 'libquantum', 'mcf', 'omnetpp', 'sjeng', 'Xalan']
# specExperiments = [astarExperiment, bzip2Experiment, gobmkExperiment, h264refExperiment, hmmerExperiment,
#                    libquantumExperiment, mcfExperiment, omnetppExperiment, sjengExperiment, xalancbmkExperiment]
specProj = ['473.astar', '401.bzip2', '464.h264ref', '429.mcf', '471.omnetpp', '458.sjeng', '483.xalancbmk']
specExec = ['astar', 'bzip2', 'h264ref', 'mcf', 'omnetpp', 'sjeng', 'Xalan']
specExperiments = [astarExperiment, bzip2Experiment, h264refExperiment, mcfExperiment, omnetppExperiment,
        sjengExperiment, xalancbmkExperiment]
slowcoach = os.path.expanduser('~/slowcoach/build/slowcoach')


def findOrigSrc(mut, root, compDB):
    dh, dt = os.path.split(os.path.dirname(os.path.relpath(mut, root)))
    dt = '.'.join(dt.rsplit('_', 1))
    mutRel = os.path.join(dh, dt)
    for entry in compDB:
        ret = os.path.join(entry['directory'], mutRel)
        if os.path.join(entry['directory'], entry['file']) == ret:
            assert(os.path.exists(ret))
            return ret


def genMut(root):
    ret = []
    rootTuple = os.walk(root)
    # Drop files in mutants/
    _ = next(rootTuple)
    for dirpath, _, filenames in rootTuple:
        ret += list(map(lambda x: os.path.join(dirpath, x), filenames))
    return ret


def getProjWorktree(projRoot, compDB, conf):
    mutantsRoot = os.path.join(projRoot, 'mutants')
    worktrs = os.path.join(projRoot, 'worktrees')
    if not os.path.exists(mutantsRoot):
        with Mutate(compDB, '10.0.1', mutantsRoot, [],
                    conf, slowcoach) as m:
            mutime = time.time()
            m.mutate()
            mutime  = time.time() - mutime
            print(f'{projRoot} mutation_time {mutime}')
    if not os.path.exists(worktrs):
        os.mkdir(worktrs)
    # step1: get sampled mutated source
    muts = rand.sample(genMut(mutantsRoot), k=120)
    # step2: find their corresponding source file
    worktreeCmd = ['git', 'worktree', 'add']
    for mut in muts:
        mutName = os.path.basename(mut)
        m = name.MutantMatcher.match(mutName)
        worktree = None
        try:
            assert(m is not None)
        except AssertionError as ae:
            print(mut)
            print(ae)
            exit(1)
        worktree = name.buildMutantProjectName(worktrs, projRoot.split(os.sep)[-3].split('.')[1],
                m['source'], m['mutation'], m['id'])
        assert(worktree is not None)
        if not os.path.exists(worktree):
            with open(compDB) as f:
                cmpCmds = json.load(f)
            injectSpot = os.path.join(worktree, os.path.relpath(findOrigSrc(mut, mutantsRoot, cmpCmds), projRoot))
            cmd = worktreeCmd + [worktree]
            workTr = subprocess.Popen(cmd, cwd=worktrs,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            workTr.communicate()
            copyfile(mut, injectSpot)
        yield worktree


def main():
    specPrefix = os.path.expanduser('~/cpu06/benchspec/CPU2006')
    configPrefix = os.path.expanduser('~/slowcoach/config')
    specPath = list(map(lambda x: os.path.join(specPrefix, x, 'build', 'build_base_none.0000'), specProj))
    assert(len(specPath) > 0)
    projArg = list(zip(specPath, list(map(lambda x: os.path.join(x, 'compile_commands.json'), specPath)),
        list(map(lambda x: os.path.join(configPrefix, '{}_config.xml'.format(x.split('.')[1])), specProj)),
        specExec, specExperiments))
    exists = reduce(operator.and_, map(lambda x: os.path.exists(x[0]) and os.path.exists(x[1]), projArg), True)

    for projRoot, compDB, conf, exe, experiment in projArg:
        overall_time = time.time()
        # FIXME if compDB does not exist create one by bear
        assert(os.path.exists(projRoot) and os.path.exists(compDB) and os.path.exists(conf))
        dataDir = os.path.join(os.sep.join(projRoot.split(os.sep)[0:-2]), 'data')
        assert(os.path.exists(dataDir))
        resultDir = os.path.join(projRoot, 'performance_results')
        if not os.path.exists(resultDir):
            os.mkdir(resultDir)
        if not os.path.exists(os.path.join(projRoot, exe)):
            buildOrig = subprocess.Popen(['make', '-j', '4'], cwd=projRoot,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = buildOrig.communicate()
        dummy = SpecExperiment(exe, projRoot, resultDir, dataDir, '-O0', True)

        wtime = time.time()
        wt = list(getProjWorktree(projRoot, compDB, conf))
        wtime = time.time() - wtime
        print(f'{projRoot} worktree_time {wtime}')

        mut_build_time = time.time()
        with Pool(16) as p:
        #     p.map(experiment, map(lambda x: SpecExperiment(exe, x, resultDir, dataDir, '-O0'), wt))
            p.map(lambda x: SpecExperiment(exe, x, resultDir, dataDir, '-O0'), wt)
        mut_build_time = time.time() - mut_build_time
        print(f'{projRoot} mutants_build_time {mut_build_time}')
        overall_time = time.time() - overall_time
        print(f'{projRoot} overall_time {overall_time}')


if __name__ == '__main__':
    main()
