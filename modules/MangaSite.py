import abc


class MangaSite(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def check_manga_length(self):
        pass

    @abc.abstractmethod
    def generate_chapters_array(self, start, end):
        pass

    @abc.abstractmethod
    def scrape_each_chapter(self, chapter, manga_library, Error_dict, his_length, idx):
        pass
