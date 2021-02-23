from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import quamash, asyncio, aiohttp, sys
import time
session = None

class MainWin(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        button = QPushButton('Push', clicked=self.clk)
        self.label = QLabel('Content Here')
        self.layout.addWidget(self.label)
        self.layout.addWidget(button)

    def clk(self):
        self.ass = time.time()
        async def get():
            # async with aiohttp.ClientSession(loop=loop) as session:
            # url = 'http://codeforces.com/'
            url = 'http://falseknees.com'
            # url = 'https://api.github.com/users/pluto0x0'
            # url = 'http://myip.ipip.net'
            # for i in range(10):
            async with session.get(url) as respones:
                res = await respones.text()
                print(res[:5])
                print('time used:',time.time() - self.ass)
                    # self.label.setText(res[:50])

        for i in range(10):  
            asyncio.ensure_future(get(), loop=loop)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    loop = quamash.QEventLoop(app)
    asyncio.set_event_loop(loop)
    session = aiohttp.ClientSession(loop=loop)
    mainwin = MainWin()
    mainwin.show()
    async def initSession():
        global session
        session = aiohttp.ClientSession(loop = loop)
    asyncio.ensure_future(initSession(), loop=loop)
    with loop:
        loop.run_forever()