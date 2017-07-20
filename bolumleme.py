import sys, parted
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

#################################################################### 
def main(): 
	app = QApplication(sys.argv) 
	w = Bolumleme() 
	w.show() 
	sys.exit(app.exec_()) 

#################################################################### 
class Bolumleme(QWidget): 
	def __init__(self, *args): 
		QWidget.__init__(self, *args) 
		
		self.diskler = parted.getAllDevices()
		disklerWidget = QWidget()
		disklerLayout = QHBoxLayout()
		self.disklerAcilirKutu = QComboBox()
		self.yenileButon = QPushButton("Yenile")
		self.yenileButon.pressed.connect(self.diskYenile)
		for disk in self.diskler:
			try:
				if parted.Disk(disk).type == "msdos" or parted.Disk(disk).type == "gpt":
					pass
					self.disklerAcilirKutu.addItem("{} {} GB ({})".format(disk.model, format(disk.getSize(unit="GB"),'.2f'), disk.path), userData=disk.path)
			except:
				pass
		self.disklerAcilirKutu.currentIndexChanged.connect(self.diskDegisti)
		
		if self.disklerAcilirKutu.currentData():
			self.aygit = parted.getDevice(self.disklerAcilirKutu.currentData())

			self.disk = parted.Disk(self.aygit)

			self.bolumListeKutu = QListWidget()
			
			for bolum in self.disk.partitions:

				_bolum = self.bolumBilgi(bolum, "GB")

				item = QListWidgetItem("{}\t{} GB\t{}\t{}".format(_bolum["yol"],_bolum["boyut"],_bolum["dosyaSis"],_bolum["bayraklar"]))
				item.setData(Qt.UserRole, _bolum["no"])
				self.bolumListeKutu.addItem(item)

		
		disklerLayout.addWidget(self.disklerAcilirKutu)
		disklerLayout.addWidget(self.yenileButon)
		disklerWidget.setLayout(disklerLayout)
		layout = QVBoxLayout()
		layout.addWidget(disklerWidget)
		layout.addWidget(self.bolumListeKutu)
		self.bolumListeKutu.itemClicked.connect(self.bolumSecildiFonk)
		
		opWidget=QWidget()
		opButonlar = QHBoxLayout()
		self.yeniBolumBtn = QPushButton("Yeni Bölüm Ekle")
		self.yeniBolumBtn.pressed.connect(self.bolumEkleFonk)
		self.bolumSilBtn = QPushButton("Bölümü Sil")
		self.bolumSilBtn.pressed.connect(self.bolumSilFonk)
		opButonlar.addWidget(self.yeniBolumBtn)
		opButonlar.addWidget(self.bolumSilBtn)
		opWidget.setLayout(opButonlar) 
		layout.addWidget(opWidget)
		
		self.bolumSilBtn.setEnabled(False)
		self.setLayout(layout)

	def bolumBilgi(self, bolum, birim):
		_bolum = {}
		_bolum["yol"] = bolum.path
		if birim == "GB":
			_bolum["boyut"] = format(bolum.getSize(unit=birim),'.2f')
		else:
			_bolum["boyut"] = bolum.getSize(unit=birim)

		_bolum["dosyaSis"] = None
		
		if bolum.fileSystem:
			if bolum.fileSystem.type.startswith('linux-swap'): 
				_bolum["dosyaSis"] = "takas"
			else:
				_bolum["dosyaSis"] = bolum.fileSystem.type


		_bolum["bayraklar"] = bolum.getFlagsAsString()
		_bolum["no"] = bolum.number
		_bolum["tur"] =  bolum.type
		_bolum["baslangic"] = bolum.geometry.start
		_bolum["bitis"] = bolum.geometry.end

		return _bolum

	def diskYenile(self):
		self.disklerAcilirKutu.clear()
		self.diskler = parted.getAllDevices()
		for disk in self.diskler:
			try:
				if parted.Disk(disk).type == "msdos" or parted.Disk(disk).type == "gpt":
					pass
					self.disklerAcilirKutu.addItem("{} {} GB ({})".format(disk.model, format(disk.getSize(unit="GB"),'.2f'), disk.path), userData=disk.path)
			except:
				pass		

	def diskDegisti(self):
		self.aygit = parted.getDevice(self.disklerAcilirKutu.currentData())
		self.disk = parted.Disk(self.aygit)
		self.bolumListeYenile()


	def bolumListeYenile(self):
		self.bolumListeKutu.clear()
		for bolum in self.disk.partitions:

			_bolum = self.bolumBilgi(bolum, "GB")

			item = QListWidgetItem("{}\t{} GB\t{}\t{}".format(_bolum["yol"],_bolum["boyut"],_bolum["dosyaSis"],_bolum["bayraklar"]))
			item.setData(Qt.UserRole, _bolum["no"])
			self.bolumListeKutu.addItem(item)		

	def bolumSecildiFonk(self,tiklanan):
		self.bolumSilBtn.setEnabled(True)


	def bolumSilFonk(self):
		bolumNo = self.bolumListeKutu.currentItem().data(Qt.UserRole)
		for bolum in self.disk.partitions:
			if bolum.number == bolumNo:
				try:
					self.disk.deletePartition(bolum)
					self.bolumListeYenile()
				except parted.PartitionException as e:
					print(e.message)
				break
	def bolumEkleFonk(self):

		if self._en_buyuk_bos_alan():
			geometri = self._en_buyuk_bos_alan()
			eklenenBolum = self.bolumOlustur(geometri, type=parted.PARTITION_NORMAL)
			self.disk.commit()
			self.bolumListeYenile()

		else:
			 QMessageBox.critical(self,"Hata","Yeni disk bölümü oluşturmak için yeterli alan yok !")
	
	def _en_buyuk_bos_alan(self):
		maks_boyut = -1
		alan = None
		alignment = self.aygit.optimumAlignment
		
		for _alan in self.disk.getFreeSpaceRegions():
			if _alan.length > maks_boyut and _alan.length > alignment.grainSize:
				alan = _alan
				maks_boyut = _alan.length
		
		return alan	

	def bolumOlustur(self, alan, type):
		alignment = self.aygit.optimalAlignedConstraint
		constraint = parted.Constraint(maxGeom=alan).intersect(alignment)
		data = {
		    'start': constraint.startAlign.alignUp(alan, alan.start),
		    'end': constraint.endAlign.alignDown(alan, alan.end),
		}
	
		boyut, ok = QInputDialog.getText(self, 'Bölüm oluştur', 'GB cinsinden boyut:')

		if ok:
			data["length"] = int(parted.sizeToSectors(int(boyut),"GB", self.aygit.sectorSize))
			print(data)
			try:
				geometry = parted.Geometry(device=self.aygit, start=int(data["start"]), length=int(data["length"]))
				partition = parted.Partition(
			        disk=self.disk,
			        type=type,
			        fs = parted.FileSystem("ext4", geometry),
			        geometry = geometry,
			    )

				self.disk.addPartition(partition=partition, constraint=constraint)
			except (parted.PartitionException, parted.GeometryException, parted.CreateException) as e:
			    # GeometryException accounts for incorrect start/end values (e.g. start < end),
			    # CreateException is raised e.g. when the partition doesn't fit on the disk.
			    # PartedException is a generic error (e.g. start/end values out of range)
			    raise RuntimeError(e.message)

			print(partition.number)
			return partition

if __name__ == "__main__": 
	main()
