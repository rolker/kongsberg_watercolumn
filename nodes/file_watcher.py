#!/usr/bin/env python3

import rospy
from marine_acoustic_msgs.msg import RawSonarImage, SonarImageData
import sys
import math
import kongsberg_watercolumn
import time
import struct

rospy.init_node('kongsberg_watercolumn', sys.argv)

publisher = rospy.Publisher('watercolumn', RawSonarImage, queue_size=10)

data_directory = '/home/field/data/mnt/surveypc/sisdata/raw/NA155_DX082303_NautilusTechChallenge/'
data_directory = rospy.get_param('~data_directory', data_directory)

def processWatercolumn(wc):
  print('ping!', wc['header']['dgdatetime'])
  message = RawSonarImage()
  message.header.frame_id = 'project11/drix_8/em712'
  message.header.stamp = rospy.Time.from_seconds(wc['header']['dgdatetime'].timestamp())

  i = 0
  nadir_beam_angle = None
  nadir_beam_index = None
  for beam in wc['beamData']:
    beam_angle = beam['beamPointAngReVertical_deg']
    if nadir_beam_angle is None or abs(beam_angle) < abs(nadir_beam_angle):
      nadir_beam_angle = beam_angle
      nadir_beam_index = i
    i += 1
  print(nadir_beam_index, nadir_beam_angle)
  beam = wc['beamData'][nadir_beam_index]
  sector_number = beam['beamTxSectorNum']
  sector = None
  for sector_data in wc['sectorData']:
    if sector_data['txSectorNum'] == sector_number:
      sector = sector_data
      break
  message.ping_info.frequency = sector['centreFreq_Hz']
  message.ping_info.tx_beamwidths.append(math.radians(sector['txBeamWidthAlong_deg']))
  message.ping_info.sound_speed = wc['rxInfo']['soundVelocity_mPerSec']
  message.sample_rate = wc['rxInfo']['sampleFreq_Hz']
  message.samples_per_beam = beam['numSampleData']
  message.sample0 = beam['startRangeSampleNum']
  message.image.beam_count = 1
  message.image.dtype = SonarImageData.DTYPE_FLOAT32

  samples = []
  for sample in beam['sampleAmplitude05dB_p']:
    samples.append(sample*0.5)

  message.image.data = struct.pack('<'+str(len(samples))+'f', *samples)

  publisher.publish(message)
  time.sleep(0.1)

watcher = kongsberg_watercolumn.kongsberg_watercolumn.FilesystemWatcher(data_directory)


def checkForNewPingsCallback(event):
  pings = watcher.getNewPings()
  for ping in pings:
    processWatercolumn(ping)

rospy.Timer( rospy.Duration(1.0), checkForNewPingsCallback)

rospy.spin()
