# PyQt
from PyQt5.Qt import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
# UI
import ui.net, ui.login, ui.lists, ui.pattern, ui.sublist, ui.listItem

import qtawesome as qta
import xmlrpc.client as rpc
import mutagen.flac, mutagen.id3
import requests, time, re, os, platform, hashlib, sys, subprocess, json
import quamash, asyncio, aiohttp

LogFileName = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
LogFile = open(f'log/{LogFileName}.log', 'w')
# log文件


def log(*args, **kwargs):
    print('[' + time.asctime(time.localtime(time.time())) + ']', file=LogFile)
    print(*args, **kwargs, file=LogFile)


OS = platform.platform()
# OS信息
isWindows = re.match('windows', OS, re.I) != None
# 判断是否Windows系统
log('systeminfo:', OS)

CHECKS = [
    'songCheck', 'picCheck', 'lrcCheck', 'skipCheck', 'tagCheck', 'lrcFormatCheck', 'radioButton', 'radioButton_2',
    'radioButton_3'
]
# 需要保存状态的控件列表

conf = {
    'baseURL': 'http://app.yzzzf.xyz:3000',
    'loginName': '',
    'cookie': '',
    'nickname': '',
    'avatarURL': '',
    'patternStr': '{artist}-{name}-{album}',
    'maxLen': 50,
    'maxDownload': 6,
    'noneLyric': r'[00:00.000]纯音乐，请您欣赏',
    'path': os.path.abspath('./output'),
    'widget': {
        'checks': {check: True
                   for check in CHECKS}
    }
}
# 初始配置，如果没有已保存的配置则使用
confName = 'config.json'

# NoCache = False

if not os.path.exists(conf['path']):
    conf['path'] = os.path.abspath('.')
    log('path in config do not exitst.changed to', conf['path'])
    # os.mkdir(conf['path'])

rpcServer = rpc.ServerProxy('http://localhost:6888/rpc')
# rpc连接实例

try:
    with open(confName, encoding='utf-8') as confFile:
        conf = json.loads(confFile.read())
except FileNotFoundError:
    # 找不到config文件
    log('config file do not exist. use default one.')
    pass
except json.decoder.JSONDecodeError:
    # config文件decode错误
    log('decode config json file error. use default one.')
    pass

allLrc = re.compile(r'^(\[\d+:\d+\.\d+\])', re.M)
# 匹配lrc所有头
lrcReg = re.compile(r'^(\[\d+:\d+\.\d{2})(\d+)(\])', re.M)
# 匹配三位lrc头


def lrcMerge(a, b):
    # 合并歌词
    aa = allLrc.split(a)
    bb = allLrc.split(b)
    out = ''
    for i in range(1, len(aa), 2):
        try:
            index = bb.index(aa[i])
            aa[i + 1] = aa[i + 1][:-1] + ' ' + bb[index + 1]
        except ValueError:
            pass
    return ''.join(aa)


def fileStr(str):
    # 文件名转换
    dic = {'*': '＊', '/': '／', '\\': '＼', ':': '：', '"': '＂', '?': '？', '>': '＞', '＜': '＜', '|': '｜'}
    for key in dic:
        str = str.replace(key, dic[key])
    return str


aria2 = None
aria2_log = open('aria2.log', 'a')
aria2_err = open('aria2.err', 'a')


def startAria2():
    # 启动Aria2
    global aria2
    kwargs = {'stdout': aria2_log, 'stderr': aria2_err, 'stdin': subprocess.PIPE}
    if isWindows:
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        # 该参数仅用于windows系统
    aria2 = subprocess.Popen([r'aria2c', r'--conf-path', r'aria2.conf'], **kwargs)
    # QMessageBox.critical(self, '错误', 'aria2 启动失败，请重试。')


session = None
httpProxy = 'http://49.75.59.242:3128'


