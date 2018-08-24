import pymongo
import os
import luigi
import subprocess
import tempfile
from ftplib import FTP
from zipfile import ZipFile
from pymongo import MongoClient
from luigi.contrib.mongodb import MongoCellTarget
from luigi import LocalTarget
from .directory_target import DirectoryTarget

def new_client():
    url = 'smartengines.com'
    ftp = FTP(url)
    ftp.login()
    ftp.cwd('midv-500/dataset')
    return ftp


class VideoDocInMongo(luigi.ExternalTask):
    video = luigi.Parameter()

    def output(self):
        return MongoCellTarget(MongoClient(), 'quicksign', 'videos', self.video, 'data')


#class VideoToImages(luigi.Task):
#    video = luigi.Parameter()
#
#    def requires(self):
#        return VideoDocInMongo(self.video)
#
#    def output(self):
#        return MongoCellTarget(MongoClient(), 'quicksign', 'images', self.video, 'data')
#
#    def run(self):
#        with tempfile.TemporaryFile() as fd:
#            command = ['ffmpeg', '-i', fd.name, '-f', 'image2', 'video-frame%05d.png']
#            fd.write(self.input().read())
#            subprocess.call(command)
#            self.ouput().write('test')


class SaveVideoInMongo(luigi.Task):
    video = luigi.Parameter()
    archive = luigi.Parameter()

    def requires(self):
        return GetVideoFromArchive(self.video, self.archive)

    def output(self):
        return MongoCellTarget(MongoClient(), 'quicksign', 'videos', self.video, 'data')

    def run(self):
        with self.input().open('rb') as fd:
            data = fd.read()
        self.output().write(data)


class SaveAllVideoInMongo(luigi.WrapperTask):

    def requires(self):
        yield GetAllVideo()
        for input in GetAllVideo().requires():
            archive = input.input().path
            for target in input.output().get_targets():
                video = target.path
                yield SaveVideoInMongo(video, archive)
                #yield VideoToImages(video)


class GetAllVideo(luigi.WrapperTask):

    def requires(self):
        ftp = new_client()
        archives = ftp.nlst()
        for archive in archives:
            yield GetAllVideoFromArchive(archive)
        ftp.close()


class GetVideoFromArchive(luigi.Task):
    file_path = luigi.Parameter()
    archive_name = luigi.Parameter()

    def requires(self):
        return DownloadArchive(self.archive_name)

    def output(self):
        return LocalTarget(self.file_path, format=luigi.format.Nop)

    def run(self):
        filetarget = self.input()
        file_object = filetarget.open('r')
        with ZipFile(file_object, 'r') as zip_fd:
            with zip_fd.open(self.file_path) as fd:
                data = fd.read()
                with self.output().open('wb') as output_fd:
                    output_fd.write(data)
        file_object.close()


class ArchiveTask(luigi.ExternalTask):
    archive_name = luigi.Parameter()

    def requires(self):
        return DownloadArchive(self.archive_name)

    def output(self):
        return LocalTarget(self.archive_name, format=luigi.format.Nop)


class GetAllVideoFromArchive(luigi.Task):
    archive_name = luigi.Parameter()

    def requires(self):
        return DownloadArchive(self.archive_name)

    def output(self):
        return DirectoryTarget(self.archive_name.split('.')[0])

    def run(self):
        with ZipFile(self.input().path, 'r') as fd:
            zip_infos = fd.infolist()
            for zip_info in zip_infos:
                if not zip_info.is_dir() and 'videos' in zip_info.filename:
                    fd.extract(zip_info)


class DownloadAllArchives(luigi.WrapperTask):

    def requires(self):
        ftp = new_client()
        archives = ftp.nlst()
        for archive in archives:
            yield DownloadArchive(archive)
        ftp.close()


class DownloadArchive(luigi.Task):
    archive_name = luigi.Parameter()
    priority = 100

    def output(self):
        return LocalTarget(self.archive_name, format=luigi.format.Nop)

    def callback(self, fd, tot_size):

        def block(x):
            nonlocal self
            fd.write(x)
            fd.seek(0, 2)
            size = os.fstat(fd.fileno()).st_size
            ratio = round(100.0 * size / tot_size, 2)
            self.set_progress_percentage(ratio)
        return block

    def run(self):
        ftp = new_client()
        tot_size = ftp.size(self.archive_name)
        with self.output().open('wb') as fd:
            command = 'RETR ' + self.archive_name
            ftp.retrbinary(command, self.callback(fd, tot_size))
        ftp.close()


class MainTask(luigi.WrapperTask):

    def requires(self):
        ftp = new_client()
        archives = ftp.nlst()
        for archive in archives:
            yield GetAllVideoFromArchive(archive)
        ftp.close()
