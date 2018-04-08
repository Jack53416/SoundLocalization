import numpy as np
from scipy.optimize import fsolve
import profile

class Receiver(object):
    srcX = 1.0
    srcY = 3.0
    srcZ = 0.0

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
        self.receivedTime = np.linalg.norm(pos - src) / Receiver.c #seconds
    
    @classmethod
    def setSourcePosition(cls, xPos = srcX, yPos = srcY, zPos = srcZ):
        cls.srcX, cls.srcY, cls.srcZ = xPos, yPos, zPos
    
    @classmethod
    def getSourcePosition(cls):
        return np.array([cls.srcX, cls.srcY, cls.srcZ])
    

class MLE_HLS(object):
    def __init__(self, receivers = [], refRecId = 0):
        if len(receivers) != 4 :
            raise InvalidInput("4 receivers required for a=computation")
        self.receivers = receivers
        self.refRec = receivers[refRecId]
        self.setupProfile()
    
    def setupProfile(self):
        self.posMatrix = np.array([rec.pos() - self.refRec.pos() for rec in self.receivers if rec != self.refRec])
        self.posMatrix = -np.linalg.inv(self.posMatrix)
        self.refRec_k = self.refRec.calcK()
        
    def HLS_OF_calc(self): #D - distance between reference antenna and source
        srcPositions = [self.MLE_calc_src(D).flatten() for D in self.D_ref]
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
        
        if OF_sol_2 < OF_sol_1:
            return srcPositions[1]
        return srcPositions[0]
        
    def MLE_calc_src(self, D):
        return np.matmul(self.posMatrix, (self.distMatrix * D + self.k_distMatrix))
        
    def MLE_D_equation(self,D):
        src = self.MLE_calc_src(D)
        Xs, Ys, Zs = src[0], src[1], src[2]
        
        return (-D ** 2 + Xs ** 2 + Ys ** 2 + Zs ** 2 - 2 * Xs * self.refRec.posX - 2 * Ys * self.refRec.posY - \
                2 * Zs * self.refRec.posZ + self.refRec_k)
    
    def calculate(self):
        self.k_distMatrix = 0.5 * np.array([[rec.dist(self.refRec) ** 2 - rec.calcK() + self.refRec_k] \
                                    for rec in self.receivers if rec != self.refRec])
        self.distMatrix = np.array([[rec.dist(self.refRec)] for rec in self.receivers if rec != self.refRec])
        
        self.D_ref = fsolve(lambda D: self.MLE_D_equation(D), [1, 1])
        return self.HLS_OF_calc()
        #return self.MLE_calc_src(max(self.D_ref))
        
    class InvalidInput(Exception):
        pass


class PerformanceTest(object):
    def __init__(self, xRange = 20, yRange = 20, zRange = 20, delta = 0.1):
        self.delta = delta
        self.xRange, self.yRange, self.zRange = xRange, yRange, zRange
        
        receivers = [
                            Receiver(-1.0, -1.0, -1.0),
                            Receiver(-1.0, 1.0, 1.0),
                            Receiver(1.0, 1.0, -1.0),
                            Receiver(1.0, -1.0, -1.0)
                    ]
        self.localizer = MLE_HLS(receivers)
        
        self.xStart, self.yStart, self.zStart = -xRange/2, -yRange/2, -zRange/2

        self.gAccurracy = [] # err <= 0.05
        self.mAccurracy = [] # err <= 0.2
        self.pAccurracy = [] # err <= 1
        self.bAccurracy = [] # err > 1
        
    def excecute(self):
        for xPos in np.arange(self.xStart, self.xStart + self.xRange + self.delta, self.delta):
            #change X pos
            for yPos in np.arange(self.yStart, self.yStart + self.yRange + self.delta, self.delta):
                #change Y pos
                for zPos in np.arange(self.zStart, self.zStart + self.zRange + self.delta, self.delta):
                    #change Z pos
                    self.setupSourcePosition(xPos, yPos, zPos)
                    pos = self.localizer.calculate()
                    self.assesAccuracy(pos)
    
    def setupSourcePosition(self, xPos, yPos, zPos):
        Receiver.setSourcePosition(xPos, yPos, zPos)
        for rec in self.localizer.receivers:
            rec.receive()
    
    def assesAccuracy(self, calcSrcPostion):
        actualPos = Receiver.getSourcePosition()
        err = np.linalg.norm(calcSrcPostion - actualPos)
        if err <= 0.05:
            self.gAccurracy.append(tuple(actualPos))
        elif err <= 0.2:
            self.mAccurracy.append(tuple(actualPos))
        elif err <= 1.0:
            self.pAccurracy.append(tuple(actualPos))
        else:
            self.bAccurracy.append(tuple(actualPos))
        

def main():
    rec1 = Receiver(-1.0, -1.0, -1.0)
    rec2 = Receiver(-1.0, 1.0, 1.0)
    rec3 = Receiver(1.0, 1.0, -1.0)
    rec4 = Receiver(1.0, -1.0, -1.0)
    
    #MLE(rec1, rec2, rec3, rec4)
    m = MLE_HLS(receivers = [rec1, rec2, rec3, rec4])
    res = m.calculate()
    
    print(np.around(res, decimals = 3))

#profile.run('main()')

#main()
p = PerformanceTest(1,1,1, 1)
p.excecute()

print (p.bAccurracy)