class LoginChildWindow(QDialog, ui.login.Ui_Dialog):
    # 登录窗口
    def __init__(self):
        super(LoginChildWindow, self).__init__()
        self.setupUi(self)

        self.skipBtn.clicked.connect(self.close)
        self.loginBtn.clicked.connect(self.login)
        txtChange = lambda: self.loginBtn.setEnabled(self.actEdit.text() != '' and self.pwdEdit.text() != '')
        self.actEdit.textChanged.connect(txtChange)
        self.pwdEdit.textChanged.connect(txtChange)
        txtChange()
        # 绑定按钮槽函数

        try:
            self.actEdit.setText(conf['loginName'])
            log('cached username:', conf['loginName'])
        except KeyError:
            log('no cached username.')
            pass

    # 登录请求
    def login(self):
        self.loginBtn.setEnabled(False)
        conf['loginName'] = self.actEdit.text()

        url = conf['baseURL'] + '/login/'
        params = {'password': self.pwdEdit.text()}

        if self.isPhone.isChecked():
            url = url + 'cellphone'
            params['phone'] = self.actEdit.text()
        else:
            url = url + 'email'
            params['email'] = self.actEdit.text()

        if httpProxy:
            params['proxy'] = httpProxy
            log('use http proxy:', httpProxy)

        async def get():
            async with session.get(url, params=params) as respones:
                res = await respones.json()
                self.loginBtn.setEnabled(True)

                if res['code'] == 200:
                    conf['nickname'] = res['profile']['nickname']
                    conf['cookie'] = res['cookie']
                    conf['avatarURL'] = res['profile']['avatarUrl']

                    log('login successed:', conf['nickname'])
                else:
                    errorMsg = '登录失败（{0}）\n{1}'.format(data['code'], data['msg'] if data['code'] != 400 else '')
                    log('login failed', errorMsg)

                    QMessageBox.critical(self, '登录失败', errorMsg)

                self.accept()

        asyncio.ensure_future(get(), loop=loop)


