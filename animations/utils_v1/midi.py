# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import numpy as np
import sys
from struct import unpack


def read_byte(fobj):
    return unpack('B', fobj.read(1))[0]


def midi_varlen(fobj):
    value = 0
    while True:
        b = read_byte(fobj)
        value = (value << 7) + (b & 0x7f)
        if not (b & 0x80):
            return value


class Midi:
    def __init__(self, fn, fps=25):
        self.load(fn)
        self.fps = fps
        self.normalize()

    def load(self, fn):
        with open(fn, 'rb') as f:
            # Read header
            b = f.read(4)
            if b != b'MThd':
                raise RuntimeError("%s: no midi header" % fn)
            sz, fmt, trk, self.res = unpack(">LHHH", f.read(10))
            # Read padding
            f.read(sz - 10) if sz > 10 else None
#            print("Size: %d\nfmt: %d\ntrk: %d\nres: %d" % (
#                sz, fmt, trk, self.res))
            self.tracks = []
            self.tempo = 500000
            events = []
            track = {}
            track_name = 'NONAME'
            for trknr in range(trk):
                if events:
                    track['name'] = track_name
                    track['events'] = events
                    track['pos'] = 0
                    self.tracks.append(track)
                    events = []
                    track = {}
                if f.read(4) != b'MTrk':
                    raise RuntimeError("%s: invalid structure" % fn)
                sz = unpack(">L", f.read(4))[0]
#                print("New track %d" % sz)
                trk_start = f.tell()
                trk_pos = 0
                while f.tell() - trk_start < sz:
                    tck = midi_varlen(f)
                    trk_pos += tck * self.tempo * 1e-6 / self.res
                    etype = read_byte(f)
                    if etype >= 0x80:
                        mtype = etype & 0xf0
                        mchan = etype & 0x0f
                    else:
                        f.seek(f.tell() - 1)
                    if etype == 0xff:
                        cmd = read_byte(f)
                        esz = midi_varlen(f)
                        if cmd == 0x2F:
                            # End of track
                            break
                        data = f.read(esz)
                        if cmd == 0x58:
                            n, d, c, b = unpack(">BBBB", data)
#                            print("TS", n, d, c, b)
                        elif cmd == 0x51:
                            t = (data[0] << 16) | (data[1] << 8) | (data[2])
#                            print("BPM", (60 * 1000000) / t)
                            self.tempo = t
                        else:
                            # print("Meta 0x%x: %s" % (cmd, data))
                            if cmd == 0x3:
                                track_name = data.decode('utf-8')
                    elif etype == 0xf0:
                        # print("Skipping sysex")
                        while True:
                            if read_byte(f) == 0xf7:
                                break
                    elif mtype == 0x90:
                        pitch, velocity = read_byte(f), read_byte(f)
                        events.append({'type': 'note',
                                       'pitch': pitch,
                                       'velocity': velocity,
                                       'pos': trk_pos})
#                        print("NoteOn chan%d: %d/%d @ %f" % (
#                        mchan, pitch, velocity, trk_pos))
                    elif mtype == 0x80:
                        pitch, velocity = read_byte(f), read_byte(f)
#                        print("NoteOf chan%d %d/%d @ %f" % (
#                            mchan, pitch, velocity, trk_pos))
                    elif mtype in (0xB0, 0xC0, 0xD0, 0xE0):
                        if mtype == 0xB0 or mtype == 0xE0:
                            ctr = read_byte(f)
                            val = read_byte(f)
                            events.append({'type': 'mod',
                                           'ctr': ctr,
                                           'val': val,
                                           'pos': trk_pos})
                        else:
                            read_byte(f)
#                        print("Program/Aftertouch change %X" % mtype)
                    else:
                        print("Unknown event: 0x%X (%X / %X)" % (
                            etype, mtype, mchan))

    def normalize(self):
        self.frames = []
        pos = 1/self.fps
        while True:
            eof = True
            frame = []
            for track in self.tracks:
                trk_events = []
                trk_pos = track['pos']
                if trk_pos < len(track['events']):
                    eof = False
                else:
                    continue
                mod = {}
                chords = {}
                while (trk_pos < len(track['events']) and
                        track['events'][trk_pos]['pos'] < pos):
                    ev = track['events'][trk_pos]
                    del ev['pos']
                    if ev['type'] == 'mod':
                        if ev['ctr'] not in mod:
                            mod[ev['ctr']] = []
                        mod[ev['ctr']].append(ev['val'])
                    elif ev['type'] == 'note':
                        chords.setdefault(ev['pitch'], ev['velocity'])
                    else:
                        trk_events.append(track['events'][trk_pos])
                    trk_pos += 1
                if mod:
                    for ctr, values in mod.items():
                        trk_events.append({'type': 'mod',
                                           'mod': ctr,
                                           'val': np.sum(values)/len(values)})
                if chords:
                    trk_events.append({'type': 'chords', 'pitch': chords})
                track['pos'] = trk_pos
                if trk_events:
                    # Merge ctr
                    frame.append({'track': track['name'], 'ev': trk_events})
            self.frames.append(frame)
            if eof:
                break
            pos += 1/self.fps

    def get(self, frame):
        return self.frames[frame]
