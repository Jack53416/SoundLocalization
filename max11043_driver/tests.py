
class test(object):
    def __init__(self):
        self.counter = 0

    def on_event(self):
        def cb(a,b,c):
            print(a,b,c)
            self.counter = self.counter + 1

        return cb



aTest = test()
cb = aTest.on_event()

cb(1,2,3)
cb(2,3,4)
cb(5,6,7)
print(aTest.counter)