import sys, parted
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

#################################################################### 
def main(): 
	app = QApplication(sys.argv) 
	w = MyWindow() 
	w.show() 
	sys.exit(app.exec_()) 

#################################################################### 
class MyWindow(QWidget): 
	def __init__(self, *args): 
		QWidget.__init__(self, *args) 
		
		diskler = parted.getAllDevices()
		self.disklerAcilirKutu = QComboBox()
		for disk in diskler:
			try:
				if parted.Disk(disk).type == "msdos":
					self.disklerAcilirKutu.addItem("{} {} GB ({})".format(disk.model, format(disk.getSize(unit="GB"),'.2f'), disk.path), userData=disk.path)
			except:
				pass
				 
		self.bolumListeKutu = QListWidget()
		for bolum in parted.Disk(parted.getDevice(self.disklerAcilirKutu.currentData())).partitions:
			item = QListWidgetItem("{}\t{} GB\t{}\t\t{}".format(bolum.path, format(bolum.getSize(unit="GB"),'.2f'), bolum.fileSystem.type, bolum.getFlagsAsString()))
			item.setData(Qt.UserRole, bolum.number)
			self.bolumListeKutu.addItem(item)
		layout = QVBoxLayout()
		layout.addWidget(self.disklerAcilirKutu)
		
		layout.addWidget(self.bolumListeKutu)
		self.bolumListeKutu.itemClicked.connect(self.bolumSecildiFonk)
		
		butonWidget=QWidget()
		opButonlar = QHBoxLayout()
		self.yeniBolumBtn = QPushButton("Yeni Bölüm Ekle")
		self.bolumSilBtn = QPushButton("Bölümü Sil")
		self.bolumSilBtn.pressed.connect(self.bolumSilFonk)
		opButonlar.addWidget(self.yeniBolumBtn)
		opButonlar.addWidget(self.bolumSilBtn)
		butonWidget.setLayout(opButonlar) 
		layout.addWidget(butonWidget)
		
		self.bolumSilBtn.setEnabled(False)
		self.setLayout(layout)

	def bolumSecildiFonk(self,tiklanan):
		self.bolumSilBtn.setEnabled(True)

	def bolumSilFonk(self):
		bolumNo = self.bolumListeKutu.currentItem().data(Qt.UserRole)
		disk = parted.Disk(parted.getDevice(self.disklerAcilirKutu.currentData()))
		for bolum in disk.partitions:
			if bolum.number == bolumNo:
				try:
					disk.deletePartition(bolum)
					disk.commit()
				except parted.PartitionException as e:
					print(e.message)
				break

if __name__ == "__main__": 
	main()
