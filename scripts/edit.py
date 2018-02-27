
# edit.py - Edit Distance
#
# Copyright (C) QCRI, 2012
#
# Author: Yifan Zhang
# Revision:
#   25/12/2012 - initial version

import collections

def make_2d_array(ncol, nrow, default_value=None):
    a = [ ]
    for i in range(nrow):
        a.append([ default_value ] * ncol)
    return a

class EditDistance:
    COR = 0
    INS = 1
    DEL = 2
    SUB = 3
    """ 
    """
    def __init__(self, insCost=3.0, delCost=3.0, subCost=4.0, options=None):
        """ 
        """
        self.insCost = insCost
        self.delCost = delCost
        self.subCost = subCost
        self.options = options or {}
        self.acc = {"INS":0, "DEL":0, "SUB":0, "COR":0}
        self.errors = collections.Counter()
        self.compare = 'compare' in self.options and self.options['compare'] or self.compare_default

    @staticmethod
    def compare_default(hyp, ref):
        return hyp.lower() == ref.lower()

    @staticmethod
    def wer(nins, ndel, nsub, ncor):
        return 100.0 * (nins + ndel + nsub) / (ndel + nsub + ncor)

    def detailed_result(self):
        numWords = self.acc['DEL'] + self.acc['SUB'] + self.acc['COR']
        numIns = self.acc['INS']
        numDel = self.acc['DEL']
        numSub = self.acc['SUB']
        numErr = numIns + numDel + numSub
        wer = self.overall_wer()
        return "WER = %(wer).2f%% [ %(numErr)d / %(numWords)d, %(numIns)d ins, %(numDel)d del, %(numSub)d sub ]" % locals()

    def overall_wer(self):
        acc = self.acc
        return 100.0 * (acc["INS"] + acc["DEL"] + acc["SUB"]) / (acc["DEL"] +
                acc["SUB"] + acc["COR"])

    def print_most_common_errors(self, limit=10):
        for (error_type, ref, hyp), count in self.errors.most_common(limit):
            print(error_type, ref, hyp, count)

    def calculate(self, hyp, ref, alignment=None):
        """ 
        """
        nref = len(ref)
        nhyp = len(hyp)

        costs = make_2d_array(nrow=nref + 1, ncol=nhyp + 1, default_value=0.0)
        paths = make_2d_array(nrow=nref + 1, ncol=nhyp + 1)

        for j in range(nhyp + 1):
            costs[0][j] = j * self.insCost
            paths[0][j] = self.INS


        for i in range(nref):
            costs[i+1][0] = (i + 1) * self.delCost
            paths[i+1][0] = self.DEL

            for j in range(nhyp):
                if self.compare(hyp[j], ref[i]):
                    costs[i+1][j+1] = costs[i][j]
                    paths[i+1][j+1] = self.COR
                else:
                    costs[i+1][j+1] = costs[i][j] + self.subCost
                    paths[i+1][j+1] = self.SUB

                if costs[i+1][j] + self.insCost < costs[i+1][j+1]:
                    costs[i+1][j+1] = costs[i+1][j] + self.insCost
                    paths[i+1][j+1] = self.INS

                if costs[i][j+1] + self.delCost < costs[i+1][j+1]:
                    costs[i+1][j+1] = costs[i][j+1] + self.delCost
                    paths[i+1][j+1] = self.DEL

        # back trace
        i = nref
        j = nhyp
        traces = []
        nCor = nSub = nIns = nDel = 0
        errors = []
        while i > 0 or j > 0:
            # traces.append(i, j, paths[i][j])
            if paths[i][j] == self.INS:
                j -= 1
                nIns += 1
                errors.append(('INS', '-', hyp[j]))
                if alignment is not None:
                    alignment.insert(0, ("<INS>", hyp[j]))
            elif paths[i][j] == self.DEL:
                i -= 1
                nDel += 1
                errors.append(('DEL', ref[i], '-'))
                if alignment is not None:
                    alignment.insert(0, (ref[i], "<DEL>"))
            elif paths[i][j] == self.COR:
                i -= 1
                j -= 1
                nCor += 1
                if alignment is not None:
                    alignment.insert(0, (ref[i], hyp[j]))
            elif paths[i][j] == self.SUB:
                i -= 1
                j -= 1
                nSub += 1
                errors.append(('SUB', ref[i], hyp[j]))
                if alignment is not None:
                    alignment.insert(0, (ref[i], hyp[j]))
            else:
                raise

        if self.options['filter']:
          flag = False
          nCor = nSub = nIns = nDel = 0
          for ref, hyp in alignment:
            if ref == '<INS>':
              if flag: nIns += 1
            else:
              flag = self.options['filter'](hyp, ref)

            if hyp == '<DEL>':
              if flag: nDel += 1
            elif self.compare(hyp, ref):
              if flag: nCor += 1
            else:
              if flag: nSub += 1

        self.errors.update(errors)

        self.acc["COR"] += nCor
        self.acc["SUB"] += nSub
        self.acc["INS"] += nIns
        self.acc["DEL"] += nDel
        return self.wer(ncor=nCor, nsub=nSub, nins=nIns, ndel=nDel)
        