class fuckerd(ui.sublist.Ui_Form, QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


# 用户歌单窗口类
class ListChildWindow(QDialog, ui.lists.Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.exitBtn.clicked.connect(self.close)
        self.xx = fuckerd()
        self.gridLayout.addChildWidget(self.xx)


class ListItem(QWidget, ui.listItem.Ui_Form):
    def __init__(self, title):
        super().__init__()
        self.setupUi(self)
        self.titleLabel.setText(title)
        self.folderButton.setIcon(qta.icon('fa5.folder', scale_factor=1))
        self.deleteButton.setIcon(qta.icon('fa.trash-o', scale_factor=1))
        self.pauseButton.setIcon(qta.icon('fa.pause', scale_factor=1))
        self.folderButton.setEnabled(False)
        self.deleteButton.setEnabled(False)
        self.pauseButton.setEnabled(False)


class WriteTagThread(QThread):
    always = pyqtSignal(str)
    final = pyqtSignal()

    def __init__(self, songs, config={
        'ID3v2x': 3,
    }):
        super().__init__()
        self.songs = songs
        self.config = config

    def run(self):
        for song in self.songs:
            ret = '写入完成。'
            print(song['name'])
            try:
                if song['type'] == 'mp3':
                    tag = mutagen.id3.ID3()
                    img = open(conf['path'] + '/' + song['filename'] + '.jpg', 'rb')
                    if self.config['ID3v2x'] == '3':
                        tag.update_to_v23()
                    tag['APIC'] = mutagen.id3.APIC(  #插入专辑图片
                        encoding=0,  # ass hole, for sony A35
                        mime=u'image/jpeg',
                        type=mutagen.id3.PictureType.COVER_FRONT,
                        desc='Cover',
                        data=img.read())
                    tag['TPE1'] = mutagen.id3.TPE1(  #插入第一演奏家、歌手、等
                        encoding=3, text=[song['artist']])
                    tag['TALB'] = mutagen.id3.TALB(  #插入专辑名称
                        encoding=3, text=[song['album']])
                    tag['TIT2'] = mutagen.id3.TIT2(  #插入歌名
                        encoding=3, text=[song['name']])
                    tag['TYER'] = mutagen.id3.TYER(  #插入专辑名称
                        encoding=3, text=[song['year']])

                    v2x = 4
                    WriteID1 = 1

                    tag.save(conf['path'] + '/' + song['filename'] + '.mp3', v1=WriteID1, v2_version=v2x)
                    img.close()

                elif song['type'] == 'flac':
                    audio = mutagen.flac.FLAC(conf['path'] + '/' + song['filename'] + '.flac')
                    audio.delete()
                    audio['title'] = song['name']
                    audio['album'] = song['album']
                    audio['artist'] = song['artist']
                    audio['date'] = song['year']

                    img = mutagen.flac.Picture()
                    with open(conf['path'] + '/' + song['filename'] + '.jpg', 'rb') as fil:
                        img.data = fil.read()
                    img.type = mutagen.id3.PictureType.COVER_FRONT
                    img.mime = u"image/jpeg"
                    img.desc = u'Cover'

                    audio.add_picture(img)
                    audio.save()
                else:
                    ret = '格式未知。'
            except BaseException as e:
                ret = f'写入错误:{repr(e)}。'
            self.always.emit(f'{song["filename"]}.{song["type"]} {ret}')
        self.final.emit()


class WriteLrcThread(QThread):
    always = pyqtSignal(str)
    res = {}
    lrcType = ()

    def __init__(self, res, lrcType=(True, False, False), lrcformat=False):
        super().__init__()
        self.res = res
        self.lrcType = lrcType
        self.lrcformat = lrcformat

    def run(self):
        data = self.res['ret']
        filename = self.res['data']
        lrc = ''
        try:
            if data['nolyric']:
                lrc = conf['noneLyric']
        except KeyError:
            try:
                tlrc = data['tlyric']['lyric']
                rlrc = data['lrc']['lyric']
                if self.lrcType[0]:
                    lrc = rlrc
                elif self.lrcType[1]:
                    lrc = rlrc if tlrc == None else tlrc
                elif self.lrcType[2]:
                    lrc = lrcMerge(rlrc, tlrc)
            except KeyError:
                pass
        finally:
            if self.lrcformat:
                lrc = lrcReg.sub(r'\1\3', lrc)
            with open(f"{conf['path']}/{filename}", 'w', encoding='utf-8') as file:
                file.write(lrc)
        self.always.emit(f'{filename}写入完成。')


# get请求线程类
class RequestThread(QThread):  # 线程1
    success = pyqtSignal(object)
    fail = pyqtSignal()
    always = pyqtSignal()

    def __init__(self, url, params=None, retry=3, timeout=5, is_json=True, data=None, NoCache=False):
        super().__init__()
        self.url = url
        self.params = params
        if (NoCache):
            self.params.update({'timestamp': int(time.time())})
        self.retry = retry
        self.timeout = timeout
        self.is_json = is_json
        self.data = data

    def run(self):
        i = 0
        while i < self.retry:
            try:
                res = requests.get(self.url, params=self.params, timeout=self.timeout)
                if res.status_code != 200:
                    continue
                ret = res.json() if self.is_json else res
                self.success.emit(ret if self.data == None else {'ret': ret, 'data': self.data})
                self.always.emit()
                return
            except requests.exceptions.RequestException:
                print('error')
                i += 1
        self.always.emit()
        self.fail.emit()


mutex = QMutex()


class Download(QThread):
    always = pyqtSignal()
    updateUI = pyqtSignal(object, object)
    pause = pyqtSignal(object, bool)
    delete = pyqtSignal(object)
    paused = False
    fucked = False
    myItem = None
    filename = ''

    def __init__(self, myItem, url, opt={}):
        super().__init__()
        self.opt = opt
        self.filename = opt['out']
        self.url = url
        self.myItem = myItem[0]
        self.listItem = myItem[1]
        self.myItem.pauseButton.clicked.connect(self.onPause)
        self.myItem.deleteButton.clicked.connect(self.onDelete)
        self.myItem.folderButton.clicked.connect(self.onFolder)

    def onDelete(self):
        self.delete.emit(self.listItem)
        mutex.lock()
        try:
            rpcServer.aria2.remove(self.gid)
        except rpc.Fault:
            pass
        mutex.unlock()

    def onPause(self):
        mutex.lock()
        try:
            if self.paused:
                rpcServer.aria2.unpause(self.gid)
                self.paused = False
            else:
                rpcServer.aria2.pause(self.gid)
                self.paused = True
        except rpc.Fault:
            pass
        mutex.unlock()
        self.pause.emit(self.myItem, self.paused)

    def onFolder(self):
        pt = os.path.abspath(f"{conf['path']}\{self.filename}")
        os.system(f'explorer /e,/select,"{pt}"')
        print(f'explorer /e,/select,"{pt}"')

    def run(self):
        mutex.lock()
        self.gid = rpcServer.aria2.addUri(self.url, self.opt)
        print(rpcServer)
        # time.sleep(0.5)
        mutex.unlock()
        while True:
            time.sleep(1)
            mutex.lock()
            if self.fucked:
                break
            ret = rpcServer.aria2.tellStatus(self.gid, ['status', 'totalLength', 'completedLength', 'downloadSpeed'])
            self.updateUI.emit(self.myItem, ret)
            print(ret['status'])
            mutex.unlock()
            if ret['status'] == 'complete':
                break
        self.always.emit()
        self.delete.emit(self.listItem)


# http://cn.voidcc.com/question/p-vujtksge-wr.html
class CostomTableWidgetItem(QTableWidgetItem):
    def __init__(self, key):
        super().__init__(str(key) if key != None else '(不可用)', QTableWidgetItem.UserType)
        self.key = key

    #Qt uses a simple < check for sorting items, override this to use the sortKey
    #重载小于号
    def __lt__(self, other):
        if self.key == None:
            return True
        if other.key == None:
            return False
        return self.key < other.key


# 多任务get请求
class MultiTask(QObject):
    final = pyqtSignal()

    def __init__(self, max_conn=5):
        super().__init__()
        self.queue = list()
        self.pos = 0
        self.num = max_conn
        self.done_cnt = 0

    def add(self, req: RequestThread):
        req.always.connect(self.next)
        self.queue.append(req)

    def start(self):
        if len(self.queue) == 0:
            self.final.emit()
            return

        self.num = min(self.num, len(self.queue))
        for i in range(self.num):
            self.queue[i].start()
        self.pos = self.num

    def next(self):
        # print('fucker',len(self.queue))
        self.done_cnt = self.done_cnt + 1
        if self.done_cnt == len(self.queue):
            self.final.emit()
            return
        if self.pos < len(self.queue):
            self.queue[self.pos].start()
            self.pos = self.pos + 1


# 主窗口类
class MainWindow(QMainWindow, ui.net.Ui_MainWindow):
    songs = [{}]
    listName = '歌单名称'

    def __init__(self, parent=None):
        # 固定用法
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        # 按钮绑定槽函数
        self.statusBar().showMessage('无动作')
        self.queryBtn.clicked.connect(self.query)
        self.idEdit.returnPressed.connect(self.query)
        # 菜单绑定槽函数
        self.exitBtn.triggered.connect(self.close)
        self.loginAction.triggered.connect(self.login)
        self.fnameAction.triggered.connect(self.setFilename)
        # 用户名标签事件绑定
        self.userLB.enterEvent = self.UserEnter
        self.userLB.leaveEvent = self.UserLeave
        self.userLB.mousePressEvent = self.UserPress

        self.testBtn.clicked.connect(self.test)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 表格初始化
        self.tableWidget.setColumnCount(10)
        self.tableWidget.setHorizontalHeaderLabels(
            ['id', '序号', '标题', '艺术家', '专辑', '时长（s）', '文件名', 'URL', '比特率（bps）', '格式'])
        # 比特率combobox初始化
        self.brBox.addItems(['180 kbps', '320 kbps', '999 kbps'])
        self.brBox.setCurrentIndex(2)
        idChange = lambda: self.queryBtn.setEnabled(self.idEdit.text() != '')
        self.idEdit.textChanged.connect(idChange)
        idChange()

        self.exitBtn.setIcon(qta.icon('mdi.exit-to-app', scale_factor=1.25))
        self.loginAction.setIcon(qta.icon('mdi.login', scale_factor=1.25))
        self.fnameAction.setIcon(qta.icon('mdi.file-edit-outline', scale_factor=1.25))
        self.aboutAction.setIcon(qta.icon('fa.info-circle', scale_factor=1.25))
        self.websiteAction.setIcon(qta.icon('mdi.web', scale_factor=1.25))
        self.updateAction.setIcon(qta.icon('mdi.update', scale_factor=1.25))
        self.cacheAction.setIcon(qta.icon('fa.database', scale_factor=1))
        self.userListAction.setIcon(qta.icon('mdi.playlist-music', scale_factor=1.25))
        self.METAAction.setIcon(qta.icon('mdi.file-music-outline', scale_factor=1.25))
        self.aria2Action.setIcon(qta.icon('ei.refresh', scale_factor=1))
        # 检查配置
        '''
        global confName
        if not os.path.exists(confName):
            print('配置文件不存在，自动下载默认配置...')
            QMessageBox.warning(self, '提示', '配置文件缺失，\n点击‘Yes’下载配置', QMessageBox.Yes, QMessageBox.Yes)
            self.get = Get(
                'https://raw.githubusercontent.com/pluto0x0/NeteaseMusicDownload/master/NeteaseMusic.default.conf',
                retry=5,
                timeout=15,
                is_json=False)
            self.get.success.connect(self.writeConf)
            self.get.fail.connect(lambda: self.close())
            self.get.start()
        '''
        self.groupBox.setVisible(False)
        self.proBtn.clicked.connect(self.displayPro)
        self.proBtn.setIcon(qta.icon('fa.chevron-down'))
        self.testBtn.setIcon(qta.icon('fa.download'))

        self.m3u8Btn.clicked.connect(self.genM3u8)

        self.pathLB.setText(conf['path'])
        self.pathBtn.clicked.connect(self.changePath)

        self.aria2Action.triggered.connect(self.RestartAria2)
        startAria2()

        for check in CHECKS:
            eval(f"self.{check}.setChecked({str(conf['widget']['checks'][check])})")

        if conf['cookie'] != '':
            self.loginDone()

    def showStatus(self, *args, sp=' '):
        self.statusBar().showMessage(sp.join(map(lambda x: str(x), args)))
        log(args)

    def RestartAria2(self):
        aria2.kill()
        startAria2()

    def UpdateFileName(self):
        for i in range(len(self.songs)):
            self.songs[i]['filename'] = fileStr(conf['patternStr'].format(**self.songs[i]))
            self.tableWidget.setItem(i, 6, CostomTableWidgetItem(self.songs[i]['filename']))

    # 写入配置方法
    def WriteConf(self, res):
        with open(confName, 'wb') as conffile:
            conffile.write(res.content)
        print('下载cussed')

    # 用户名鼠标进入事件
    def UserEnter(self, e):
        font = self.userLB.font()
        font.setUnderline(True)
        # 粗体
        # font.setBold(True)
        self.userLB.setFont(font)
        return super().enterEvent(e)

    # 用户名鼠标离开事件
    def UserLeave(self, e):
        font = self.userLB.font()
        font.setUnderline(False)
        # 粗体
        # font.setBold(False)
        self.userLB.setFont(font)
        return super().leaveEvent(e)

    # 用户名鼠标点击事件
    def UserPress(self, e):
        self.lists = ListChildWindow()
        self.lists.show()
        return super().mousePressEvent(e)
    

    def login(self):
        '''用户登录'''
        self.showStatus('用户登录')

        login = LoginChildWindow()
        if login.exec_() == login.Accepted:
            self.loginDone()

        login.destroy()

    def loginDone(self):
        '''登录成功'''
        self.userLB.setText(conf['nickname'])
        # 显示id

        def displayImg(data):
            '''显示用户头像'''
            img = QPixmap()
            img.loadFromData(data)
            img = img.scaled(50, 50, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.canvas = QPixmap(50, 50)
            self.canvas.fill(Qt.transparent)
            painter = QPainter(self.canvas)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            path = QPainterPath()
            path.addEllipse(0, 0, 50, 50)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, img)
            self.AvatarLB.setPixmap(self.canvas)

        async def getAvatar(url):
            async with session.get(url) as respones:
                res = await respones.read()
                if not res:
                    # 头像获取失败
                    log('get avatar failed:', url)
                else:
                    displayImg(res)

        asyncio.ensure_future(getAvatar(conf['avatarURL']),loop=loop)

    # 生成m3u8歌单
    def genM3u8(self):
        # https://www.cnblogs.com/xiyuan2016/p/7218203.html
        # https://cloud.tencent.com/developer/article/1487084
        filename = fileStr(self.listName)
        file_path, file_type = QFileDialog.getSaveFileName(self, '保存m3u8歌单',
                                                           f"{os.path.abspath(conf['path'])}\\{filename}.m3u8",
                                                           '播放多媒体列表 (*.m3u8);;所有文件(*.*)')
        with open(file_path, 'w', encoding='utf8') as f:
            f.write('#EXTM3U\n')
            for i in self.songs:
                if i['url'] != None:
                    f.write('#EXTINF:{0:.2f},{3}\n{1}.{2}\n'.format(i['len'], i['filename'], i['type'], i['name']))
        self.statusBar().showMessage('已生成{0}.m3u8'.format(filename))

    def delete(self, listitem):
        # self.taskList.removeItemWidget(listitem)
        # https://stackoverflow.com/a/23836142
        self.taskList.takeItem(self.taskList.row(listitem))

    def pause(self, myitem, paused):
        myitem.pauseButton.setIcon(qta.icon('fa.play' if paused else 'fa.pause', scale_factor=1))

    def setupItem(self, title):
        listitem = QListWidgetItem(self.taskList)
        listitem.setSizeHint(QSize(200, 50))
        myitem = ListItem(title)
        # myitem.deleteButton.clicked.connect(self.delete)
        # myitem.folderButton.clicked.connect(lambda : os.system(f'explorer {path}'))
        self.taskList.setItemWidget(listitem, myitem)
        return (myitem, listitem)

    lrcTask = MultiTask()

    def _getLrc(self, res):
        lrcWriter = WriteLrcThread(
            res, (self.radioButton.isChecked(), self.radioButton_2.isChecked(), self.radioButton_3.isChecked()),
            self.lrcFormatCheck.isChecked())
        lrcWriter.always.connect(self.statusBar().showMessage)
        self.lrcTask.add(lrcWriter)

    def closeEvent(self, event):
        LogFile.close()
        aria2.kill()
        for check in CHECKS:
            conf['widget']['checks'][check] = eval(f"self.{check}.isChecked()")
        with open(confName, 'w', encoding='utf-8') as confFile:
            confFile.write(json.dumps(conf, sort_keys=False, indent=4))
        event.accept()

    def changePath(self):
        conf['path'] = QFileDialog.getExistingDirectory(self, '选择下载目录', conf['path'])
        self.pathLB.setText(conf['path'])

    def test(self):
        # self.genM3u8()
        # return

        self.mutidown = MultiTask(max_conn=conf['maxDownload'])
        fileList = os.listdir(conf['path'])

        def addTask(ext, url):
            # 'i' in self.songs
            filename = f"{i['filename']}.{ext}"
            # print(url)
            if self.skipCheck.isChecked() and filename in fileList:
                self.statusBar().showMessage(f'跳过{filename}，已存在。')
                return
            task = Download(self.setupItem(filename), [url], {
                'dir': os.path.abspath(conf['path']),
                'out': f"{i['filename']}.{ext}"
            })
            task.updateUI.connect(self.updateList)
            task.pause.connect(self.pause)
            task.delete.connect(self.delete)
            self.mutidown.add(task)

        if self.songCheck.isChecked():
            for i in self.songs:
                if i['url'] != None:
                    addTask(i['type'], i['url'])

        if self.picCheck.isChecked():
            for i in self.songs:
                addTask('jpg', i['pic'])

        if self.lrcCheck.isChecked():
            self.lrcGet = MultiTask(max_conn=5)
            for i in self.songs:
                filename = i['filename'] + '.lrc'
                if self.skipCheck.isChecked() and filename in fileList:
                    self.statusBar().showMessage(f'跳过{filename}，已存在。')
                    continue
                task = RequestThread(f"{conf['baseURL']}/lyric", params={'id': i['id']}, data=filename)
                task.success.connect(self._getLrc)
                self.lrcGet.add(task)
            self.lrcTask.final.connect(lambda: self.statusBar().showMessage('所有歌词完成。'))
            self.lrcGet.final.connect(self.lrcTask.start)
            self.lrcGet.start()

        self.mutidown.final.connect(self.writeTag)
        self.mutidown.start()
        # self.writeTag()

    def writeTag(self):
        fileList = os.listdir(conf['path'])
        if self.tagCheck.isChecked():
            self.tagwriter = WriteTagThread(
                filter(lambda song: f'{song["filename"]}.{song["type"]}' in fileList, self.songs))
            self.tagwriter.always.connect(lambda ret: self.statusBar().showMessage(ret))
            self.tagwriter.final.connect(lambda: self.statusBar().showMessage('所有标签写入完成。'))
            self.tagwriter.start()
        self.statusBar().showMessage('所有任务完成。')

    def displayPro(self):
        if self.groupBox.isVisible():
            self.groupBox.setVisible(False)
            self.resize(self.width(), self.height() - self.groupBox.height() + 2)
            self.proBtn.setIcon(qta.icon('fa.chevron-down'))
        else:
            self.resize(self.width(), self.height() + self.groupBox.height() - 2)
            self.groupBox.setVisible(True)
            self.proBtn.setIcon(qta.icon('fa.chevron-up'))

    def updateList(self, myitem, ret):
        myitem.progressBar.setRange(1, int(ret['totalLength']))
        myitem.progressBar.setValue(int(ret['completedLength']))
        myitem.speedLabel.setText(f'{int(ret["downloadSpeed"])/1024:.2f}KiB/s')

    # 请求歌单方法
    def query(self):
        self.tableWidget.clearContents()
        '''
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.setSortingEnabled(True)

        self.tableWidget.setColumnCount(0)
        self.tableWidget.setColumnCount(10)
        '''
        self.tableWidget.setSortingEnabled(False)
        '''
        self.tableWidget.setHorizontalHeaderLabels(
        ['id', '序号', '标题', '艺术家', '专辑', '时长（s）', '文件名', 'URL', '比特率（bps）', '格式'])
        '''
        id = self.idEdit.text()
        if re.search(r'album', id) != None:
            id = re.search(r'album\?id=([0-9]+)', id).group(1)
            # self.idEdit.setText(id)
            self.getLists = RequestThread(conf['baseURL'] + '/album', params={'id': id}, data='album')
        else:
            if re.search(r'id', id) != None:
                id = re.search(r'id=([0-9]+)', id).group(1)
                self.idEdit.setText(id)
            self.getLists = RequestThread(conf['baseURL'] + '/playlist/detail', params={'id': id}, data='playlist')
        self.getLists.start()
        self.getLists.success.connect(self._query)

    # 请求歌单回调函数
    def _query(self, retu):
        data = retu['ret']
        songids = []
        self.id2no = {}

        if retu['data'] == 'playlist':
            songids = [str(song['id']) for song in data['playlist']['trackIds']]
            self.listName = data['playlist']['name']
        elif retu['data'] == 'album':
            songids = [str(song['id']) for song in data['songs']]
            self.listName = data['album']['name'] + ' - ' + data['album']['artist']['name']

        self.len = len(songids)

        # https://blog.csdn.net/xingce_cs/article/details/79178077
        self.songs = [{} for i in range(self.len)]
        # 初始化
        self.progressBar.setRange(1, self.len * 2)
        self.done = 0
        self.progressBar.setValue(0)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setRowCount(self.len)

        for i in range(self.len):
            self.tableWidget.setItem(i, 0, CostomTableWidgetItem(songids[i]))
            self.id2no[songids[i]] = i
        # print(repr(songids))
        cur_br = [180000, 320000, 999000][self.brBox.currentIndex()]
        self.brBox.setEnabled(False)
        self.mget = MultiTask()
        self.songs_d = []

        for i in range(0, len(self.songs), conf['maxLen']):
            ids = ','.join(songids[i:i + conf['maxLen']])
            # 获取音乐信息
            # TODO!!!!!!!!!!!!!!!!!
            get = RequestThread(conf['baseURL'] + '/song/detail', params={'ids': ids}, data={'no': i},
                                NoCache=True)  # no：序号
            get.success.connect(self._each)
            self.mget.add(get)
            # 获取音乐URL
            get = RequestThread(conf['baseURL'] + '/song/url',
                                params={
                                    'id': ids,
                                    'cookie': conf['cookie'],
                                    'br': cur_br
                                },
                                data={'no': i},
                                NoCache=True)
            get.success.connect(self._each_url)
            self.mget.add(get)
        self.mget.final.connect(self.qDone)
        self.mget.start()
        '''
        for i in range(self.len):
            song = {'id': songids[i]}
            # 获取音乐信息
            get = Get(conf['baseURL'] + '/song/detail', params={'ids': song['id']}, data={'id': i})
            get.success.connect(self._each)
            self.mget.add(get)
            # 获取音乐URL
            get = Get(conf['baseURL'] + '/song/url', params={'id': song['id'], 'cookie': conf['cookie'], 'br': cur_br})
            get.success.connect(self._each_url)
            self.mget.add(get)
        '''

    # 单个歌曲信息回调函数
    def _each(self, res):
        for data in res['ret']['songs']:
            no = self.id2no[str(data['id'])]
            song = {
                'id': data['id'],
                'no': no + 1,
                'name': data['name'],
                'len': data['dt'] / 1000,
                'year': str(time.localtime(data['publishTime'] // 1000).tm_year),
                'album': data['al']['name'],
                'pic': data['al']['picUrl'],
                'filename': 'file',
                'artists': [ar['name'] for ar in data['ar']],
                'artist': '',
            }
            '''
            for ar in data['ar']:
                song['artists'].append(ar['name'])
            '''

            song['artist'] = ','.join(song['artists'])
            song['filename'] = fileStr(conf['patternStr'].format(**song))

            self.songs[no].update(song)

            mapping = ['no', 'name', 'artist', 'album', 'len', 'filename']
            for j in range(len(mapping)):
                self.tableWidget.setItem(no, j + 1, CostomTableWidgetItem(song[mapping[j]]))

        le = len(res['ret']['songs'])
        self.done = self.done + le
        self.progressBar.setValue(self.done)
        self.statusBar().showMessage('完成 音乐信息： {0}-{1}'.format(res['data']['no'], res['data']['no'] + le))

    # 单个歌曲url回调函数
    def _each_url(self, res):
        for data in res['ret']['data']:
            no = self.id2no[str(data['id'])]
            # print(no,'!')
            self.songs[no].update({'url': data['url'], 'br': data['br'], 'type': data['type']})

            self.tableWidget.setItem(no, 7, CostomTableWidgetItem(data['url']))
            self.tableWidget.setItem(no, 8, CostomTableWidgetItem(data['br']))
            if self.songs[no]['type'] != None:
                self.songs[no]['type'] = self.songs[no]['type'].lower()
            self.tableWidget.setItem(no, 9, CostomTableWidgetItem(self.songs[no]['type']))

        le = len(res['ret']['data'])
        self.done = self.done + le
        self.progressBar.setValue(self.done)
        self.statusBar().showMessage('完成 URL： {0}-{1}'.format(res['data']['no'] + 1, res['data']['no'] + le))

    # 所有请求完成事件
    def qDone(self):
        self.statusBar().showMessage('所有信息获取完成。')
        self.brBox.setEnabled(True)
        self.tableWidget.setSortingEnabled(True)
        del self.mget

    # 设置文件名格式方法
    def setFilename(self):
        self.fnameWindow = PatternWindow()
        if self.fnameWindow.exec_() == self.fnameWindow.Accepted:
            self.statusBar().showMessage('文件名模式串已更新。')
            self.UpdateFileName()

        # TODO:
        # update


# 文件名格式窗口类
class PatternWindow(QDialog, ui.pattern.Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        global patternStr
        self.patternEdit.setText(conf['patternStr'])
        self.patternCombo.addItems(['标题', '艺术家', '专辑', '年份', '序号'])
        self.insertBtn.clicked.connect(self.insert)
        self.exitBtn.clicked.connect(lambda: self.reject())
        self.okBtn.clicked.connect(self.ok)

    # 插入模式串方法
    def insert(self):
        pstr = [r'{titile}', r'{artist}', r'{album}', r'{year}', r'{index}']
        self.patternEdit.insert(pstr[self.patternCombo.currentIndex()])

    # 确认保存并退出方法
    def ok(self):
        global patternStr
        conf['patternStr'] = self.patternEdit.text()
        self.accept()


# 主函数
if __name__ == '__main__':
    ncmd = QApplication(sys.argv)
    loop = quamash.QEventLoop(ncmd)
    asyncio.set_event_loop(loop)

    async def initSession():
        global session
        session = aiohttp.ClientSession(loop=loop)
    asyncio.ensure_future(initSession(), loop=loop)
    
    mainwin = MainWindow()
    mainwin.show()
    with loop:
        loop.run_forever()
