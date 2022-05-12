from funcrun import astarBench, bzip2Bench, gobmkBench, h264refBench, hmmerBench, libquantumBench, mcfBench, omnetppBench, sjengBench, xalancbmkBench
from SecondThought import funcRun
from functools import partial
import pandas as pd
from mutate import Mutate
import os
import operator
from functools import reduce
import json
import random as rand
import name
import subprocess
from collections import defaultdict
import cov
from shutil import copyfile
from multiprocessing.dummy import Pool
from spec_experiments import astarExperiment, bzip2Experiment, gobmkExperiment, h264refExperiment, hmmerExperiment, libquantumExperiment, mcfExperiment, omnetppExperiment, sjengExperiment, xalancbmkExperiment, SpecExperiment
from getCov import astarCov, bzip2Cov, gobmkCov, h264refCov, hmmerCov, libquantumCov, mcfCov, omnetppCov, sjengCov, xalancbmkCov, SpecCov


specCovs = [astarCov, bzip2Cov, gobmkCov, h264refCov, hmmerCov,
                   libquantumCov, mcfCov, omnetppCov, sjengCov, xalancbmkCov]
specProj = ['473.astar', '401.bzip2', '445.gobmk', '464.h264ref', '456.hmmer', '462.libquantum', '429.mcf',
            '471.omnetpp', '458.sjeng', '483.xalancbmk']
specExec = ['astar', 'bzip2', 'gobmk', 'h264ref', 'hmmer', 'libquantum', 'mcf', 'omnetpp', 'sjeng', 'Xalan']
specBench = [astarBench, bzip2Bench, gobmkBench, h264refBench, hmmerBench,
                   libquantumBench, mcfBench, omnetppBench, sjengBench, xalancbmkBench]
specExperiments = [astarExperiment, bzip2Experiment, gobmkExperiment, h264refExperiment, hmmerExperiment,
                   libquantumExperiment, mcfExperiment, omnetppExperiment, sjengExperiment, xalancbmkExperiment]
slowcoach = os.path.expanduser('~/slowcoach/build/slowcoach')


