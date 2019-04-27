import re

indenting = False
indentSpaces = '        '

def translateLineComment(CPPstring):
  # whitespace then comment
  global indenting
  commentPattern = re.compile('( *)//(.*)')
  match = commentPattern.match(CPPstring)
  if match:
    if indenting:
      result = indentSpaces+'%s#%s' % (match.group(1), match.group(2))
    else:
      result = '%s#%s' % (match.group(1), match.group(2))
  else:
    result = CPPstring
  return result

def translateComment(CPPstring):
  commentPattern = re.compile('(.*)//(.*)')
  match = commentPattern.match(CPPstring)
  if match:
    result = '%s#%s' % (match.group(1), match.group(2))
  else:
    result = CPPstring
  return result

def translateStruct(CPPstring):
  global indenting
  commentPattern = re.compile('struct *(.*)')
  match = commentPattern.match(CPPstring)
  if match:
    result = 'class %s(ctypes.Structure):\n    _pack_ = 4\n    _fields_ = [' % (match.group(1))
    indenting = True
  else:
    result = CPPstring
  return result

def translateStructItem(CPPstring):
  dict = {
    'long': 'ctypes.c_int',
    'double': 'ctypes.c_double',
    'char': 'ctypes.c_ubyte',
    'short': 'ctypes.c_short',
    'char': 'ctypes.c_ubyte',
    'signed': 'ctypes.c_ubyte',
    'unsigned char': 'ctypes.c_ubyte',
    'signed char': 'ctypes.c_ubyte',
    'const char': 'ctypes.c_ubyte',
    'bool': 'ctypes.c_ubyte',
    'float': 'ctypes.c_float',
    # user-defined structs 
    'TelemVect3': 'TelemVect3',
    'VehicleScoringInfoV01': 'VehicleScoringInfoV01',
    'TelemWheelV01': 'TelemWheelV01',
    'MultiSessionParticipantV01': 'MultiSessionParticipantV01',
    'TrackRulesColumnV01': 'TrackRulesColumnV01',
    'TrackRulesStageV01': 'TrackRulesStageV01',
    'TrackRulesActionV01': 'TrackRulesActionV01',
    'TrackRulesParticipantV01': 'TrackRulesParticipantV01'
  }

  arrayPattern = re.compile(' *(.*) +(.*) *\[ *(.*) *\] *;(.*)')
  match = arrayPattern.match(CPPstring)
  if match:
    try:
      pythonType = dict[match.group(1).strip()]
      result = "        ('%s', %s*%s),%s" % (match.group(2), pythonType, match.group(3),match.group(4))
    except KeyError:
      print('bad C type "%s" in "%s"' % (match.group(1), CPPstring))
      result = CPPstring
  else:
    commentPattern = re.compile(' *(.*) +(.*) *;(.*)')
    match = commentPattern.match(CPPstring)
    if match:
      try:
        pythonType = dict[match.group(1).strip()]
        result = indentSpaces+"('%s', %s),%s" % (match.group(2), pythonType, match.group(3))
      except KeyError:
        print('bad C type "%s" in "%s"' % (match.group(1), CPPstring))
        result = CPPstring
    else:
      result = CPPstring
  return result


def translateStructOpen(CPPstring):
  commentPattern = re.compile('{')
  match = commentPattern.match(CPPstring)
  if match:
    result = None
  else:
    result = CPPstring
  return result

def translateStructClose(CPPstring):
  global indenting
  commentPattern = re.compile(' *};')
  match = commentPattern.match(CPPstring)
  if match:
    result = '    ]'
    indenting = False
  else:
    result = CPPstring
  return result


if __name__ == '__main__':
  python = []
  with open('InternalsPlugin.hpp', "r") as cpp:
    src = cpp.readlines()
    for line in src:
      line = line.strip()
      pythonLine = translateLineComment(line)
      pythonLine = translateStruct(pythonLine)
      pythonLine = translateStructOpen(pythonLine)
      if pythonLine:
        pythonLine = translateStructItem(pythonLine)
        pythonLine = translateStructClose(pythonLine)
        if pythonLine == line:
          pythonLine = '#untranslated ' + pythonLine
        else:
          pythonLine = translateComment(pythonLine)
        python.append(pythonLine + '\n')
  with open('InternalsPlugin.py', "w") as p:
    p.writelines(""" \
# Python mapping of The Iron Wolf's rF2 Shared Memory Tools
# Auto-generated.

import mmap
import ctypes
import time

MAX_MAPPED_VEHICLES = 128
MAX_MAPPED_IDS = 512

class rF2Vec3(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('x', ctypes.c_double),
        ('y', ctypes.c_double),
        ('z', ctypes.c_double),
    ]

"""      )
    p.writelines(python)
    p.writelines("""
class SimInfo:
    def __init__(self):


        self._rf2_tele = mmap.mmap(0, ctypes.sizeof(rF2Telemetry), "$rFactor2SMMP_Telemetry$")
        self.Rf2Tele = rF2Telemetry.from_buffer(self._rf2_tele)
        self._rf2_scor = mmap.mmap(0, ctypes.sizeof(rF2Scoring), "$rFactor2SMMP_Scoring$")
        self.Rf2Scor = rF2Scoring.from_buffer(self._rf2_scor)
        self._rf2_ext = mmap.mmap(0, ctypes.sizeof(rF2Extended), "$rFactor2SMMP_Extended$")
        self.Rf2Ext = rF2Extended.from_buffer(self._rf2_ext)

    def close(self):
        self._rf2_tele.close()
        self._rf2_scor.close()
        self._rf2_ext.close()

    def __del__(self):
        self.close()

if __name__ == '__main__':
    # Example usage
    info = SimInfo()
    version = info.Rf2Ext.mVersion
    v = ''
    for i in range(8):
      v += str(version[i])
    clutch = info.Rf2Tele.mVehicles[0].mUnfilteredClutch # 1.0 clutch down, 0 clutch up
    gear   = info.Rf2Tele.mVehicles[0].mGear  # -1 to 6
    print('Map version: %s\nGear: %d, Clutch position: %d' % (v, gear, clutch))

""")
