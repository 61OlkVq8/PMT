import re
import os

MutantMatcher = re.compile(r'^(?P<source>[\w\-]+)\_(?P<mutation>[\w\-]+)\_(?P<id>\w+)\.(?P<extension>\w+)$')

def formResultFile(prefix, profiler, src, mut, ident, opt):
    return '_'.join([prefix, profiler, src, mut, ident, opt])


def buildMutantProjectName(prefix, project, src, mut, ident):
    return '_'.join([os.path.join(prefix, project), src, mut, ident])
