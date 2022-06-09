#  Copyright Control-F 2021
#
#  This software is licensed 'as-is'.  You bear the risk of using it.  In
#  consideration for use of the software, you agree that you have not relied upon
#  any, and we have made no, warranties, whether oral, written, or implied, to
#  you in relation to the software.  To the extent permitted at law, we disclaim
#  any and all warranties, whether express, implied, or statutory, including, but
#  without limitation, implied warranties of non-infringement of third party
#  rights, merchantability and fitness for purpose.
#
#  In no event will we be held liable to you for any loss or damage (including
#  without limitation loss of profits or any indirect or consequential losses)
#  arising from the use of this software.
#
#  Permission is granted to anyone to use this software free of charge for any
#  purpose, including commercial applications, and to alter it and redistribute
#  it freely, subject to the following restrictions:
#
#  1. The origin of this software must not be misrepresented; you must not
#  claim that you wrote the original software. If you use this software
#  in a product, an acknowledgment in the form of
#  "Copyright Control-F 2021" in the product
#  documentation would be appreciated but is not required.
#
#  2. Altered versions of the source code must be plainly marked as such, and
#  must not be misrepresented as being the original software.
#
#  3. This copyright notice and disclaimer may not be removed from or varied in
#  any copy of the software (whether in its original form or any altered version)
#
#  AUTHORS:
#    Mike Bangham (Control-F www.controlf.net)
#
#  REQUIREMENTS:
#    Python 3
#    Tested on iOS 14
#
#  UPDATES:
#    Now parses default application GUIDs and their corresponding APP name
#    Outputs to CSV rather than TXT
#
#  iOS Full File System - requires: root/private/var/
#  Parses property lists (iTunesMetadata.plist and .com.apple.mobile_container_manager.metadata.plist)
#  in order to associate application GUID's with the Application name.
#
#  USAGE: python <scriptname>

__version__ = 0.4
__description__ = "iOS Application GUID Name Resolver"
__contact__ = "mike.bangham@controlf.co.uk"

import tarfile
import zipfile
import sys
import time
import csv
import plistlib
import webbrowser as wb
from io import BytesIO
from os.path import dirname, basename, isfile, abspath
import sys
import argparse


def fetch_meta(plist_dict, fp, guid, installed):
    if installed:
        try:
            appname = plist_dict['itemName']
        except: appname = 'unknown'
        try:
            dev = plist_dict['artistName']
        except: dev = 'unknown'
        try:
            installd = (
                plist_dict['com.apple.iTunesStore.downloadInfo']['purchaseDate'].replace('T', ' ').replace('Z', ''))
        except: installd = 'unknown'
        try:
            pkg = plist_dict['softwareVersionBundleId']
        except: pkg = 'unknown'
        try:
            genre = plist_dict['genre']
        except: genre = 'unknown'
        try:
            defaultapp = plist_dict['isFactoryInstall']
        except: defaultapp = 'unknown'

        return ['No', guid, fp, appname, dev, installd, pkg, genre, defaultapp]

    else:
        try:
            app_name = plist_dict['MCMMetadataIdentifier']
        except:
            app_name = 'unknown'
        return ['Yes', guid, fp, app_name]


class NameParser:
    def __init__(self, *args):
        self.ios_archive, self.apps, self.archive_type, self.output_format = args
        self.date_time = int(time.time())

        if self.apps == 'all':
            self.plists_to_extract = ['iTunesMetadata.plist', '.com.apple.mobile_container_manager.metadata.plist']
        else:
            self.plists_to_extract = ['iTunesMetadata.plist']

    def generate_csv(self, row_data):
        with open('iOS_Apps_{}.csv'.format(self.date_time), 'w', encoding='UTF8', newline='') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(['Default', 'GUID', 'GUID Path', 'App Name', 'Developer',
                             'Installed', 'Bundle ID', 'Genre', 'Default App'])
            for row in row_data:
                writer.writerow(row)
        return 'iOS_Apps_{}.csv'.format(self.date_time)

    def generate_dataframe(self, row_data):
        import pandas as pd
        df = pd.DataFrame(row_data, columns=['Default', 'GUID', 'GUID Path', 'App Name', 'Developer',
                                             'Installed', 'Bundle ID', 'Genre', 'Default App'])
        return df

    def parse(self):
        parsed_count = 0
        row_data = list()

        if self.archive_type == 'zip':
            with zipfile.ZipFile(self.ios_archive, 'r') as zip_obj:
                fps = zip_obj.namelist()
                for fp in fps:
                    if any(_plist in fp for _plist in self.plists_to_extract):
                        guid = basename(dirname(fp))  # each GUI has a plist containing info we need
                        f = zip_obj.read(fp)
                        try:
                            plist_data_dict = plistlib.load(BytesIO(f))  # convert to stream then convert plist > dict
                            if plist_data_dict:
                                if fp.endswith('iTunesMetadata.plist'):
                                    installed = True
                                else:
                                    installed = False
                                row_data.append(fetch_meta(plist_data_dict, fp, guid, installed))
                                parsed_count += 1
                        except Exception as err:
                            print('[!] Error - Could not parse plist for {}\n{}'.format(guid, err))
                            pass

        else:
            with tarfile.open(self.ios_archive, 'r') as file_obj:
                fps = file_obj.getnames()
                for fp in fps:
                    if any(_plist in fp for _plist in self.plists_to_extract):
                        guid = basename(dirname(fp))  # each GUI has a plist containing info we need
                        f = file_obj.extractfile(fp)  # extract file as bytes
                        try:
                            plist_data_dict = plistlib.load(BytesIO(f.read()))  # convert to stream then convert to dict
                            if plist_data_dict:
                                if fp.endswith('iTunesMetadata.plist'):
                                    installed = True
                                else:
                                    installed = False
                                row_data.append(fetch_meta(plist_data_dict, fp, guid, installed))
                                parsed_count += 1
                        except Exception as err:
                            print('[!] Error - Could not parse plist for {}\n{}'.format(guid, err))
                            pass

        if self.output_format == 'csv':
            output = self.generate_csv(row_data)
        else:
            output = self.generate_dataframe(row_data)

        return parsed_count, output


