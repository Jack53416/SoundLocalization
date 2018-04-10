import numpy as np
from scipy.optimize import fsolve
from enum import Enum
import profile

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import gridspec

class Receiver(object):
    srcX = -8.0
    srcY = 5.0
    srcZ = 6.0

    c = 340 #m/x
    
    def __init__(self, posX, posY, posZ, receivedTime = 0):
        self.posX, self.posY, self.posZ = posX, posY, posZ
        self.receive()
    
    def pos(self):
        return np.array([self.posX, self.posY, self.posZ])
    
    def dist(self, other):
        return (self.receivedTime - other.receivedTime) * Receiver.c
    
    def calcK(self):
        return self.posX ** 2 + self.posY ** 2 + self.posZ ** 2
    
    def receive(self):
        src = Receiver.getSourcePosition()
        pos = np.array([self.posX, self.posY, self.posZ])
        self.receivedTime = np.round(np.linalg.norm(pos - src) / Receiver.c, 4) #seconds
    
    @classmethod
    def setSourcePosition(cls, xPos = srcX, yPos = srcY, zPos = srcZ):
        cls.srcX, cls.srcY, cls.srcZ = xPos, yPos, zPos
    
    @classmethod
    def getSourcePosition(cls):
        return np.array([cls.srcX, cls.srcY, cls.srcZ])
    

class MLE(object):
    class Mode(Enum):
        MLE_MINUS = 0
        MLE_PLUS = 1
        MLE_HLS = 2

    def __init__(self, receivers = [], refRecId = 0, mode = Mode.MLE_HLS) :
        if len(receivers) != 4 :
            raise InvalidInput("4 receivers required for a=computation")
        self.receivers = receivers
        self.refRec = receivers[refRecId]
        self.setupProfile()
        self.estimatedPositions = []
        self.chosenRootIdx = None
        if not isinstance(mode, Enum):
            raise InvalidInput("Mode is not instance of MLE.Mode enum class")
        
        self.mode = mode
    
    def setupProfile(self):
        self.posMatrix = np.array([rec.pos() - self.refRec.pos() for rec in self.receivers if rec != self.refRec])
        self.posMatrix = -np.linalg.inv(self.posMatrix)
        self.refRec_k = self.refRec.calcK()
        
    def HLS_OF_calc(self): #D - distance between reference antenna and source
        srcPositions = [self.calcSrc(D).flatten() for D in self.D_ref]
        d_array_sol_1 = [np.linalg.norm(rec.pos() - srcPositions[0]) for rec in self.receivers]
        d_array_sol_2 = [np.linalg.norm(rec.pos() - srcPositions[1]) for rec in self.receivers]
        
        OF_sol_1 = []
        OF_sol_2 = []
        
        for i in range(0, len(self.receivers)):
            if self.receivers[i] == self.refRec:
                continue
            OF_sol_1.append((d_array_sol_1[i] - self.D_ref[0] - self.refRec.dist(self.receivers[i])) ** 2)
            OF_sol_2.append((d_array_sol_2[i] - self.D_ref[1] - self.refRec.dist(self.receivers[i])) ** 2)

        OF_sol_1 = sum(OF_sol_1)
        OF_sol_2 = sum(OF_sol_2)
        
        #print("OF 1", OF_sol_1)
        #print("OF_2", OF_sol_2)
        self.estimatedPositions = srcPositions
        
        if OF_sol_2 < OF_sol_1:
            self.chosenRootIdx = 1
            return srcPositions[1]
        self.chosenRootIdx = 0
        return srcPositions[0]
        
    def calcSrc(self, D):
        return np.matmul(self.posMatrix, (self.distMatrix * D + self.k_distMatrix))
        
    def MLE_D_equation(self,D):
        src = self.calcSrc(D)
        Xs, Ys, Zs = src[0], src[1], src[2]
        
        return (-D ** 2 + Xs ** 2 + Ys ** 2 + Zs ** 2 - 2 * Xs * self.refRec.posX - 2 * Ys * self.refRec.posY - \
                2 * Zs * self.refRec.posZ + self.refRec_k)
    
    def calculate(self):
        self.k_distMatrix = 0.5 * np.array([[rec.dist(self.refRec) ** 2 - rec.calcK() + self.refRec_k] \
                                    for rec in self.receivers if rec != self.refRec])
        self.distMatrix = np.array([[rec.dist(self.refRec)] for rec in self.receivers if rec != self.refRec])
        
        self.D_ref = fsolve(lambda D: self.MLE_D_equation(D), [-40, 40])
        
        if self.mode == self.Mode.MLE_HLS:
            return self.HLS_OF_calc()
        elif self.mode == self.Mode.MLE_PLUS:
            return self.calcSrc(max(self.D_ref)).flatten()
        return self.calcSrc(min(self.D_ref)).flatten()
    
    def getOtherSolution(self):
        if self.chosenRootIdx == 0:
            return self.estimatedPositions[1]
        return self.estimatedPositions[0]
    
    class InvalidInput(Exception):
        pass


