import json
from unidiff import PatchSet
import subprocess
import os
import gc

def getOrigChgs(mutRoot):
    diffProc = subprocess.Popen(['git', 'diff', '-U0'],
            cwd=mutRoot, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = diffProc.communicate()[0].decode()
    patch = PatchSet(out)
    for f in patch:
        for hunk in f:
            yield (f.path, hunk.source_start)

def isCovered(fl, covList):
    ret = []
    gc.collect()
    for mutSrc, l in fl:
        assert(len(covList) > 0)
        for covName, cov in covList:
            assert(len(cov['data']) > 0)
            foundFile = False
            for export in cov['data']:
                for f in export['files']:
                    if f['filename'].endswith(mutSrc):
                        foundFile = True
                        segments = f['segments']
                        idx = list(range(len(segments)))
                        if len(idx) == 1:
                            assert(segments[0][0] <= l)
                            ret.append((mutSrc, covName, segments[0][3]))
                        else:
                            foundSeg = False
                            covered = False
                            if l < segments[0][0]:
                                ret.append((mutSrc, covName, False))
                                break
                            for i in idx[1:]:
                                # segments[i][3] is whether the segment is executed
                                # segments[i][4] is whether the segment is a macro expansion

                                # If the previous segment starting line number <= l
                                # and the current segment starting line number > l,
                                # the hunk belongs to the previous segment
                                # So record if the previous segment is executed
                                assert(segments[i-1][0] <= segments[i][0])
                                if segments[i-1][0] <= l and segments[i][0] >= l:
                                    foundSeg = True
                                    covered = segments[i-1][3]
                                    while i < len(idx) and segments[i-1][0] == segments[i][0]:
                                        covered |= segments[i][3]
                                        i = i + 1
                                    ret.append((mutSrc, covName, covered))
                                    break
                            if not foundSeg:
                                try:
                                    assert(l >= segments[i-1][0] and l >= segments[i][0])
                                except AssertionError as ae:
                                    print(l)
                                    print(segments[i-1][0])
                                    print(segments[i][0])
                                    print(f['filename'])
                                    raise ae
                                covered = segments[i][3]
                                while i > 0 and segments[i-1][0] == segments[i][0]:
                                    covered |= segments[i-1]
                                    i = i - 1
                                ret.append((mutSrc, covName, covered))
                                break
                        # Found the file. Stop iterating
                        break
            assert(foundFile)

    assert(len(ret) > 0)
    return ret

# FIXME This is buggy
def getCovLoc(cov, src):
    ret = set()
    # Please refer to https://stackoverflow.com/questions/56013927/how-to-read-llvm-cov-json-format
    for export in cov['data']:
        for f in export['files']:
            if f['filename'] == src:
                for seg in f['segments']:
                    # seg[3] is whether the segment is executed
                    # seg[4] is whether the segment is a macro expansion
                    if seg[3] == True:
                        ret.add(int(seg[0]))
    return ret
