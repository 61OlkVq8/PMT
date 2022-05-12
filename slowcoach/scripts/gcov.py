import os
import re


branchCvgTy = set('notexec', 'taken', 'nottaken')

def parseCov(cov):
    os.path.abspath(cov)
    ret = dict()
    with open(cov) as f:
        for line in f:
            heads = line.split(':')
            assert(len(heads) == 2)
            if heads[0] == 'file':
                ret['file'] = heads[1]
            elif heads[0] == 'function':
                if ret['function'] is None:
                    ret['function'] = list(dict())
                funcBody = heads[1].split(',')
                assert(len(funcBody) == 3)
                ret['function'].append({'line_number': funcBody[0],
                                        'execution_count': funcBody[1],
                                        'function_name': funcBody[2]})
            elif heads[0] == 'lcount':
                if ret['lcount'] is None:
                    ret['lcount'] = list(dict())
                lcountBody = heads[1].split(',')
                assert(len(lcountBody) == 2)
                ret['lcount'].append({'line_number': lcountBody[0],
                                      'execution_count': lcountBody[1]})
            elif heads[0] == 'branch':
                if ret['branch'] is None:
                    ret['branch'] = dict()
                branchBody = heads[1].split(',')
                assert(len(branchBody) == 2 and branchBody[1] in branchCvgTy)
                ret['lcount'].append({'line_number': branchBody[0],
                                      'branch_coverage_type': branchBody[1]})
            else:
                raise ValueError
    return ret