class PerformanceTest(object):
    def __init__(self, xRange = 20, yRange = 20, zRange = 20, delta = 0.1, allRoots = False, mleMode = MLE.Mode.MLE_HLS):
        self.delta = delta
        self.xRange, self.yRange, self.zRange = xRange, yRange, zRange
        
        receivers = [
                            Receiver(-1.5, -1.5, -1.5),
                            Receiver(-1.5, 1.5, 1.5),
                            Receiver(1.5, 1.5, -1.5),
                            Receiver(1.5, -1.5, -1.5)
                    ]
        self.localizer = MLE(receivers, mode = mleMode)
        
        self.xStart, self.yStart, self.zStart = -xRange/2, -yRange/2, -zRange/2

        self.gAccurracy = [] # err <= 0.05
        self.mAccurracy = [] # err <= 0.2
        self.pAccurracy = [] # err <= 1
        self.bAccurracy = [] # err > 1
        
        self.allRoots = allRoots
        
    def excecute(self):
        for xPos in np.arange(self.xStart, self.xStart + self.xRange + self.delta, self.delta):
            #change X pos
            print(xPos)
            for yPos in np.arange(self.yStart, self.yStart + self.yRange + self.delta, self.delta):
                #change Y pos
                for zPos in np.arange(self.zStart, self.zStart + self.zRange + self.delta, self.delta):
                    #change Z pos
                    self.setupSourcePosition(xPos, yPos, zPos)
                    pos = self.localizer.calculate()
                    #print(pos)
                    self.assesAccuracy(pos)
    
    def setupSourcePosition(self, xPos, yPos, zPos):
        Receiver.setSourcePosition(xPos, yPos, zPos)
        for rec in self.localizer.receivers:
            rec.receive()
    
    def assesAccuracy(self, calcSrcPostion):
        actualPos = Receiver.getSourcePosition()
        err = np.linalg.norm(calcSrcPostion - actualPos)
        
        if self.allRoots:
            err2 = np.linalg.norm(self.localizer.getOtherSolution() - actualPos)
            err = min(err, err2)
        
        if err <= 0.05:
            self.gAccurracy.append(tuple(actualPos))
        elif err <= 0.2:
            self.mAccurracy.append(tuple(actualPos))
        elif err <= 1.0:
            self.pAccurracy.append(tuple(actualPos))
        else:
            self.bAccurracy.append(tuple(actualPos))
    
    def plot(self):
        fig = plt.figure(figsize = (8,6))
        gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1]) 
        ax0 = plt.subplot(gs[0], projection = '3d')
        gAccurracy = np.array(self.gAccurracy)
        mAccurracy = np.array(self.mAccurracy)
        pAccurracy = np.array(self.pAccurracy)
        bAccurracy = np.array(self.bAccurracy)
        
        if len(gAccurracy) > 0:
            ax0.scatter(gAccurracy[:,0], gAccurracy[:,1], gAccurracy[:, 2], c = 'g', marker = 'o')
        if len(mAccurracy) > 0:
            ax0.scatter(mAccurracy[:,0], mAccurracy[:,1], mAccurracy[:, 2], c = 'y', marker = 'o')
        if len(pAccurracy) > 0:
            ax0.scatter(pAccurracy[:,0], pAccurracy[:,1], pAccurracy[:, 2], c = 'orange', marker = 'o')
        if len(bAccurracy) > 0:
            ax0.scatter(bAccurracy[:,0], bAccurracy[:,1], bAccurracy[:, 2], c = 'r', marker = 'o')
        
        
        ax0.set_xlabel('X[m]')
        ax0.set_ylabel('Y[m]')
        ax0.set_zlabel('Z[m]')
        
        self.calcStats()
        ax1 = plt.subplot(gs[1])
        explode = (0.1, 0, 0 ,0)
        labels = ['{0} - {1:1.2f} %'.format(i,j) for i,j in zip(self.captions, self.percentage)]

        patches, text = ax1.pie(self.percentage, explode = explode, shadow = True, startangle = 90, 
                                colors = ['g', 'y', 'orange', 'r'])
        
        patches, labels, dummy =  zip(*sorted(zip(patches, labels, self.percentage),
                                          key=lambda x: x[2],
                                          reverse=True))
        
        
        ax1.legend(patches, labels, loc='lower center', bbox_to_anchor=(0.5, 0.1),
           fontsize=8)

        ax1.axis('equal')
        
        plt.tight_layout()
        plt.show()
    
    def calcStats(self):
        self.captions = ["Good", "Medium", "Poor", "Bad"]
        lengths = np.array([len(self.gAccurracy), len(self.mAccurracy), len(self.pAccurracy), len(self.bAccurracy)])
        total = sum(lengths)
        self.percentage = np.round(lengths / total * 100, 5)
        #print(dict(zip(captions, percentage)))
        
        
        

def main():
    rec1 = Receiver(-1.0, -1.0, -1.0)
    rec2 = Receiver(-1.0, 1.0, 1.0)
    rec3 = Receiver(1.0, 1.0, -1.0)
    rec4 = Receiver(1.0, -1.0, -1.0)
    
    #MLE(rec1, rec2, rec3, rec4)
    m = MLE(receivers = [rec1, rec2, rec3, rec4])
    res = m.calculate()
    
    print(np.around(m.calcSrc(m.D_ref), decimals = 3))
    #print(np.around(res, decimals = 3))
#profile.run('main()')

#main()
p = PerformanceTest(3,3,3,0.1, allRoots = False, mleMode = MLE.Mode.MLE_HLS)
p.excecute()
p.plot()
#print(p.bAccurracy)




