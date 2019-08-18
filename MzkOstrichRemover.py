#!/usr/bin/env python3

# Python imports
import os
import sys
import argparse

# Project imports
from src.models.folderInfo import FolderInfo
from src.scan.albumTester import AlbumTester
from src.fill.albumFiller import AlbumFiller
from src.clean.albumCleaner import AlbumCleaner
from src.utils.tools import computePurity
from src.utils.reportBuilder import *
from src.utils.uiBuilder import *

# Globals
global scriptVersion
scriptVersion = '1.1.3'


# Script main frame
def main():
    # Init argparse arguments
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', help='The input folder path to crawl (absolute or relative)')
    ap.add_argument('-s', '--scan', help='Scan a folder to test it against naming convention', action='store_true')
    ap.add_argument('-f', '--fill', help='Prefill tags with folder name and file name information', action='store_true')
    ap.add_argument('-c', '--clean', help='Clean all previously setted tags, and ambiguous ones', action='store_true')
    ap.add_argument('-d', '--dump', help='Dump errors as JSON in ./output folder', action='store_true')
    ap.add_argument('-v', '--verbose', help='Display errors as a tree after crawling', action='store_true')
    arg = ap.parse_args()
    args = vars(ap.parse_args())
    # Preventing path from missing its trailing slash (or backslash for win compatibility)
    if not args['folder'].endswith('\\') and not args['folder'].endswith('/'):
        printInvalidPath(args['folder'])
        sys.exit(-1)
    # Exec script
    printCredentials(scriptVersion)
    # Perform a scan for the given folder against the naming convention
    if args['scan']:
        scanFolder(args)
    # Pre-fill folder's track tags with information held in folder name and file name
    elif args['fill']:
        fillTags(args)
    # Clean all previously setted tags (to prepare a track to be properly filled)
    elif args['clean']:
        cleanTags(args)
    # Otherwise print an error message (missing arguments)
    else:
        printMissingArguments()


# Will crawl the folder path given in argument, and all its sub-directories
def scanFolder(args):
    # Retrieve folder global information
    printRetrieveFolderInfo()
    folderInfo = FolderInfo(args['folder'])
    printRootFolderInfo(folderInfo)
    # Scan internals
    totalTracks = folderInfo.flacCounter + folderInfo.mp3Counter
    rootPathLength = len(args['folder'].split(os.sep))
    scannedTracks = 0
    fileCounter = 0
    errorCounter = 0
    albumTesters = []
    # Scan progression utils
    step = 10
    percentage = step
    previousLetter = '1'  # ordered folder/file parsing begins with numbers
    # Start scan
    printScanStart(args['folder'], totalTracks)
    # Sort directories so they are handled in the alphabetical order
    for root, directories, files in sorted(os.walk(args['folder'])):
        files = [f for f in files if not f[0] == '.'] # Ignore hidden files
        directories[:] = [d for d in directories if not d[0] == '.'] # ignore hidden directories

        # Split root into an array of folders
        path = root.split(os.sep)
        # Mutagen needs a preserved path when using ID3() or FLAC()
        preservedPath = list(path)

        # Poping all path element that are not the root folder, the artist sub folder or the album sub sub folder
        for x in range(rootPathLength - 1):
            path.pop(0)

        # Current path is for an album directory : perform tests
        if len(path) == 2 and path[1] != '':
            albumTester = AlbumTester(files, preservedPath)
            scannedTracks += albumTester.album.totalTrack
            errorCounter += albumTester.errorCounter
            errorCounter += albumTester.tracksErrorCounter()
            albumTesters.append(albumTester)

            # Display a progress every step %
            scannedPercentage = (scannedTracks * 100) / totalTracks
            if totalTracks > 10 and scannedPercentage >= step:
                if (scannedTracks * 100) / totalTracks > percentage and percentage < 100:
                    printScanProgress(percentage, previousLetter, path[0][0], errorCounter, scannedTracks,
                                      computePurity(errorCounter, scannedTracks))
                    percentage += step
                    previousLetter = path[0][0]  # path[0] is the Artists name
    # In this case, ui has display a percentage progression. No need to add a line break if no progression is to be displayed
    if totalTracks > 10:
        printLineBreak()
    printScanEnd(errorCounter, totalTracks, computePurity(errorCounter, scannedTracks));
    # Compute and save JSON report
    if args['dump']:
        saveReportFile(computeReport(scriptVersion, folderInfo, albumTesters, errorCounter,
                                     computePurity(errorCounter, scannedTracks)))
    # Verbose report
    if args['verbose']:
        printErroredTracksReport(albumTesters)


