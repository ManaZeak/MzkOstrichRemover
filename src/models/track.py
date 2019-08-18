# Project imports
from mutagen.id3 import ID3
from mutagen.flac import FLAC, Picture

import base64
import mimetypes
import PIL

# from utils.uiBuilder import printDetailledTrack # Uncomment for debug purpose only (printDetailledTrack() is very verbose)
mimetypes.init()
mode_to_bpp = {'1':1, 'L':8, 'P':8, 'RGB':24, 'RGBA':32, 'CMYK':32, 'YCbCr':24, 'I':32, 'F':32}

# A Track container class with all useful attributes
class Track(object):
    def __init__(self, fileType, pathList, fileName, audioTagPath):
        # ID3 tags
        self.title = ''
        self.artists = []
        self.albumTitle = ''
        self.albumArtist = ''
        self.year = ''
        self.performers = []
        self.composedPerformer = []
        self.composers = ''
        self.producer = ''
        self.label = ''
        self.trackNumber = 0
        self.totalTrack = 0
        self.discNumber = 0
        self.totalDisc = 0
        self.bpm = ''
        self.lang = ''
        # Computed
        self.audioTagPath = audioTagPath
        self.audioTag = {}
        self.feat = []
        self.remix = []
        self.hasCover = False
        self.cover = {}
        self.coverType = ''
        # Filesystem path and name as lists (separator is ` - `)
        self.pathList = pathList
        self.fileType = fileType
        self.fileName = fileName  # Filename as a string
        # %releaseArtists% - %year% - %albumTitle% - %discNumber%%trackNumber% - %artists% - %title%
        self.fileNameList = []
        self.folderNameList = []  # %year% - %albumTitle%
        # Self fill
        if fileType == 'MP3':
            self.audioTag = ID3(audioTagPath)
            self._fillFromMP3()
        elif fileType == 'FLAC':
            self.audioTag = FLAC(audioTagPath)
            self._fillFromFLAC()
        self._computeInternals()

    # Read the mp3 track ID3 tags and extract all interresting values into a Track object
    def _fillFromMP3(self):
        if 'TIT2' in self.audioTag and self.audioTag['TIT2'].text[0] != '':
            self.title = self.audioTag['TIT2'].text[0].rstrip()
        if 'TPE1' in self.audioTag:
            self.artists = self.audioTag['TPE1'].text[0].split('; ')
        if 'TPE2' in self.audioTag:
            self.albumArtist = self.audioTag['TPE2'].text[0].rstrip()
        if 'TALB' in self.audioTag:
            self.albumTitle = self.audioTag['TALB'].text[0].rstrip()
        if 'TDRC' in self.audioTag and self.audioTag['TDRC'].text[0].get_text() != '':
            self.year = self.audioTag['TDRC'].text[0].get_text()[:4].rstrip()
        if 'TPUB' in self.audioTag and self.audioTag['TPUB'].text[0] != '':
            self.producer = self.audioTag['TPUB'].text[0].rstrip()
        if 'TCOP' in self.audioTag and self.audioTag['TCOP'].text[0] != '':
            self.label = self.audioTag['TCOP'].text[0].rstrip()
        if 'TCOM' in self.audioTag and self.audioTag['TCOM'].text[0] != '':
            self.composers = self.audioTag['TCOM'].text[0]
        if 'TOPE' in self.audioTag and self.audioTag['TOPE'].text[0] != '':
            self.performers = self.audioTag['TOPE'].text[0].rstrip().split('; ')
        if 'TLAN' in self.audioTag:
            self.lang = self.audioTag['TLAN'].text[0].rstrip().split('; ')
        if 'TRCK' in self.audioTag and self.audioTag['TRCK'].text[0] != '':
            if '/' in self.audioTag['TRCK'].text[0]:
                tags = self.audioTag['TRCK'].text[0].rstrip().split('/')
                self.trackNumber = tags[0]
                self.totalTrack = tags[1]
            else:
                self.trackNumber = self.audioTag['TRCK'].text[0].rstrip()
        if 'TPOS' in self.audioTag and self.audioTag['TPOS'].text[0] != '':
            tags = self.audioTag['TPOS'].text[0].rstrip().split('/')
            self.discNumber = tags[0]
            if len(tags) > 1:
                self.totalDisc = tags[1]
            else:
                self.totalDisc = -1
        if 'TBPM' in self.audioTag and self.audioTag['TBPM'].text[0] != '':
            self.bpm = self.audioTag['TBPM'].text[0].rstrip()

    # Read the flac track Vorbis tags and extract all interresting values into a Track object
    def _fillFromFLAC(self):
        if 'TITLE' in self.audioTag:
            self.title = self.audioTag['TITLE'][0]
        if 'DATE' in self.audioTag:
            self.year = self.audioTag['DATE'][0]
        if 'TRACKNUMBER' in self.audioTag:
            self.trackNumber = self.audioTag['TRACKNUMBER'][0]
        if 'PRODUCER' in self.audioTag:
            self.producer = self.audioTag['PRODUCER'][0]
        if 'LABEL' in self.audioTag:
            self.label = self.audioTag['LABEL'][0]
        if 'DISCNUMBER' in self.audioTag:
            self.discNumber = self.audioTag['DISCNUMBER'][0]
        if 'DISCTOTAL' in self.audioTag:
            self.totalDisc = self.audioTag['DISCTOTAL'][0]
        if 'TRACKTOTAL' in self.audioTag:
            self.totalTrack = self.audioTag['TRACKTOTAL'][0]
        if 'COMPOSER' in self.audioTag:
            self.composers = self.audioTag['COMPOSER'][0]
        if 'PERFORMER' in self.audioTag:
            self.performers = self.audioTag['PERFORMER'][0].split('; ')
        if 'ARTIST' in self.audioTag:
            self.artists = self.audioTag['ARTIST'][0].split('; ')
        if 'ALBUM' in self.audioTag:
            self.albumTitle = self.audioTag['ALBUM'][0]
        if 'ALBUMARTIST' in self.audioTag:
            self.albumArtist = self.audioTag['ALBUMARTIST'][0]
        if 'BPM' in self.audioTag:
            self.bpm = self.audioTag['BPM'][0]
        if 'LANGUAGE' in self.audioTag:
            self.lang = self.audioTag['LANGUAGE'][0].split('; ')

    # Compute all class internals that can not be extracted from ID3 tags
    def _computeInternals(self):
        self._computeFileNameList()
        self._computeFolderNameList()
        self._computeFeaturing()
        self._computeRemixer()
        self._containsCover()

    # Splits the filename into its components
    # (%releaseArtists% - %year% - %albumTitle% - %discNumber%%trackNumber% - %artists% - %title%)
    def _computeFileNameList(self):
        # We split the filename into its differents parts, as mentioned in this method description
        self.fileNameList = self.fileName.split(' - ')
        forbiddenPattern = ['Single', 'Intro', 'ÉPILOGUE', '25', 'Interlude']
        # Here we handle all specific cases (when ' - ' is not a separator)
        if len(self.fileNameList) > 6 and self.fileNameList[3] in forbiddenPattern:
            # When album is a single, we must re-join the album name and the 'Single' suffix
            self.fileNameList[2:4] = [' - '.join(self.fileNameList[2:4])]  # Re-join with a ' - ' separator

    # Splits the folderame into its components (%year% - %albumTitle%)
    def _computeFolderNameList(self):
        # We also split the folder name to make a double check for Year and Album name
        self.folderNameList = self.pathList[len(self.pathList) - 1].split(' - ')
        forbiddenPattern = ['Single', 'Intro', 'ÉPILOGUE', '25', 'Interlude']

        if len(self.folderNameList) == 3 and self.folderNameList[2] in forbiddenPattern:
            # When album is a single, we must re-join the album name and the 'Single' suffix
            self.folderNameList[1:3] = [' - '.join(self.folderNameList[1:3])]  # Re-join with a ' - ' separator

    # Extract the featured artist(s) name(s) from the track fileName
    def _computeFeaturing(self):
        if self.fileName.find('(feat.') != -1:
            startIndex = self.fileName.rfind('(feat.', 0, len(self.fileName))
            # TODO handle matching brace -> in cas (feat. Zob(Thom))
            self.feat = self.fileName[startIndex + 7: self.fileName.find(')', startIndex)].split(', ')
            # +7 is to remove the `(feat. ` string from feat artist
            if len(self.feat) > 0 and self.feat[0] != '':
                self.composedPerformer = [*self.feat, *self.artists]
                return
        self.composedPerformer = self.artists  # No featuring so performer should be equal to artist

    # Extract the track remix artist name from the track fileName
    def _computeRemixer(self):
        if self.fileName.find(' Remix)') != -1:
            self.remix = self.fileName[
                         # +1 is to remove the opening parenthesis
                         self.fileName.rfind('(', 0, len(self.fileName)) + 1:self.fileName.rfind(' Remix)')
                         ].split(', ')

    # Test the cover existence in the file
    def _containsCover(self):
        # Extract image from file
        if self.fileType == 'MP3' and 'APIC:' in self.audioTag:
            self.cover = self.audioTag['APIC:'].data
            self.coverType = self.audioTag['APIC:'].mime
        elif self.fileType == 'FLAC':
            if len(self.audioTag.pictures) > 0:
                self.cover = self.audioTag.pictures[0].data
                self.coverType = self.audioTag.pictures[0].mime
            else:
                self.cover = self.audioTag.pictures
        # Test cover existence
        if len(self.cover) != 0:
            self.hasCover = True
        else:
            self.hasCover = False


    def clearInternalTags(self, album):
        self.audioTag['TITLE'] = '';
        self.audioTag['DATE'] = '';
        self.audioTag['ALBUM'] = '';
        self.audioTag['ARTIST'] = '';
        self.audioTag['ALBUMARTIST'] = '';
        self.audioTag['PERFORMER'] = '';
        self.audioTag['TRACKNUMBER'] = '';
        self.audioTag['DISCNUMBER'] = '';
        self.audioTag['TRACKTOTAL'] = '';
        self.audioTag['TOTALTRACK'] = '';
        self.audioTag['TOTALTRACKS'] = '';
        self.audioTag['DISCTOTAL'] = '';
        self.audioTag['TOTALDISC'] = '';
        self.audioTag['TOTALDISCS'] = '';
        self.audioTag.clear_pictures()
        self.audioTag.save(self.audioTagPath)



    # Compute all class internals that can not be extracted from ID3 tags
    def setInternalTags(self, album):
        self._buildArtistsList()
        self._buildPerformersList()
        self._addCoverToFile(album)
        if self.fileType == 'FLAC':
            if len(self.fileNameList) == 6 and self.fileNameList[5] is not None:
                self._setInternalTag('TITLE', self.fileNameList[5][:-5])
            if album.year is not None:
                self._setInternalTag('DATE', str(album.year))
            if self.artists is not None:
                self._setInternalTag('ARTIST', '; '.join(self.artists))
            if album.albumArtist is not None:
                self._setInternalTag('ALBUMARTIST', album.albumArtist)
            if self.performers is not None:
                self._setInternalTag('PERFORMER', '; '.join(self.performers))
            if len(self.fileNameList) == 6 and self.fileNameList[3] is not None:
                self._setInternalTag('TRACKNUMBER', str(self.fileNameList[3][2:]))
            if album.totalTrack is not None:
                self._setInternalTag('TRACKTOTAL', str(album.totalTrack))
            if len(self.folderNameList) == 2 and self.folderNameList[1] is not None:
                self._setInternalTag('ALBUM', self.folderNameList[1])
            if album.totalDisc is not None:
                self._setInternalTag('DISCTOTAL', str(album.totalDisc))
            if len(self.fileNameList) == 6 and self.fileNameList[3] is not None:
                self._setInternalTag('DISCNUMBER', str(self.fileNameList[3][:1]))
            self.audioTag.save(self.audioTagPath)
        elif self.fileType == 'MP3':
            # TODO
            print(album.albumArtist)


    # Check if the tag is already filled before adding one
    def _setInternalTag(self, tag, value):
        if tag in self.audioTag and self.audioTag[tag] is not value:
            self.audioTag[tag] = value
        else:
            self.audioTag[tag] = ''


    def _buildArtistsList(self):
        outputList = []

        if len(self.remix) == 0:
            artists = self.fileNameList[4].split(', ')
            for artist in artists:
                outputList.append(artist)
        else:
            outputList = list(set(outputList + self.remix))
        outputList.sort()
        self.artists = outputList


    def _buildPerformersList(self):
        outputList = []
        if len(self.remix) == 0:
            performers = self.fileNameList[4].split(', ')
            for performer in performers:
                outputList.append(performer)
        else:
            outputList = list(set(outputList + self.remix))
        if len(self.feat) > 0:
            outputList = list(set(outputList + self.feat))
        outputList.sort()
        self.performers = outputList


    def _addCoverToFile(self, album):
        if self.hasCover == False or (self.audioTag.pictures[0].height != 1000 and self.audioTag.pictures[0].width != 1000):
            if self.hasCover == True:
                self.audioTag.clear_pictures()

            path = ''
            for folder in self.pathList:  # Build the file path by concatenating folder in the file path
                path += '{}/'.format(folder)
            path += album.coverName
            with open(path, "rb") as img:
                data = img.read()

            im = PIL.Image.open(path)
            width, height = im.size

            picture = Picture()
            picture.data = data
            picture.type = 3 # COVER_FRONT
            picture.desc = path.rsplit('/', 1)[-1] # Add picture name as a description
            picture.mime = mimetypes.guess_type(path)[0]
            picture.width = width
            picture.height = height
            picture.depth = mode_to_bpp[im.mode]

            self.audioTag.add_picture(picture);
            self.audioTag.save()