if __name__ == '__main__':
    print("\n\n"
          "                                                        ,%&&,\n"
          "                                                    *&&&&&&&&,\n"
          "                                                  /&&&&&&&&&&&&&\n"
          "                                               #&&&&&&&&&&&&&&&&&&\n"
          "                                           ,%&&&&&&&&&&&&&&&&&&&&&&&\n"
          "                                        ,%&&&&&&&&&&&&&&#  %&&&&&&&&&&,\n"
          "                                     *%&&&&&&&&&&&&&&%       %&&&&&&&&&%,\n"
          "                                   (%&&&&&&&&&&&&&&&&&&&#       %&%&&&&&&&%\n"
          "                               (&&&&&&&&&&&&&&&%&&&&&&&&&(       &&&&&&&&&&%\n"
          "              ,/#%&&&&&&&#(*#&&&&&&&&&&&&&&%,    #&&&&&&&&&(       &&&&&&&\n"
          "          (&&&&&&&&&&&&&&&&&&&&&&&&&&&&&#          %&&&&&&&&&(       %/\n"
          "       (&&&&&&&&&&&&&&&&&&&&&&&&&&&&&(               %&&&&&&&&&/\n"
          "     /&&&&&&&&&&&&&&&&&&%&&&&&&&%&/                    %&&&&&,\n"
          "    #&&&&&&&&&&#          (&&&%*                         #,\n"
          "   #&&&&&&&&&%\n"
          "   &&&&&&&&&&\n"
          "  ,&&&&&&&&&&\n"
          "   %&&&&&&&&&                           {}\n"
          "   (&&&&&&&&&&,             /*          Version: {}\n"
          "    (&&&&&&&&&&&/        *%&&&&&#\n"
          "      &&&&&&&&&&&&&&&&&&&&&&&&&&&&&%\n"
          "        &&&&&&&&&&&&&&&&&&&&&&&&&%\n"
          "          *%&&&&&&&&&&&&&&&&&&#,\n"
          "                *(######/,".format(__description__, __version__))
    print('\n\n')

    print("Append the '--help' command to see usage in detail")

    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('-i', required=True, help='The iOS input archive (Full File System)')
    parser.add_argument('-a', required=True, help="Accepts: 'all' (all apps) or '3rd' (third party apps only)")
    parser.add_argument('-o', required=True, help="Output format: accepts 'df' or 'csv'")
    args = parser.parse_args()

    if len(args.i) and isfile(abspath(args.i)):
        archive = args.i
        if zipfile.is_zipfile(archive):
            archive_type = 'zip'
        elif tarfile.is_tarfile(archive):
            archive_type = 'tar'
        else:
            print('\n[!] Unrecognised file format - must be a zip or tar archive')
            sys.exit()
    else:
        print('[!!] Error: Please provide an archive for argument -i')
        sys.exit()

    if len(args.a) and args.a in ['all', '3rd']:
        apps = args.a
    else:
        print("[!!] Error: argument -a only accepts 'all' or '3rd'")
        sys.exit()

    if len(args.o) and args.o in ['df', 'csv']:
        output_format = args.o
    else:
        print("[!!] Error: argument -o only accepts 'df' or 'csv'")
        sys.exit()

    np = NameParser(archive, apps, archive_type, output_format)
    parsed_count, content = np.parse()
    print('\nFinished! Parsed {} application names'.format(parsed_count))
    print('Out:\n{}'.format(content))
    print('\n\n')