def isNormalWt(fe, tree):
    ent = fe[fe['mut'] == os.path.basename(tree)]
    return len(ent) == 1 and ent['strong'].iloc[0] == 'True'


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
    # step 1: initialize git
    if not os.path.exists(os.path.join(projRoot, '.git')):
        initProc = subprocess.Popen(['git', 'init'], cwd=projRoot,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        initProc.communicate()

        addProc = subprocess.Popen(['git', 'add', '-A'], cwd=projRoot,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = addProc.communicate()

        cmtProc = subprocess.Popen(['git', 'commit', '-m', 'init project'], cwd=projRoot,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = cmtProc.communicate()

    # step 2: generate mutant sources
    if not os.path.exists(mutantsRoot):
        with Mutate(compDB, '10.0.1', mutantsRoot, [],
                    conf, slowcoach) as m:
            m.mutate()
    # step 3: if worktree does not exist, create one
    if os.path.exists(worktrs):
        return list(map(lambda x: os.path.join(worktrs, x), next(os.walk(worktrs))[1]))

    os.mkdir(worktrs)

    # step 4: get sampled mutated source
    #muts = rand.sample(genMut(mutantsRoot), k=120)
    q3Dict = defaultdict(list)
    with open(os.path.join(mutantsRoot, 'slowcoach.log')) as f:
        for l in f:
            line = l.split()
            if line[3] == '<info>:':
                if line[6] == 'Inserting':
                    loc = line[-1].split(':')
                    src = os.path.splitext(loc[0])
                    fn = '_'.join([src[0], line[4][1:-1], line[5][1:-1]])
                    q3Dict[(loc[0], loc[1], loc[2])].append(os.path.join(mutantsRoot,
                        f'{src[0]}_{src[1][1:]}', f'{fn}{src[1]}'))
                elif line[6] == 'Replacing':
                    loc = line[-2][1:].split(':')
                    src = os.path.splitext(loc[0])
                    fn = '_'.join([src[0], line[4][1:-1], line[5][1:-1]])
                    q3Dict[(loc[0], loc[1], loc[2])].append(os.path.join(mutantsRoot,
                        f'{src[0]}_{src[1][1:]}', f'{fn}{src[1]}'))
                else:
                    raise ValueError
    groupedMutDict = dict(q3Dict)
    for k in q3Dict:
        assert(len(q3Dict[k]) >= 4)
        if len(q3Dict[k]) > 4:
            del groupedMutDict[k]
        else:
            assert(len(q3Dict[k]) == 4)
            groupedMutDict[k] = list(map(lambda x: os.path.join(mutantsRoot, x), groupedMutDict[k]))
            for e in groupedMutDict[k]:
                assert(os.path.exists(e))
    allmuts = list(genMut(mutantsRoot))
    # TODO Adjust sampling threshold here
    if len(allmuts) <= 50:
        muts = allmuts
    else:
        selectedKeys = rand.sample(list(groupedMutDict), k=30)
        groupedMuts = list(map(lambda x: groupedMutDict[x], selectedKeys))
        with open(os.path.join(mutantsRoot, 'groupedQ3'), 'w') as f:
            f.write(str(groupedMuts))
        muts = []
        for g in groupedMuts:
            muts += g

    # step 5: find their corresponding source file
    worktreeCmd = ['git', 'worktree', 'add']
    ret = []
    for mut in muts:
        mutName = os.path.basename(mut)
        m = name.MutantMatcher.match(mutName)
        worktree = None
        assert(m is not None)
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
            if not os.path.exists(injectSpot):
                print(injectSpot)
                print(worktree)
            assert(os.path.exists(injectSpot))
            copyfile(mut, injectSpot)
        ret.append(worktree)
    return ret


def buildWorktrees(projRoot, compDB, conf, exe, experiment):
    # FIXME if compDB does not exist create one by bear
    assert(os.path.exists(projRoot))
    dataDir = os.path.join(os.sep.join(projRoot.split(os.sep)[0:-2]), 'data')
    assert(os.path.exists(dataDir))
    resultDir = os.path.join(projRoot, 'performance_results')
    if not os.path.exists(resultDir):
        os.mkdir(resultDir)
    if not os.path.exists(os.path.join(projRoot, exe)):
        if os.path.exists(compDB):
            buildOrig = subprocess.Popen(['make', '-j', '8'], cwd=projRoot,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            buildOrig = subprocess.Popen(['bear', 'make', '-j', '8'], cwd=projRoot,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = buildOrig.communicate()

    return (SpecExperiment(exe, projRoot, resultDir, dataDir, 'O0', True),
            list(map(lambda x: SpecExperiment(exe, x, resultDir, dataDir, 'O0'),
                getProjWorktree(projRoot, compDB, conf))))


def getProfRaw(projArg):
    for projRoot, exe, experiment in projArg:
        assert(os.path.exists(projRoot))
        dataDir = os.path.join(os.sep.join(projRoot.split(os.sep)[0:-2]), 'data')
        assert(os.path.exists(dataDir))
        resultDir = os.sep.join(projRoot.split(os.sep)[0:-2])
        if not os.path.exists(resultDir):
            os.mkdir(resultDir)
        if not os.path.exists(os.path.join(projRoot, exe)):
            buildOrig = subprocess.Popen(['make', '-j', '4'], cwd=projRoot,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = buildOrig.communicate()
        assert(os.path.exists(os.path.join(projRoot, exe)))
        yield experiment(SpecCov(exe, projRoot, resultDir, dataDir, '-O0', True)), os.path.join(projRoot, exe)


def genProf(profraws, exe):
    pre = list(map(lambda x: os.path.dirname(x), profraws))
    assert(len(set(pre)) == 1)
    prPrefix = pre[0]
    for pr in profraws:
        # for each project prPrefix should be the same
        prName = os.path.basename(pr)
        profileName = prName.split('.')[0]

        if not os.path.exists(os.path.join(prPrefix, f'{profileName}.profdata')):
            covProc = subprocess.Popen(['llvm-profdata', 'merge', '-sparse', pr, '-o', f'{profileName}.profdata'],
                    cwd=prPrefix, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            covProc.communicate()
        covProc = subprocess.Popen(['llvm-cov', 'export', f'-instr-profile={profileName}.profdata', exe],
                cwd=prPrefix, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = covProc.communicate()
        yield (profileName, json.loads(out.decode()))


class MutantCoverage:
    def __init__(self, mut, cov):
        self.mut = mut
        self.cov = defaultdict(lambda: False)
        for c in cov:
            self.cov[c[1]] |= c[2]


def mutCov(prefix, muts, covList):
        for m in muts:
            mPath = os.path.join(prefix, m)
            yield(MutantCoverage(mPath, cov.isCovered(cov.getOrigChgs(mPath), covList)))


def mutIsCovered(mutCov):
    for w in mutCov.cov:
        if mutCov.cov[w] is True:
            return True
    return False

def getAllWt(worktrees):
    for wt in worktrees:
        if os.path.exists(wt):
            wtRoot, wts, _ = next(os.walk(wt))
            yield list(map(lambda x: os.path.join(wtRoot, x), wts))
        else:
            yield []

def loadFunceq(f):
    if os.path.exists(f):
        return pd.read_csv(f, names=['orig', 'mut', 'strong', 'weak', 'timeout'])
    else:
        return pd.DataFrame(columns=['orig', 'mut', 'strong', 'weak', 'timeout'])

def main():
    specPrefix = os.path.expanduser('~/cpu06/benchspec/CPU2006')
    configPrefix = os.path.expanduser('~/slowcoach/config')
    specPath = list(map(lambda x: os.path.join(specPrefix, x, 'build', 'build_base_O0.0000'), specProj))
    covPath = list(map(lambda x: os.path.join(specPrefix, x, 'build', 'build_base_cov.0000'), specProj))
    worktrees = list(map(lambda x: os.path.join(x, 'worktrees'), specPath))
    assert(len(specPath) > 0)
    projArg = list(zip(specPath, list(map(lambda x: os.path.join(x, 'compile_commands.json'), specPath)),
        list(map(lambda x: os.path.join(configPrefix, '{}_config.xml'.format(x.split('.')[1])), specProj)),
        specExec, specExperiments))
    exists = reduce(operator.and_, map(lambda x: os.path.exists(x[0]) and os.path.exists(x[1]), projArg), True)
    covConf = os.path.join(configPrefix, 'unopt_cov_setup')

    # First run: Build worktrees
    with Pool(10) as p:
        wtbuilt = p.map(lambda x: buildWorktrees(x[0], x[1], x[2], x[3], x[4]), projArg)
    # FIXME bzip only
    wtbuilt = [None, wtbuilt[0], None, None, None, None, None, None, None, None]

    # Second run: Check coverage
    # covConfProc = subprocess.Popen(['runspec', '-c', covConf], cwd=specPrefix,
    #                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # covConfProc.communicate()
    # # profraw is a list of profraw list of each project returned by cov functions in getCov
    # projArg = list(zip(covPath, specExec, specCovs))
    # profraw  = list(getProfRaw(projArg))
    # prof = map(lambda x: genProf(x[0], x[1]), profraw)
    # projArg = list(zip(specProj, wtbuilt, prof))
    # # FIXME remove next line
    # projArg = [projArg[0]]
    # cwt = []
    # for proj, exp, pr in projArg:
    #     assert(os.path.exists(exp[1][0].worktree))
    #     covLog = os.path.join(specPrefix, proj, 'cov.log')
    #     if not os.path.exists(covLog):
    #         prefix = os.path.dirname(exp[1][0].worktree)
    #         assert(len(list(set(map(lambda x: os.path.dirname(x.worktree), exp[1])))) == 1)
    #         muts = map(lambda x: os.path.basename(x.worktree), exp[1])
    #         covList = list(pr)
    #         st = defaultdict(lambda: 0)
    #         projCov = mutCov(prefix, muts, covList)
    #         coveredMut = list(map(lambda x: x.mut, filter(mutIsCovered, projCov)))
    #         cwt.append(coveredMut)
    #         with open(covLog, 'w') as f:
    #             f.writelines(coveredMut)
    #     else:
    #         with open(covLog) as f:
    #             cwt.append(f.readlines())

    # Third run: Check functional equivalence
    mWt = list(getAllWt(worktrees))
    #projArg = list(zip(cwt, specExec, specBench, specProj, specPath))
    projArg = list(zip(mWt, specExec, specBench, specProj, specPath))
    for wt, exe, bench, proj, path in projArg:
        # assert(os.path.exists(wt) and os.path.isdir(wt))
        assert(len(set(map(os.path.dirname, wt))) == 1)
        prefix = list(set(map(os.path.dirname, wt)))[0]
        muts = list(map(os.path.basename, wt))
        #prefix, muts, _ = next(os.walk(wt))
        origabs = os.path.join(path, exe)
        if not os.path.exists(origabs):
            buildOrig = subprocess.Popen(['make', '-j', '16'], cwd=path,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            buildOrig.communicate()
            # The original project should compile
            assert(buildOrig.returncode == 0)
        orig = list(bench(os.path.join(path, '../', '../'), origabs, 'orig'))
        logfile = os.path.join(os.path.join(path, '../', '../'), 'funceq.csv')

        if not os.path.exists(logfile):
            execFunc = partial(funcRun, prefix, orig, proj, path, bench, exe, logfile)
            list(map(execFunc, muts))
            assert(os.path.exists(logfile))

    # funceq = map(lambda x: pd.read_csv(os.path.join('~/slowcoach/scripts/funceq/',
    #     x.split('.')[1] + '_funceq.csv'), names=['orig', 'mut', 'strong', 'weak', 'timeout']),
    #     specProj)
    funceq = list(map(lambda x: loadFunceq(os.path.join(specPrefix, x, 'funceq.csv')), specProj))

    # Fourth run: Run experiments
    projArg = list(zip(specPath, specExec, specExperiments, wtbuilt, funceq))
    for projRoot, exe, experiment, exps, fe in projArg:
        assert(fe is not None)
        assert(exps[0].isReady())
        wt = list(filter(partial(isNormalWt, fe), map(lambda x: x.worktree, exps[1])))
        experiment(exps[0])
        for e in exps[1]:
            if e.isReady():
                experiment(e)

if __name__ == '__main__':
    main()
