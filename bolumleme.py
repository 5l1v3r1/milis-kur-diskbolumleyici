import sys, parted
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

#################################################################### 
def main(): 
	app = QApplication(sys.argv)
	app.setApplicationName('Bölümleme Demosu') 
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
				if parted.Disk(disk).type == "msdos":
					self.disklerAcilirKutu.addItem("{} {} GB ({})".format(disk.model, format(disk.getSize(unit="GB"),'.2f'), disk.path), userData=disk.path)
			except parted.DiskLabelException:
				disk = parted.freshDisk(disk, 'msdos')
			# CDROM Aygıtları için
				try:
					disk.commit()
				except parted.IOException:
					pass
				else:
					disk = disk.device
					self.disklerAcilirKutu.addItem("{} {} GB ({})".format(disk.model, format(disk.getSize(unit="GB"),'.2f'), disk.path), userData=disk.path)

		self.disklerAcilirKutu.currentIndexChanged.connect(self.diskDegisti)
		
		if self.disklerAcilirKutu.currentData():
			self.aygit = parted.getDevice(self.disklerAcilirKutu.currentData())

			self.disk = parted.Disk(self.aygit)

			self.bolumListeKutu = QListWidget()
			
			for bolum in self.disk.partitions:

				_bolum = self.bolumBilgi(bolum, "GB")

				item = QListWidgetItem("{}\t\t{} GB\t{}\t{}".format(_bolum["yol"],_bolum["boyut"],_bolum["dosyaSis"],_bolum["bayraklar"]))
				item.setData(Qt.UserRole, _bolum["no"])
				if _bolum["tur"] == parted.PARTITION_NORMAL:
					item.setIcon(QIcon("gorseller/primary.xpm"))
				elif _bolum["tur"] == parted.PARTITION_EXTENDED:				
					item.setIcon(QIcon("gorseller/extended.xpm"))	
				elif _bolum["tur"] == parted.PARTITION_LOGICAL:
					item.setIcon(QIcon("gorseller/logical.xpm"))					
				self.bolumListeKutu.addItem(item)

			for bosBolum in self.disk.getFreeSpacePartitions():
				_toplam = 0
				_bolum = self.bolumBilgi(bosBolum, "GB")
				if float(_bolum["boyut"]) > 0:
					if _bolum["tur"] == 5:
						uzatilmisKalan = QListWidgetItem("{}\t{} GB".format("Uzatılmış Bölüm Kalan",_bolum["boyut"]))
						uzatilmisKalan.setIcon(QIcon("gorseller/blank.xpm"))
						uzatilmisKalan.setData(Qt.UserRole, "ayrilmamis")
						self.bolumListeKutu.addItem(uzatilmisKalan)
					if _bolum["tur"] == parted.PARTITION_FREESPACE:
						_toplam = _toplam + float(_bolum["boyut"])
					ayrilmamis = QListWidgetItem("{}\t{} GB".format("Ayrılmamış Bölüm",_toplam))
					ayrilmamis.setIcon(QIcon("gorseller/blank.xpm"))
					ayrilmamis.setData(Qt.UserRole, "ayrilmamis")
					self.bolumListeKutu.addItem(ayrilmamis)		
		
		disklerLayout.addWidget(self.disklerAcilirKutu)
		disklerLayout.addWidget(self.yenileButon)
		disklerWidget.setLayout(disklerLayout)
		layout = QVBoxLayout()
		layout.addWidget(disklerWidget)
		layout.addWidget(self.bolumListeKutu)
		lejant = QLabel()
		lejant.setPixmap(QPixmap("gorseller/lejant.png"))
		lejant.setAlignment(Qt.AlignCenter)
		layout.addWidget(lejant)
		self.bolumListeKutu.itemClicked.connect(self.bolumSecildiFonk)
		self.bolumListeKutu.itemDoubleClicked.connect(self.bolumFormatSecFonk)
		
		opWidget=QWidget()
		opButonlar = QHBoxLayout()
		self.yeniBolumBtn = QPushButton("Yeni Bölüm Ekle")
		self.yeniBolumBtn.pressed.connect(self.bolumEkleFonk)
		self.bolumSilBtn = QPushButton("Bölümü Sil")
		self.bolumSilBtn.pressed.connect(self.bolumSilFonk)
		self.kaydetBtn = QPushButton("Kaydet")
		self.kaydetBtn.pressed.connect(self.kaydet)
		opButonlar.addWidget(self.yeniBolumBtn)
		opButonlar.addWidget(self.bolumSilBtn)
		opButonlar.addWidget(self.kaydetBtn)
		opWidget.setLayout(opButonlar) 
		layout.addWidget(opWidget)
		
		self.bolumSilBtn.setEnabled(False)
		self.setLayout(layout)

	def kaydet(self):
		self.disk.commit()

	def bolumFormatSecFonk(self, tiklanan):
		if tiklanan.data(Qt.UserRole) != "ayrilmamis":
			for bolum in self.disk.partitions:
				if bolum.number == tiklanan.data(Qt.UserRole):
					print(bolum.path)
	def bolumBilgi(self, bolum, birim):
		_bolum = {}
		_bolum["yol"] = bolum.path
		if birim == "GB":
			_bolum["boyut"] = format(bolum.getSize(unit=birim),'.2f')
		else:
			_bolum["boyut"] = bolum.getSize(unit=birim)

		_bolum["dosyaSis"] = "Bilinmeyen"
		
		if bolum.fileSystem:
			if bolum.fileSystem.type.startswith('linux-swap'): 
				_bolum["dosyaSis"] = "takas"
			else:
				_bolum["dosyaSis"] = bolum.fileSystem.type

		try:
			_bolum["bayraklar"] = bolum.getFlagsAsString()
		except:
			pass
		_bolum["no"] = bolum.number
		_bolum["tur"] = bolum.type
		
		return _bolum

	def diskYenile(self):
		self.disklerAcilirKutu.clear()
		self.diskler = parted.getAllDevices()
		for disk in self.diskler:
			try:
				if parted.Disk(disk).type == "msdos":
					self.disklerAcilirKutu.addItem("{} {} GB ({})".format(disk.model, format(disk.getSize(unit="GB"),'.2f'), disk.path), userData=disk.path)
			except parted.DiskLabelException:
				disk = parted.freshDisk(disk, 'msdos')
			# CDROM Aygıtları için
				try:
					disk.commit()
				except parted.IOException:
					pass
				else:
					disk = disk.device
					self.disklerAcilirKutu.addItem("{} {} GB ({})".format(disk.model, format(disk.getSize(unit="GB"),'.2f'), disk.path), userData=disk.path)

	def diskDegisti(self):
		if self.disklerAcilirKutu.currentData():
			self.aygit = parted.getDevice(self.disklerAcilirKutu.currentData())
			self.disk = parted.Disk(self.aygit)
			self.bolumListeYenile()


	def bolumListeYenile(self):
		self.bolumListeKutu.clear()
		for bolum in self.disk.partitions:

			_bolum = self.bolumBilgi(bolum, "GB")

			item = QListWidgetItem("{}\t\t{} GB\t{}\t{}".format(_bolum["yol"],_bolum["boyut"],_bolum["dosyaSis"],_bolum["bayraklar"]))
			item.setData(Qt.UserRole, _bolum["no"])
			if _bolum["tur"] == parted.PARTITION_NORMAL:
				item.setIcon(QIcon("gorseller/primary.xpm"))
			elif _bolum["tur"] == parted.PARTITION_EXTENDED:				
				item.setIcon(QIcon("gorseller/extended.xpm"))	
			elif _bolum["tur"] == parted.PARTITION_LOGICAL:
				item.setIcon(QIcon("gorseller/logical.xpm"))	
			self.bolumListeKutu.addItem(item)	

		for bosBolum in self.disk.getFreeSpacePartitions():
			_toplam = 0
			_bolum = self.bolumBilgi(bosBolum, "GB")
			if float(_bolum["boyut"]) > 0:
				if _bolum["tur"] == 5:
					uzatilmisKalan = QListWidgetItem("{}\t{} GB".format("Uzatılmış Bölüm Kalan",_bolum["boyut"]))
					uzatilmisKalan.setIcon(QIcon("gorseller/blank.xpm"))
					uzatilmisKalan.setData(Qt.UserRole, "ayrilmamis")
					self.bolumListeKutu.addItem(uzatilmisKalan)
				if _bolum["tur"] == parted.PARTITION_FREESPACE:
					_toplam = _toplam + float(_bolum["boyut"])
				ayrilmamis = QListWidgetItem("{}\t{} GB".format("Ayrılmamış Bölüm",_toplam))
				ayrilmamis.setIcon(QIcon("gorseller/blank.xpm"))
				ayrilmamis.setData(Qt.UserRole, "ayrilmamis")
				self.bolumListeKutu.addItem(ayrilmamis)			

	def bolumSecildiFonk(self,tiklanan):
		
		if tiklanan.data(Qt.UserRole) != "ayrilmamis":
			self.bolumSilBtn.setEnabled(True)
		else:
			self.bolumSilBtn.setEnabled(False)


	def bolumSilFonk(self):
		bolumNo = self.bolumListeKutu.currentItem().data(Qt.UserRole)
		for bolum in self.disk.partitions:
			if bolum.number == bolumNo:
				try:
					self.disk.deletePartition(bolum)
					self.bolumListeYenile()
				except parted.PartitionException:
					QMessageBox.warning(self,"Uyarı", 
"Lütfen uzatılmış bölümleri silmeden önce mantıksal bölümleri siliniz.")
		self.bolumListeKutu.setCurrentRow(self.bolumListeKutu.count() - 2)

	def bolumEkleFonk(self):
		if self._en_buyuk_bos_alan():
			alan = self._en_buyuk_bos_alan()
			birincilSayi = len(self.disk.getPrimaryPartitions())
			uzatilmisSayi = ext_count = 1 if self.disk.getExtendedPartition() else 0
			parts_avail = self.disk.maxPrimaryPartitionCount - (birincilSayi + uzatilmisSayi)
			if not parts_avail and not ext_count:
				QMessageBox.warning(self,
				"Uyarı",
"""Eğer dörtten fazla disk bölümü oluşturmak istiyorsanız birincil bölümlerden birini silip uzatılmış bölüm oluşturun. 
Bu durumda oluşturduğunuz uzatılmış bölümleri işletim sistemi kurmak için kullanamayacağınızı aklınızda bulundurun."""
				)
			else:
				if parts_avail:
					if not uzatilmisSayi and parts_avail > 1:
						self.bolumOlustur(alan, parted.PARTITION_NORMAL)
						self.bolumListeYenile()
					elif parts_avail == 1:
						self.bolumOlustur(alan, parted.PARTITION_EXTENDED)
						self.bolumListeYenile()
				 
				if uzatilmisSayi:
						ext_part = self.disk.getExtendedPartition()
						try:
							alan = ext_part.geometry.intersect(alan)
						except ArithmeticError:
							QMessageBox.critical(self,"Hata","Yeni disk bölümü oluşturmak için yeterli alan yok ! Uzatılmış bölümün boyutunu arttırmayı deneyiniz.")
						else:	
							self.bolumOlustur(alan, parted.PARTITION_LOGICAL)
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

	def bolumOlustur(self, alan, bolumTur):
		
		if bolumTur == parted.PARTITION_NORMAL or bolumTur == parted.PARTITION_EXTENDED:
			for bosBolum in self.disk.getFreeSpacePartitions():
				_bolum = self.bolumBilgi(bosBolum, "GB")
				if _bolum["tur"] == parted.PARTITION_FREESPACE:
					maksBoyut = float(_bolum["boyut"])
		elif bolumTur == bolumTur == parted.PARTITION_LOGICAL:
			for bosBolum in self.disk.getFreeSpacePartitions():
				_bolum = self.bolumBilgi(bosBolum, "GB")
				if _bolum["tur"] == 5:
					maksBoyut = float(_bolum["boyut"])						
						
		alignment = self.aygit.optimalAlignedConstraint
		constraint = self.aygit.getConstraint()
		data = {
		    'start': constraint.startAlign.alignUp(alan, alan.start),
		    'end': constraint.endAlign.alignDown(alan, alan.end),
		}
		
		boyut, ok = QInputDialog().getDouble(self, 'Bölüm oluştur', 'GB cinsinden boyut:',min=0.001,value=1, max=maksBoyut,decimals=3)

		if ok:
			data["end"] = int(data["start"]) + int(parted.sizeToSectors(float(boyut),"GiB", self.aygit.sectorSize))
			try:
				geometry = parted.Geometry(device=self.aygit, start=int(data["start"]), end=int(data["end"]))
				partition = parted.Partition(
			        disk=self.disk,
			        type=bolumTur,
			        geometry = geometry,
			    )

				self.disk.addPartition(partition=partition, constraint=constraint)
			except (parted.PartitionException, parted.GeometryException, parted.CreateException) as e:
			    # GeometryException accounts for incorrect start/end values (e.g. start < end),
			    # CreateException is raised e.g. when the partition doesn't fit on the disk.
			    # PartedException is a generic error (e.g. start/end values out of range)
			    raise RuntimeError(e.message)

if __name__ == "__main__": 
	main()
