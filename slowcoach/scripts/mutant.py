import os
import name
from copy import copy
import subprocess

class Mutant:
    def __init__(self, mutantsRoot, mutatedSource, origCompilation, sourceRelpath):
        assert(os.path.exists(mutatedSource) and os.path.isfile(mutatedSource))
        m = name.MutantMatcher.match(os.path.basename(mutatedSource)).groupdict()
        assert(m is not None)
        self.sourceFile = m['source']
        self.mutation = m['mutation']
        self.id = m['id']
        worktree = name.buildMutantProjectName(mutantsRoot,
            origCompilation.name, self.sourceFile, self.mutation, self.id)
        worktreeExec = ['git', 'worktree', 'add', worktree]
        workTr = subprocess.Popen(worktreeExec, cwd=mutantsRoot,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        workTr.communicate()
        injectionSpot = os.path.join(worktree, sourceRelpath)
        self.mutationCompilation = copy(origCompilation)
        self.mutationCompilation.pwd = worktree
        self.mutationCompilation.prefix = None
        os.rename(mutatedSource, injectionSpot)
        self.isMutant = True
        self.resultDir = os.path.join(origCompilation.pwd, 'performance_results')
