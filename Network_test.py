from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import quamash, asyncio, aiohttp, sys


class MainWin(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        button = QPushButton('Push', clicked=self.clk)
        self.label = QLabel('Content Here')
        self.layout.addWidget(self.label)
        self.layout.addWidget(button)

    def clk(self):
        async def get():
            async with aiohttp.ClientSession(loop=loop) as sesession:
                async with sesession.get('https://api.github.com/users/pluto0x0') as respones:
                    res = await respones.text()
                    self.label.setText(res[:50])

        asyncio.ensure_future(get(), loop=loop)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    loop = quamash.QEventLoop(app)
    asyncio.set_event_loop(loop)
    mainwin = MainWin()
    mainwin.show()
    with loop:
        loop.run_forever()