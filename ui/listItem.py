# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/listItem.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(632, 132)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.titleLabel = QtWidgets.QLabel(Form)
        self.titleLabel.setMinimumSize(QtCore.QSize(140, 0))
        self.titleLabel.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.titleLabel.setWordWrap(True)
        self.titleLabel.setObjectName("titleLabel")
        self.horizontalLayout.addWidget(self.titleLabel)
        self.progressBar = QtWidgets.QProgressBar(Form)
        self.progressBar.setMinimumSize(QtCore.QSize(140, 0))
        self.progressBar.setMaximumSize(QtCore.QSize(400, 16777215))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout.addWidget(self.progressBar)
        self.speedLabel = QtWidgets.QLabel(Form)
        self.speedLabel.setObjectName("speedLabel")
        self.horizontalLayout.addWidget(self.speedLabel)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pauseButton = QtWidgets.QPushButton(Form)
        self.pauseButton.setEnabled(True)
        self.pauseButton.setText("")
        self.pauseButton.setObjectName("pauseButton")
        self.horizontalLayout.addWidget(self.pauseButton)
        self.folderButton = QtWidgets.QPushButton(Form)
        self.folderButton.setText("")
        self.folderButton.setObjectName("folderButton")
        self.horizontalLayout.addWidget(self.folderButton)
        self.deleteButton = QtWidgets.QPushButton(Form)
        self.deleteButton.setText("")
        self.deleteButton.setObjectName("deleteButton")
        self.horizontalLayout.addWidget(self.deleteButton)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.titleLabel.setText(_translate("Form", "Name"))
        self.speedLabel.setText(_translate("Form", "KiBps"))