# Will pre-fill the tags for tracks in the given folder
def fillTags(args):
    # Retrieve folder global information
    printRetrieveFolderInfo()
    folderInfo = FolderInfo(args['folder'])
    printRootFolderInfo(folderInfo)
    # Fill internals
    filledTracks = 0
    totalTracks = folderInfo.flacCounter + folderInfo.mp3Counter
    # Start Fill
    printFillStart(args['folder'], totalTracks)
    rootPathLength = len(args['folder'].split(os.sep))
    albumFillers = []
    # Fill progression utils
    step = 10
    percentage = step
    # Sort directories so they are handled in the alphabetical order
    for root, directories, files in sorted(os.walk(args['folder'])):
        files = [f for f in files if not f[0] == '.'] # Ignore hidden files
        directories[:] = [d for d in directories if not d[0] == '.'] # ignore hidden directories

        # Split root into an array of folders
        path = root.split(os.sep)
        # Mutagen needs a preserved path when using ID3() or FLAC()
        preservedPath = list(path)

        # Poping all path element that are not the root folder, the artist sub folder or the album sub sub folder
        for x in range(rootPathLength - 1):
            path.pop(0)

        # Current path is for an album directory : perform tests
        if len(path) == 2 and path[1] != '':
            albumFiller = AlbumFiller(files, preservedPath)
            albumFillers.append(albumFiller)
            filledTracks += albumFiller.album.totalTrack
        # Display a progress every step %
        fillPercentage = (filledTracks * 100) / totalTracks
        if totalTracks > 10 and fillPercentage >= step:
            if (filledTracks * 100) / totalTracks > percentage and percentage < 100:
                printFillProgress(percentage, filledTracks)
                percentage += step
    # In this case, ui has display a percentage progression. No need to add a line break if no progression is to be displayed
    if totalTracks > 10:
        printLineBreak()
    printFillEnd(filledTracks)


def cleanTags(args):
    # Retrieve folder global information
    printRetrieveFolderInfo()
    folderInfo = FolderInfo(args['folder'])
    printRootFolderInfo(folderInfo)
    # Fill internals
    cleanedTracks = 0
    totalTracks = folderInfo.flacCounter + folderInfo.mp3Counter
    # Start Fill
    printCleanStart(args['folder'], totalTracks)
    rootPathLength = len(args['folder'].split(os.sep))
    albumCleaners = []
    # Fill progression utils
    step = 10
    percentage = step
    # Sort directories so they are handled in the alphabetical order
    for root, directories, files in sorted(os.walk(args['folder'])):
        files = [f for f in files if not f[0] == '.'] # Ignore hidden files
        directories[:] = [d for d in directories if not d[0] == '.'] # ignore hidden directories

        # Split root into an array of folders
        path = root.split(os.sep)
        # Mutagen needs a preserved path when using ID3() or FLAC()
        preservedPath = list(path)

        # Poping all path element that are not the root folder, the artist sub folder or the album sub sub folder
        for x in range(rootPathLength - 1):
            path.pop(0)

        # Current path is for an album directory : perform tests
        if len(path) == 2 and path[1] != '':
            albumCleaner = AlbumCleaner(files, preservedPath)
            albumCleaners.append(albumCleaner)
            cleanedTracks += albumCleaner.album.totalTrack
        # Display a progress every step %
        cleanPercentage = (cleanedTracks * 100) / totalTracks
        if totalTracks > 10 and cleanPercentage >= step:
            if (cleanedTracks * 100) / totalTracks > percentage and percentage < 100:
                printCleanProgress(percentage, cleanedTracks)
                percentage += step
    # In this case, ui has display a percentage progression. No need to add a line break if no progression is to be displayed
    if totalTracks > 10:
        printLineBreak()
    printCleanEnd(cleanedTracks)


# Script start point
if __name__ == '__main__':
    main()
