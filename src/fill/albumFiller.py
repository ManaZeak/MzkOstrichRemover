# Project imports
from src.models.album import Album
from src.models.track import Track


class AlbumFiller:
    def __init__(self, files, preservedPath, verbose, logErrors):
        self.preservedPath = preservedPath
        self.files = files
        self.album = Album(files)
        self.verbose = verbose
        self.logErrors = logErrors
        self.hasErrors = False
        self._analyseAlbumInternals()
        self._analyseTracks()


    # Analyse first the global album errors (compute a total disc/track and global album year)
    def _analyseAlbumInternals(self):
        self.album.folderNameList = self.preservedPath[len(self.preservedPath) - 1].split(' - ')
        self.album.albumArtist = self.preservedPath[len(self.preservedPath) - 2]
        lockErrors = False
        # Filling internals
        for fileName in self.album.filesIterable:
            if fileName[-3:] == 'MP3' or fileName[-3:] == 'mp3' or fileName[-4:] == 'FLAC' or fileName[-4:] == 'flac':
                self.album.totalTrack += 1
                forbiddenPattern = ['Single', 'Intro', 'ÉPILOGUE', '25', 'Interlude']
                fileNameList = fileName.split(' - ')
                # Re-join Single properly into list
                if len(fileNameList) == 7 and fileNameList[3] in forbiddenPattern:
                    # When album is a single, we must re-join the album name and the 'Single' suffix
                    fileNameList[2:4] = [' - '.join(fileNameList[2:4])]  # Re-join with a ' - ' separator
                # Fill internals
                if len(fileNameList) == 6:
                    try:
                        if int(fileNameList[len(fileNameList) - 3][:-2]) > int(self.album.totalDisc):
                            self.album.totalDisc = fileNameList[len(fileNameList) - 3][:-2]
                    except:
                        self.hasErrors = True
                        if self.verbose == True or self.logErrors == True:
                            print("ERROR for track : {}\n\tThe file isn't named according to the naming convention.\n".format(fileName))
                    if self.album.year == 0:
                        self.album.year = fileNameList[1]
                    if self.verbose:
                        print('Track {}: {}\n\tRelease artist: {}\n\tAlbum: {}'.format(fileNameList[3], fileNameList[5][:-5], fileNameList[0], fileNameList[2]))
                else:
                    self.hasErrors = True
                    if self.verbose == True or self.logErrors == True:
                        print("ERROR for track : {}\n\tThe file isn't named according to the naming convention.\n".format(fileName))
            if fileName[-3:] == 'JPG' or fileName[-3:] == 'jpg' or fileName[-4:] == 'JPEG' or fileName[-4:] == 'jpeg' or fileName[-3:] == 'PNG' or fileName[-3:] == 'png':
              self.album.hasCover = True
              self.album.coverName = fileName
        # Tracking errors
        for fileName in self.album.filesIterable:
            if fileName[-3:] == 'MP3' or fileName[-3:] == 'mp3' or fileName[-4:] == 'FLAC' or fileName[-4:] == 'flac':
                fileNameList = fileName.split(' - ')
                # ErrorCode 17 : Year is not the same on all physical files of the album
                if self.album.year != fileNameList[1] and lockErrors is False:
                    lockErrors = True
                    self.album.year = 0


    # Analyse the album tracks
    def _analyseTracks(self):
        for fileName in self.files:
            self._fillFile(fileName, self.preservedPath)


    # Manages the MP3/FLAC files to test in the pipeline
    def _fillFile(self, fileName, pathList):
        audioTagPath = ''
        for folder in pathList:  # Build the file path by concatenating folder in the file path
            audioTagPath += '{}/'.format(folder)
        audioTagPath += fileName  # Append the filename at the end of the newly created path
        # Send the file path to the mutagen ID3 to get its tags and create the associated Track object
        if fileName[-3:] == 'mp3' or fileName[-3:] == 'MP3':
            track = Track('MP3', pathList, fileName, audioTagPath)
        elif fileName[-4:] == 'flac' or fileName[-4:] == 'FLAC':
            track = Track('FLAC', pathList, fileName, audioTagPath)
        else:
            return None
        track.setInternalTags(self.album)
