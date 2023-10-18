#!/usr/bin/env python3

import pathlib
import datetime
from . import kmall


class Datagram:
  def __init__(self, kmall_file):
    self.kmall = kmall_file
    self.file_position = kmall_file.tell()
    self.header = None
    self.readHeader()

  def fileSize(self):
    self.kmall.seek(0, 2)
    file_size = self.kmall.tell()
    self.kmall.seek(self.file_position, 0)
    return file_size

  def readHeader(self):
    if self.fileSize() > self.file_position + 20:
      data = self.kmall.read(20)
      self.header, count = kmall.read_EMdgmHeader(data)
      self.kmall.seek(self.file_position, 0)

  def next(self):
    if self.header is None:
      self.readHeader()
      if self.header is None:
        return None
    self.kmall.seek(self.file_position+self.header['numBytesDgm'])
    if self.kmall.tell() == self.file_position+self.header['numBytesDgm']:
      return Datagram(self.kmall)
    return None

  def data(self):
    if self.header is None:
      self.readHeader()
    if self.header is not None:
      if self.fileSize() >= self.header['numBytesDgm'] + self.file_position:
        return self.kmall.read(self.header['numBytesDgm'])
    return None



class FilesystemWatcher:
  def __init__(self, path, extension='kmwcd_frag'):
    self.path = pathlib.Path(path)
    self.current_file = None
    self.file_extension = extension
    self.current_datagram = None
    self.previous_datagram = None

  def lookForLatestFile(self):
    latest_file = None
    latest_file_mtime = None
    for k in self.path.glob('*.'+self.file_extension):
      mtime_ns = k.stat().st_mtime_ns
      mtime = datetime.datetime.fromtimestamp(mtime_ns/1000000000.0)
      if latest_file_mtime is None or mtime > latest_file_mtime:
        latest_file = k
        latest_file_mtime = mtime

    return latest_file, latest_file_mtime


  def getNewPings(self):
    datagrams = []

    latest_file,latest_file_mtime = self.lookForLatestFile()
    if latest_file != self.current_file:
      # make sure to finish reading from the previous file
      datagrams += self.getAllDatagrams()
      self.previous_datagram = None
      kmall_file = open(latest_file, 'rb')
      self.current_datagram = Datagram(kmall_file)
      self.current_file = latest_file
    datagrams += self.getAllDatagrams()
    return datagrams


        
  def getAllDatagrams(self):
    datagrams = []

    if self.current_datagram is None:
      if self.previous_datagram is not None:
        self.current_datagram = self.previous_datagram.next()
    while self.current_datagram is not None:
      data = self.current_datagram.data()
      if data is not None:
        if self.current_datagram.header['dgmType'] == b'#MWC':
          wc = kmall.read_EMdgmMWC(data)
          if wc['partition']['numOfDgms'] > 1:
            if wc['partition']['dgmNum'] == 1:
              self.fragments = []
            self.fragments.append(wc)
            if wc['partition']['dgmNum'] == wc['partition']['numOfDgms']:
              if len(self.fragments) == wc['partition']['numOfDgms']:
                all_the_data = self.fragments[0]['multibeam_payload']
                for f in self.fragments[1:]:
                  all_the_data += f['multibeam_payload']
                full_wc = kmall.read_EMdgmMWC(all_the_data, True)
                datagrams.append(full_wc)
              self.fragments = []
          else:
            datagrams.append(wc)

        self.previous_datagram = self.current_datagram
        self.current_datagram = self.previous_datagram.next()
      else:
        break
    return datagrams

