from mutate import Mutate
import os
import operator
from functools import reduce
import json
import random as rand
# from experiments import Experiment
import name
import subprocess
from shutil import copyfile
from multiprocessing import Pool
from getCov import *
from functools import partial
import cov
from collections import defaultdict
from funcrun import *

specProj = ['473.astar', '401.bzip2', '445.gobmk', '464.h264ref', '456.hmmer', '462.libquantum', '429.mcf',
            '471.omnetpp', '458.sjeng', '483.xalancbmk']
specExec = ['astar', 'bzip2', 'gobmk', 'h264ref', 'hmmer', 'libquantum', 'mcf', 'omnetpp', 'sjeng', 'Xalan']
specCovs = [astarCov, bzip2Cov, gobmkCov, h264refCov, hmmerCov,
                   libquantumCov, mcfCov, omnetppCov, sjengCov, xalancbmkCov]
specBench = [astarBench, bzip2Bench, gobmkBench, h264refBench, hmmerBench,
                   libquantumBench, mcfBench, omnetppBench, sjengBench, xalancbmkBench]
slowcoach = os.path.expanduser('~/slowcoach/build/slowcoach')

class MutantCoverage:
    def __init__(self, mut, cov):
        self.mut = mut
        self.cov = defaultdict(lambda: False)
        for c in cov:
            self.cov[c[1]] |= c[2]
        print(self.mut, self.cov)

# Writes lhs_mut, rhs_mut, strong_eq, weak_eq, timeout
def funcEq(lhs, rhs):
    # Assume lhs and rhs are equal
    weak = True
    strong = True
    assert(len(lhs) > 0 and len(rhs) > 0)
    if len(lhs) != len(rhs):
        return f'{lhs[0].mut}, {rhs[0].mut}, False, False, True'
    comp = list(zip(lhs, rhs))
    for l, r in comp:
        # Sanity check
        assert(l is not None)
        if r.out is None:
            assert(r.err is None)
            return f'{lhs[0].mut},{rhs[0].mut},False,False,True'
        # if output do not match the mutant is neither 
        # strong nor weak equivalent
        strong &= (l.out == r.out)
        weak &= (l.out == r.out)
        strong &= (l.err == r.err)

    return f'{lhs[0].mut},{rhs[0].mut},{strong},{weak},False'

def funcRun(prefix, orig, proj, path, bench, exe, logfile, mut):
    p = os.path.join(prefix, mut, exe)
    if not os.path.exists(os.path.join(prefix, mut, exe)):
        buildProc = subprocess.Popen(['make', '-j', '16'], cwd=path,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        buildProc.communicate()
        if buildProc.returncode != 0:
            print(f'{mut} in {proj} does not compile')
            return
    # If the build fails and not captured by returncode
    if os.path.exists(os.path.join(prefix, mut, exe)):
        mutrun = list(bench(os.path.join(path, '../', '../'), p, mut))
        with open(logfile, 'a') as f:
            f.write(f'{funcEq(orig, mutrun)}{os.linesep}')

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

def mutCov(prefix, muts, covList):
        for m in muts:
            mPath = os.path.join(prefix, m)
            yield(MutantCoverage(mPath, cov.isCovered(cov.getOrigChgs(mPath), covList)))

def main():
    specPrefix = os.path.expanduser('~/cpu06/benchspec/CPU2006')
    configPrefix = os.path.expanduser('~/slowcoach/config')
    covConf = os.path.join(configPrefix, 'unopt_cov_setup')
    specPath = list(map(lambda x: os.path.join(specPrefix, x, 'build', 'build_base_cov.0000'), specProj))
    projPath = list(map(lambda x: os.path.join(specPrefix, x, 'build', 'build_base_O0.0000'), specProj))
    worktrees = map(lambda x: os.path.join(x, 'worktrees'), projPath)
    assert(len(specPath) > 0)
    projArg = list(zip(specPath, specExec, specCovs))
    exists = reduce(operator.and_, map(lambda x: os.path.exists(x[0]) and os.path.exists(x[1]), projArg), True)

    covConfProc = subprocess.Popen(['runspec', '-c', covConf], cwd=specPrefix,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    covConfProc.communicate()
    # profraw is a list of profraw list of each project returned by cov functions in getCov
    profraw  = list(getProfRaw(projArg))
    prof = map(lambda x: genProf(x[0], x[1]), profraw)
    projArg = zip(specProj, worktrees, prof)
    for proj, wt, pr in projArg:
        assert(os.path.exists(wt) and os.path.isdir(wt))
        prefix, muts, _ = next(os.walk(wt))
        covList = list(pr)
        st = defaultdict(lambda: 0)
        projCov = list(mutCov(prefix, muts, covList))
        projCov = None
        # for c in projCov:
        #     for w in c.cov:
        #         if c.cov[w] == True:
        #             st[w] += 1
        # print(proj, st)

    # projArg = list(zip(worktrees, specExec, specBench, specProj, projPath))
    # for wt, exe, bench, proj, path in projArg:
    #     assert(os.path.exists(wt) and os.path.isdir(wt))
    #     prefix, muts, _ = next(os.walk(wt))
    #     origabs = os.path.join(path, exe)
    #     if not os.path.exists(origabs):
    #         buildOrig = subprocess.Popen(['make', '-j', '16'], cwd=path,
    #                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #         buildOrig.communicate()
    #         # The original project should compile
    #         assert(buildOrig.returncode == 0)
    #     orig = list(bench(os.path.join(path, '../', '../'), origabs, 'orig'))
    #     logfile = os.path.join(os.path.join(path, '../', '../'), 'funceq.csv')

    #     execFunc = partial(funcRun, prefix, orig, proj, path, bench, exe, logfile)
    #     with Pool(32) as p:
    #         p.map(execFunc, muts)

if __name__ == '__main__':
    main()
