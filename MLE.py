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
        src = np.array([Receiver.srcX, Receiver.srcY, Receiver.srcZ])
        pos = np.array([self.posX, self.posY, self.posZ])
        self.receivedTime = np.linalg.norm(pos - src) / Receiver.c #seconds

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
        
        self.k_distMatrix = 0.5 * np.array([[rec.dist(self.refRec) ** 2 - rec.calcK() + self.refRec.calcK()] \
                                            for rec in self.receivers if rec != self.refRec])
    
        self.distMatrix = np.array([[rec.dist(self.refRec)] for rec in self.receivers if rec != self.refRec])
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
        
        print "OF 1", OF_sol_1
        print "OF_2", OF_sol_2
        
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
        self.D_ref = fsolve(lambda D: self.MLE_D_equation(D), [1, 1])
        return self.HLS_OF_calc()
        
        
    class InvalidInput(Exception):
        pass
        

def calcSrcPosition(D, posArray, k_distArray, distArray):
    return np.matmul(posArray, (distArray * D + k_distArray))

def MLE(rec1, rec2, rec3, rec4):
    posArray = np.array([rec2.pos() - rec1.pos(),
                rec3.pos() - rec1.pos(),
                rec4.pos() - rec1.pos()])
    posArray = -np.linalg.inv(posArray)
    
    distK = np.array([[rec2.dist(rec1) ** 2 - rec2.calcK() + rec1.calcK()],
                      [rec3.dist(rec1) ** 2 - rec3.calcK() + rec1.calcK()],
                      [rec4.dist(rec1) ** 2 - rec4.calcK() + rec1.calcK()]])
    distK = 0.5 * distK
    
    distArray = np.array([[rec2.dist(rec1)],
                   [rec3.dist(rec1)],
                   [rec4.dist(rec1)]])
    
    D1c = (posArray[0,0] * distArray[0] + posArray[0,1] * distArray[1] + posArray[0,2] * distArray[2])
    D2c = (posArray[1,0] * distArray[0] + posArray[1,1] * distArray[1] + posArray[1,2] * distArray[2]) 
    D3c = (posArray[2,0] * distArray[0] + posArray[2,1] * distArray[1] + posArray[2,2] * distArray[2])
    
    D1a = posArray[0,0] * distK[0] + posArray[0,1] * distK[1] + posArray[0,2] * distK[2]
    D2a = posArray[1,0] * distK[0] + posArray[1,1] * distK[1] + posArray[1,2] * distK[2]
    D3a = posArray[2,0] * distK[0] + posArray[2,1] * distK[1] + posArray[2,2] * distK[2]
    
    D = fsolve(lambda D, D1c = D1c, D2c = D2c, D3c = D3c, D1a = D1a, D2a = D2a, D3a = D3a, x1 = rec1.posX, y1 = rec1.posY, z1 = rec1.posZ, K1 = rec1.calcK(): -D ** 2 + (D * D1c + D1a) ** 2 + (D * D2c + D2a) ** 2 + (D * D3c + D3a) ** 2 - 2 * (D * D1c + D1a) * x1 - 2 * (D * D2c + D2a) * y1 - 2 * (D * D3c + D3a)  * z1 + K1 , [-20, 20])
    
    print D
    print calcSrcPosition(max(D), posArray, distK, distArray)
    print "Now MLE class"
    
def main():
    rec1 = Receiver(0.0, 0.0, 0.0)
    rec2 = Receiver(1.5, 0.0, 0.0)
    rec3 = Receiver(0.0, 3.0, 0.0)
    rec4 = Receiver(1.5, 3.0, 0.01)
    
    MLE(rec1, rec2, rec3, rec4)
    m = MLE_HLS(receivers = [rec1, rec2, rec3, rec4])
    print np.around(m.calculate(), decimals = 3)

#profile.run('main()')
main()

