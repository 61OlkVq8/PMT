import json
import os


# Please refer to https://stackoverflow.com/questions/56013927/how-to-read-llvm-cov-json-format
# and https://github.com/llvm/llvm-project/blob/master/llvm/tools/llvm-cov/CoverageExporterJson.cpp
class Coverage:
    def __init__(self, jsonFile):
        jsf = os.path.abspath(jsonFile)
        if not os.path.exists(jsf):
            jsf = os.path.expanduser(jsonFile)
        assert(os.path.exists(jsf))
        with open(jsf) as f:
            cov = json.load(f)
        self.covObj = cov['data']

    def hotPath(self, flt=True):
        # flt specifies whether we should ignore non-executed lines
        for export in self.covObj:
            for f in export['files']:
                if flt:
                    fltFunc = lambda x: int(x[2]) > 0
                else:
                    fltFunc = lambda x: True
                for seg in filter(fltFunc, f['segments']):
                    # return the tuple of (filename, line#, exec#)
                    yield((f['filename'], int(seg[0]), int(seg[2])))
